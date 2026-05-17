#!/usr/bin/env python3
"""
maps_client.py - CLI tool for maps, geocoding, routing, POI search, and more.
Uses only Python stdlib. Data from OpenStreetMap/Nominatim, Overpass API, OSRM,
and TimeAPI.io.

Commands:
  search          - Geocode a place name to coordinates
  reverse         - Reverse geocode coordinates to an address
  nearby          - Find nearby POIs by category
  distance        - Road distance and travel time between two places
  directions      - Turn-by-turn directions between two places
  timezone        - Timezone info for coordinates
  bbox            - Find POIs within a bounding box
  area            - Get bounding box and area info for a named place
  supplier-geo    - 1688供应商地理位置分析（批量解析+geocode）
  logistics-cost  - 物流成本估算（距离+重量+运输模式）
  supplier-clusters - 供应商聚类分析+GeoJSON可视化
  delivery-heatmap  - 交货距离热力图+SVG渲染
"""

import argparse
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

USER_AGENT = "HermesAgent/1.0 (contact: hermes@agent.ai)"
DATA_SOURCE = "OpenStreetMap/Nominatim"

NOMINATIM_SEARCH  = "https://nominatim.openstreetmap.org/search"
NOMINATIM_REVERSE = "https://nominatim.openstreetmap.org/reverse"
# Public Overpass endpoints. We try them in order so a single server
# outage doesn't break the skill — kumi.systems is a well-known mirror.
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
# Backward-compat alias for any caller that imports OVERPASS_API directly.
OVERPASS_API      = OVERPASS_URLS[0]
OSRM_BASE         = "https://router.project-osrm.org/route/v1"
TIMEAPI_BASE      = "https://timeapi.io/api/timezone/coordinate"

# Seconds to sleep between Nominatim requests (ToS requirement)
NOMINATIM_RATE_LIMIT = 1.0

# Maximum retries for HTTP errors
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds

# Category -> (OSM tag key, OSM tag value)
CATEGORY_TAGS = {
    # Food & Drink
    "restaurant":        ("amenity", "restaurant"),
    "cafe":              ("amenity", "cafe"),
    "bar":               ("amenity", "bar"),
    # bakery is tagged as shop=bakery in the OSM wiki, but some mappers use
    # amenity=bakery. Search both so small indie bakeries aren't missed.
    "bakery":            [("shop", "bakery"), ("amenity", "bakery")],
    "convenience_store": ("shop",    "convenience"),
    # Health
    "hospital":          ("amenity", "hospital"),
    "pharmacy":          ("amenity", "pharmacy"),
    "dentist":           ("amenity", "dentist"),
    "doctor":            ("amenity", "doctors"),
    "veterinary":        ("amenity", "veterinary"),
    # Accommodation
    "hotel":             ("tourism", "hotel"),
    "guest_house":       ("tourism", "guest_house"),
    "camp_site":         ("tourism", "camp_site"),
    # Shopping & Services
    "supermarket":       ("shop",    "supermarket"),
    "bookshop":          ("shop",    "books"),
    "laundry":           ("shop",    "laundry"),
    # Finance
    "atm":               ("amenity", "atm"),
    "bank":              ("amenity", "bank"),
    # Transport
    "gas_station":       ("amenity", "fuel"),
    "parking":           ("amenity", "parking"),
    "airport":           ("aeroway", "aerodrome"),
    "train_station":     ("railway", "station"),
    "bus_stop":          ("highway", "bus_stop"),
    "taxi":              ("amenity", "taxi"),
    "car_wash":          ("amenity", "car_wash"),
    "car_rental":        ("amenity", "car_rental"),
    "bicycle_rental":    ("amenity", "bicycle_rental"),
    # Culture & Entertainment
    "museum":            ("tourism", "museum"),
    "cinema":            ("amenity", "cinema"),
    "theatre":           ("amenity", "theatre"),
    "nightclub":         ("amenity", "nightclub"),
    "zoo":               ("tourism", "zoo"),
    # Education
    "school":            ("amenity", "school"),
    "university":        ("amenity", "university"),
    "library":           ("amenity", "library"),
    # Public Services
    "police":            ("amenity", "police"),
    "fire_station":      ("amenity", "fire_station"),
    "post_office":       ("amenity", "post_office"),
    # Religion
    "church":            ("amenity", "place_of_worship"),  # refined by religion tag
    "mosque":            ("amenity", "place_of_worship"),
    "synagogue":         ("amenity", "place_of_worship"),
    # Recreation
    "park":              ("leisure", "park"),
    "gym":               ("leisure", "fitness_centre"),
    "swimming_pool":     ("leisure", "swimming_pool"),
    "playground":        ("leisure", "playground"),
    "stadium":           ("leisure", "stadium"),
}

# Religion-specific overrides for place_of_worship categories
RELIGION_FILTER = {
    "church":    "christian",
    "mosque":    "muslim",
    "synagogue": "jewish",
}

VALID_CATEGORIES = sorted(CATEGORY_TAGS.keys())


def _tags_for(category):
    """Return the CATEGORY_TAGS entry as a list of (key, value) pairs.

    Most categories map to a single (tag_key, tag_val) tuple, but some
    (e.g. ``bakery``) are tagged under more than one OSM key and are
    represented as a list of tuples. Normalise both forms to a list.
    """
    entry = CATEGORY_TAGS[category]
    if isinstance(entry, list):
        return list(entry)
    return [entry]

OSRM_PROFILES = {
    "driving": "driving",
    "walking": "foot",
    "cycling": "bike",
}

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def print_json(data):
    """Print data as pretty-printed JSON to stdout."""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def error_exit(message, code=1):
    """Print an error result as JSON and exit."""
    print_json({"error": message, "status": "error"})
    sys.exit(code)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def http_get(url, params=None, retries=MAX_RETRIES, silent=False):
    """
    Perform an HTTP GET request, returning parsed JSON.
    Adds the required User-Agent header. Retries on transient errors.
    If silent=True, raises RuntimeError instead of calling error_exit.
    """
    if params:
        url = url + "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP {exc.code}: {exc.reason} for {url}"
            if exc.code in (429, 503, 502, 504):
                time.sleep(RETRY_DELAY * attempt)
            else:
                if silent:
                    raise RuntimeError(last_error)
                error_exit(last_error)
        except urllib.error.URLError as exc:
            last_error = f"URL error: {exc.reason}"
            time.sleep(RETRY_DELAY * attempt)
        except json.JSONDecodeError as exc:
            last_error = f"JSON parse error: {exc}"
            time.sleep(RETRY_DELAY * attempt)

    msg = f"Request failed after {retries} attempts. Last error: {last_error}"
    if silent:
        raise RuntimeError(msg)
    error_exit(msg)


def http_get_text(url, params=None, retries=MAX_RETRIES, silent=False):
    """
    Like http_get but returns raw text instead of parsed JSON.
    Useful for APIs that may return non-JSON responses.
    """
    if params:
        url = url + "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP {exc.code}: {exc.reason} for {url}"
            if exc.code in (429, 503, 502, 504):
                time.sleep(RETRY_DELAY * attempt)
            else:
                if silent:
                    raise RuntimeError(last_error)
                error_exit(last_error)
        except urllib.error.URLError as exc:
            last_error = f"URL error: {exc.reason}"
            time.sleep(RETRY_DELAY * attempt)

    msg = f"Request failed after {retries} attempts. Last error: {last_error}"
    if silent:
        raise RuntimeError(msg)
    error_exit(msg)


def http_post(url, data_str, retries=MAX_RETRIES):
    """
    Perform an HTTP POST with a plain-text body (for Overpass QL).
    Returns parsed JSON.
    """
    encoded = data_str.encode("utf-8")
    req = urllib.request.Request(
        url,
        data=encoded,
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP {exc.code}: {exc.reason}"
            if exc.code in (429, 503, 502, 504):
                time.sleep(RETRY_DELAY * attempt)
            else:
                error_exit(last_error)
        except urllib.error.URLError as exc:
            last_error = f"URL error: {exc.reason}"
            time.sleep(RETRY_DELAY * attempt)
        except json.JSONDecodeError as exc:
            last_error = f"JSON parse error: {exc}"
            time.sleep(RETRY_DELAY * attempt)

    error_exit(f"POST failed after {retries} attempts. Last error: {last_error}")


def overpass_query(query):
    """POST an Overpass QL query, trying each URL in OVERPASS_URLS in turn.

    A single public Overpass mirror can be rate-limited or down; trying the
    next mirror before giving up turns a flaky outage into a retry. Returns
    parsed JSON. Falls through to error_exit if every mirror fails.
    """
    post_data = "data=" + urllib.parse.quote(query)
    last_error = None
    for url in OVERPASS_URLS:
        try:
            return http_post(url, post_data, retries=1)
        except SystemExit:
            # error_exit inside http_post — keep trying the next mirror.
            last_error = f"mirror {url} exhausted retries"
            continue
        except Exception as exc:
            last_error = f"{url}: {exc}"
            continue
    error_exit(
        f"All Overpass mirrors failed. Last error: {last_error or 'unknown'}"
    )


# ---------------------------------------------------------------------------
# Geo math
# ---------------------------------------------------------------------------

def haversine_m(lat1, lon1, lat2, lon2):
    """Return distance in metres between two lat/lon points (Haversine)."""
    R = 6_371_000  # Earth mean radius in metres
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Nominatim helpers
# ---------------------------------------------------------------------------

def nominatim_search(query, limit=5):
    """Geocode a free-text query. Returns list of result dicts."""
    params = {
        "q":              query,
        "format":         "json",
        "limit":          limit,
        "addressdetails": 1,
    }
    time.sleep(NOMINATIM_RATE_LIMIT)
    return http_get(NOMINATIM_SEARCH, params=params)


def nominatim_reverse(lat, lon):
    """Reverse geocode lat/lon. Returns a single result dict."""
    params = {
        "lat":            lat,
        "lon":            lon,
        "format":         "json",
        "addressdetails": 1,
    }
    time.sleep(NOMINATIM_RATE_LIMIT)
    return http_get(NOMINATIM_REVERSE, params=params)


def geocode_single(query):
    """
    Geocode a query and return (lat, lon, display_name).
    Exits with error if nothing found.
    """
    results = nominatim_search(query, limit=1)
    if not results:
        error_exit(f"Could not geocode: {query}")
    r = results[0]
    return float(r["lat"]), float(r["lon"]), r.get("display_name", query)


# ---------------------------------------------------------------------------
# Overpass helpers
# ---------------------------------------------------------------------------

def build_overpass_nearby(tag_key, tag_val, lat, lon, radius, limit,
                          religion=None, tag_pairs=None):
    """Build an Overpass QL query for nearby POIs around a point.

    If ``tag_pairs`` is provided, the query unions across every
    ``(key, value)`` pair (used for categories like ``bakery`` that are
    tagged under more than one OSM key). Otherwise falls back to the
    single ``tag_key``/``tag_val`` pair for back-compat.
    """
    pairs = tag_pairs if tag_pairs else [(tag_key, tag_val)]
    religion_filter = ""
    if religion:
        religion_filter = f'["religion"="{religion}"]'
    body_lines = []
    for k, v in pairs:
        body_lines.append(
            f'  node["{k}"="{v}"]{religion_filter}'
            f'(around:{radius},{lat},{lon});'
        )
        body_lines.append(
            f'  way["{k}"="{v}"]{religion_filter}'
            f'(around:{radius},{lat},{lon});'
        )
    body = "\n".join(body_lines)
    return (
        f'[out:json][timeout:25];\n'
        f'(\n'
        f'{body}\n'
        f');\n'
        f'out center {limit};\n'
    )


def build_overpass_bbox(tag_key, tag_val, south, west, north, east, limit,
                        religion=None, tag_pairs=None):
    """Build an Overpass QL query for POIs within a bounding box.

    See ``build_overpass_nearby`` for ``tag_pairs`` semantics.
    """
    pairs = tag_pairs if tag_pairs else [(tag_key, tag_val)]
    religion_filter = ""
    if religion:
        religion_filter = f'["religion"="{religion}"]'
    body_lines = []
    for k, v in pairs:
        body_lines.append(
            f'  node["{k}"="{v}"]{religion_filter}'
            f'({south},{west},{north},{east});'
        )
        body_lines.append(
            f'  way["{k}"="{v}"]{religion_filter}'
            f'({south},{west},{north},{east});'
        )
    body = "\n".join(body_lines)
    return (
        f'[out:json][timeout:25];\n'
        f'(\n'
        f'{body}\n'
        f');\n'
        f'out center {limit};\n'
    )


def parse_overpass_elements(elements, ref_lat=None, ref_lon=None):
    """
    Parse Overpass elements into a clean list of POI dicts.
    If ref_lat/ref_lon are provided, computes distance and sorts by it.
    """
    places = []
    for el in elements:
        # Ways have a "center" sub-dict; nodes have lat/lon directly
        if el["type"] == "way":
            center = el.get("center", {})
            el_lat = center.get("lat")
            el_lon = center.get("lon")
        else:
            el_lat = el.get("lat")
            el_lon = el.get("lon")

        if el_lat is None or el_lon is None:
            continue

        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:en") or ""

        # Build a short address from available tags
        addr_parts = []
        for part_key in ("addr:housenumber", "addr:street", "addr:city"):
            val = tags.get(part_key)
            if val:
                addr_parts.append(val)
        address_str = ", ".join(addr_parts) if addr_parts else ""

        place = {
            "name":     name,
            "address":  address_str,
            "lat":      el_lat,
            "lon":      el_lon,
            "osm_type": el.get("type", ""),
            "osm_id":   el.get("id", ""),
            # Clickable Google Maps link so the agent can render a tap-to-open
            # URL in chat without composing one downstream.
            "maps_url": f"https://www.google.com/maps/search/?api=1&query={el_lat},{el_lon}",
            "tags": {
                k: v for k, v in tags.items()
                if k not in ("name", "name:en",
                             "addr:housenumber", "addr:street", "addr:city")
            },
        }

        # Promote commonly-useful tags to top-level fields so agents can
        # reference them without digging into the raw ``tags`` dict.
        for src_key, dst_key in (
            ("cuisine",        "cuisine"),
            ("opening_hours",  "hours"),
            ("phone",          "phone"),
            ("website",        "website"),
        ):
            val = tags.get(src_key)
            if val:
                place[dst_key] = val

        if ref_lat is not None and ref_lon is not None:
            dist_m = haversine_m(ref_lat, ref_lon, el_lat, el_lon)
            place["distance_m"] = round(dist_m, 1)
            # With a reference point we can also hand back a directions URL.
            place["directions_url"] = (
                f"https://www.google.com/maps/dir/?api=1"
                f"&origin={ref_lat},{ref_lon}"
                f"&destination={el_lat},{el_lon}"
            )

        places.append(place)

    # Sort by distance if available
    if places and "distance_m" in places[0]:
        places.sort(key=lambda p: p["distance_m"])

    return places


# ---------------------------------------------------------------------------
# Command: search
# ---------------------------------------------------------------------------

def cmd_search(args):
    """Geocode a place name and return top results."""
    query = " ".join(args.query)
    raw   = nominatim_search(query, limit=5)

    if not raw:
        print_json({
            "query":       query,
            "results":     [],
            "count":       0,
            "data_source": DATA_SOURCE,
        })
        return

    results = []
    for item in raw:
        bb = item.get("boundingbox", [])
        results.append({
            "name":         item.get("name") or item.get("display_name", ""),
            "display_name": item.get("display_name", ""),
            "lat":          float(item["lat"]),
            "lon":          float(item["lon"]),
            "type":         item.get("type", ""),
            "category":     item.get("category", ""),
            "osm_type":     item.get("osm_type", ""),
            "osm_id":       item.get("osm_id", ""),
            "bounding_box": {
                "min_lat": float(bb[0]) if len(bb) > 0 else None,
                "max_lat": float(bb[1]) if len(bb) > 1 else None,
                "min_lon": float(bb[2]) if len(bb) > 2 else None,
                "max_lon": float(bb[3]) if len(bb) > 3 else None,
            },
            "importance":   item.get("importance"),
        })

    print_json({
        "query":       query,
        "results":     results,
        "count":       len(results),
        "data_source": DATA_SOURCE,
    })


# ---------------------------------------------------------------------------
# Command: reverse
# ---------------------------------------------------------------------------

def cmd_reverse(args):
    """Reverse geocode coordinates to a human-readable address."""
    try:
        lat = float(args.lat)
        lon = float(args.lon)
    except ValueError:
        error_exit("LAT and LON must be numeric values.")

    if not (-90 <= lat <= 90):
        error_exit("Latitude must be between -90 and 90.")
    if not (-180 <= lon <= 180):
        error_exit("Longitude must be between -180 and 180.")

    data = nominatim_reverse(lat, lon)

    if "error" in data:
        error_exit(f"Reverse geocode failed: {data['error']}")

    address = data.get("address", {})

    print_json({
        "lat":          lat,
        "lon":          lon,
        "display_name": data.get("display_name", ""),
        "address": {
            "house_number":  address.get("house_number", ""),
            "road":          address.get("road", ""),
            "neighbourhood": address.get("neighbourhood", ""),
            "suburb":        address.get("suburb", ""),
            "city":          (address.get("city")
                              or address.get("town")
                              or address.get("village", "")),
            "county":        address.get("county", ""),
            "state":         address.get("state", ""),
            "postcode":      address.get("postcode", ""),
            "country":       address.get("country", ""),
            "country_code":  address.get("country_code", ""),
        },
        "osm_type":    data.get("osm_type", ""),
        "osm_id":      data.get("osm_id", ""),
        "data_source": DATA_SOURCE,
    })


# ---------------------------------------------------------------------------
# Command: nearby
# ---------------------------------------------------------------------------

def cmd_nearby(args):
    """Find nearby POIs using the Overpass API.

    Accepts either explicit coordinates (``lat``/``lon``) or a free-form
    address via ``--near`` (auto-geocoded through Nominatim). Supports
    multiple categories in one call — results are merged, deduplicated
    by ``osm_type+osm_id``, sorted by distance.
    """
    # Resolve the center point. --near takes precedence if provided so the
    # agent can ask "cafes near Times Square" in one command without having
    # to geocode first.
    if getattr(args, "near", None):
        near_query = " ".join(args.near).strip() if isinstance(args.near, list) else str(args.near).strip()
        if not near_query:
            error_exit("--near must be a non-empty address or place name.")
        lat, lon, _ = geocode_single(near_query)
    else:
        try:
            lat = float(args.lat)
            lon = float(args.lon)
        except (TypeError, ValueError):
            error_exit("Provide numeric LAT and LON, or use --near \"<address>\".")

    # Categories: support both legacy single positional ``category`` and the
    # new repeatable ``--category`` flag. Users can ask for multiple place
    # types in one query.
    categories = []
    if getattr(args, "category_list", None):
        categories.extend(args.category_list)
    if getattr(args, "category", None):
        categories.append(args.category)
    # Deduplicate, preserve order, lower-case.
    categories = list(dict.fromkeys(c.lower() for c in categories if c))
    if not categories:
        error_exit("Provide at least one category (positional or --category).")
    unknown = [c for c in categories if c not in CATEGORY_TAGS]
    if unknown:
        error_exit(
            f"Unknown categor{'ies' if len(unknown) > 1 else 'y'} "
            f"{', '.join(repr(c) for c in unknown)}. "
            f"Valid categories: {', '.join(VALID_CATEGORIES)}"
        )

    radius = int(args.radius)
    limit  = int(args.limit)
    if radius <= 0:
        error_exit("Radius must be a positive integer (metres).")
    if limit <= 0:
        error_exit("Limit must be a positive integer.")

    # Query each category against the Overpass fallback chain, merge results,
    # dedupe by OSM identity so POIs tagged under multiple categories don't
    # appear twice.
    merged = {}
    for category in categories:
        tag_pairs = _tags_for(category)
        religion = RELIGION_FILTER.get(category)
        query = build_overpass_nearby(None, None, lat, lon, radius, limit,
                                      religion=religion, tag_pairs=tag_pairs)
        raw = overpass_query(query)
        elements = raw.get("elements", [])
        for place in parse_overpass_elements(elements, ref_lat=lat, ref_lon=lon):
            place["category"] = category
            key = (place.get("osm_type", ""), place.get("osm_id", ""))
            # Prefer the entry that actually has a distance_m attached (first
            # pass through the ref_lat/ref_lon branch), then first-seen wins.
            if key not in merged:
                merged[key] = place

    # Sort merged by distance when we have ref lat/lon, then cap at ``limit``.
    places = sorted(
        merged.values(),
        key=lambda p: p.get("distance_m", float("inf")),
    )[:limit]

    print_json({
        "center_lat":  lat,
        "center_lon":  lon,
        "categories":  categories,
        "radius_m":    radius,
        "count":       len(places),
        "results":     places,
        "data_source": DATA_SOURCE,
    })


# ---------------------------------------------------------------------------
# Command: distance
# ---------------------------------------------------------------------------

def cmd_distance(args):
    """Calculate road distance and travel time between two places."""
    origin_query      = " ".join(args.origin)
    destination_query = " ".join(args.to)
    mode              = args.mode.lower()

    if mode not in OSRM_PROFILES:
        error_exit(f"Invalid mode '{mode}'. Choose from: {', '.join(OSRM_PROFILES)}")

    # Geocode origin and destination
    o_lat, o_lon, o_name = geocode_single(origin_query)
    d_lat, d_lon, d_name = geocode_single(destination_query)

    profile = OSRM_PROFILES[mode]
    url = (
        f"{OSRM_BASE}/{profile}/"
        f"{o_lon},{o_lat};{d_lon},{d_lat}"
        f"?overview=false&steps=false"
    )

    osrm_data = http_get(url)

    if osrm_data.get("code") != "Ok":
        error_exit(
            f"OSRM routing failed: "
            f"{osrm_data.get('message', osrm_data.get('code', 'unknown error'))}"
        )

    routes = osrm_data.get("routes", [])
    if not routes:
        error_exit("No route found between the two locations.")

    route        = routes[0]
    distance_m   = route.get("distance", 0)
    duration_s   = route.get("duration", 0)
    distance_km  = round(distance_m / 1000, 3)
    duration_min = round(duration_s / 60, 2)

    # Straight-line distance for reference
    straight_m = haversine_m(o_lat, o_lon, d_lat, d_lon)

    print_json({
        "origin": {
            "query":        origin_query,
            "display_name": o_name,
            "lat":          o_lat,
            "lon":          o_lon,
        },
        "destination": {
            "query":        destination_query,
            "display_name": d_name,
            "lat":          d_lat,
            "lon":          d_lon,
        },
        "mode":             mode,
        "distance_km":      distance_km,
        "distance_m":       round(distance_m, 1),
        "duration_minutes": duration_min,
        "duration_seconds": round(duration_s, 1),
        "straight_line_km": round(straight_m / 1000, 3),
        "data_source":      DATA_SOURCE,
    })


# ---------------------------------------------------------------------------
# Command: directions
# ---------------------------------------------------------------------------

def _format_duration(seconds):
    """Format seconds into a human-readable string."""
    if seconds < 60:
        return f"{round(seconds)}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{round(minutes, 1)} min"
    hours = int(minutes // 60)
    remaining = round(minutes % 60)
    return f"{hours}h {remaining}min"


def _format_distance(metres):
    """Format metres into a human-readable string."""
    if metres < 1000:
        return f"{round(metres)} m"
    return f"{round(metres / 1000, 2)} km"


def cmd_directions(args):
    """Get turn-by-turn directions between two places via OSRM."""
    origin_query      = " ".join(args.origin)
    destination_query = " ".join(args.to)
    mode              = args.mode.lower()

    if mode not in OSRM_PROFILES:
        error_exit(f"Invalid mode '{mode}'. Choose from: {', '.join(OSRM_PROFILES)}")

    # Geocode origin and destination
    o_lat, o_lon, o_name = geocode_single(origin_query)
    d_lat, d_lon, d_name = geocode_single(destination_query)

    profile = OSRM_PROFILES[mode]
    url = (
        f"{OSRM_BASE}/{profile}/"
        f"{o_lon},{o_lat};{d_lon},{d_lat}"
        f"?overview=false&steps=true"
    )

    osrm_data = http_get(url)

    if osrm_data.get("code") != "Ok":
        error_exit(
            f"OSRM routing failed: "
            f"{osrm_data.get('message', osrm_data.get('code', 'unknown error'))}"
        )

    routes = osrm_data.get("routes", [])
    if not routes:
        error_exit("No route found between the two locations.")

    route        = routes[0]
    distance_m   = route.get("distance", 0)
    duration_s   = route.get("duration", 0)

    # Extract steps from all legs
    steps = []
    step_num = 0
    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            maneuver = step.get("maneuver", {})
            step_dist = step.get("distance", 0)
            step_dur  = step.get("duration", 0)
            step_name = step.get("name", "")
            modifier  = maneuver.get("modifier", "")
            m_type    = maneuver.get("type", "")

            # Build instruction text
            if m_type == "depart":
                instruction = f"Depart on {step_name}" if step_name else "Depart"
            elif m_type == "arrive":
                instruction = "Arrive at destination"
            elif m_type == "turn":
                instruction = f"Turn {modifier} onto {step_name}" if step_name else f"Turn {modifier}"
            elif m_type == "new name":
                instruction = f"Continue onto {step_name}" if step_name else "Continue"
            elif m_type == "merge":
                instruction = f"Merge {modifier} onto {step_name}" if step_name else f"Merge {modifier}"
            elif m_type == "fork":
                instruction = f"Take the {modifier} fork onto {step_name}" if step_name else f"Take the {modifier} fork"
            elif m_type == "roundabout":
                instruction = f"Enter roundabout, exit onto {step_name}" if step_name else "Enter roundabout"
            elif m_type == "rotary":
                instruction = f"Enter rotary, exit onto {step_name}" if step_name else "Enter rotary"
            elif m_type == "end of road":
                instruction = f"At end of road, turn {modifier} onto {step_name}" if step_name else f"At end of road, turn {modifier}"
            elif m_type == "continue":
                instruction = f"Continue {modifier} on {step_name}" if step_name else f"Continue {modifier}"
            elif m_type == "on ramp":
                instruction = f"Take ramp onto {step_name}" if step_name else "Take ramp"
            elif m_type == "off ramp":
                instruction = f"Take exit onto {step_name}" if step_name else "Take exit"
            else:
                instruction = f"{m_type} {modifier} {step_name}".strip()

            step_num += 1
            steps.append({
                "step":        step_num,
                "instruction": instruction,
                "distance":    _format_distance(step_dist),
                "distance_m":  round(step_dist, 1),
                "duration":    _format_duration(step_dur),
                "duration_s":  round(step_dur, 1),
                "road_name":   step_name,
                "maneuver":    m_type,
            })

    print_json({
        "origin": {
            "query":        origin_query,
            "display_name": o_name,
            "lat":          o_lat,
            "lon":          o_lon,
        },
        "destination": {
            "query":        destination_query,
            "display_name": d_name,
            "lat":          d_lat,
            "lon":          d_lon,
        },
        "mode":               mode,
        "total_distance":     _format_distance(distance_m),
        "total_distance_m":   round(distance_m, 1),
        "total_duration":     _format_duration(duration_s),
        "total_duration_s":   round(duration_s, 1),
        "steps":              steps,
        "step_count":         len(steps),
        "data_source":        DATA_SOURCE,
    })


# ---------------------------------------------------------------------------
# Command: timezone
# ---------------------------------------------------------------------------

def cmd_timezone(args):
    """
    Get timezone information for a lat/lon coordinate.

    Strategy:
      1. Try TimeAPI.io (free, no key, supports coordinate-based lookup).
      2. Fallback: derive UTC offset approximation from longitude.
    """
    try:
        lat = float(args.lat)
        lon = float(args.lon)
    except ValueError:
        error_exit("LAT and LON must be numeric values.")

    if not (-90 <= lat <= 90):
        error_exit("Latitude must be between -90 and 90.")
    if not (-180 <= lon <= 180):
        error_exit("Longitude must be between -180 and 180.")

    timezone_str = None
    timezone_src = None
    current_time = None
    utc_offset   = None

    # --- Strategy 1: TimeAPI.io coordinate lookup ---
    try:
        params = {"latitude": lat, "longitude": lon}
        tz_data = http_get(TIMEAPI_BASE, params=params, silent=True)
        if isinstance(tz_data, dict):
            timezone_str = tz_data.get("timeZone")
            current_time = tz_data.get("currentLocalTime")
            # Build utc_offset from currentUtcOffset if available
            offset_info = tz_data.get("currentUtcOffset", {})
            if isinstance(offset_info, dict):
                oh = offset_info.get("hours", 0)
                om = abs(offset_info.get("minutes", 0))
                os_ = offset_info.get("seconds", 0)
                sign = "+" if oh >= 0 else "-"
                utc_offset = f"{sign}{abs(oh):02d}:{om:02d}"
                if os_:
                    utc_offset = f"{utc_offset}:{os_:02d}"
            elif tz_data.get("standardUtcOffset"):
                offset_info2 = tz_data["standardUtcOffset"]
                if isinstance(offset_info2, dict):
                    oh = offset_info2.get("hours", 0)
                    om = abs(offset_info2.get("minutes", 0))
                    os_ = offset_info2.get("seconds", 0)
                    sign = "+" if oh >= 0 else "-"
                    utc_offset = f"{sign}{abs(oh):02d}:{om:02d}"
                    if os_:
                        utc_offset = f"{utc_offset}:{os_:02d}"
            timezone_src = "timeapi.io"
    except (RuntimeError, KeyError, TypeError):
        pass  # API may be down; continue to fallback

    # --- Strategy 2: longitude-based UTC offset approximation ---
    if not timezone_str:
        approx_offset_h = round(lon / 15)
        if approx_offset_h >= 0:
            utc_offset = f"+{approx_offset_h:02d}:00"
        else:
            utc_offset = f"-{abs(approx_offset_h):02d}:00"
        timezone_str = f"UTC{utc_offset}"
        timezone_src = "longitude approximation (longitude/15)"

    print_json({
        "lat":          lat,
        "lon":          lon,
        "timezone":     timezone_str,
        "utc_offset":   utc_offset,
        "current_time": current_time,
        "source":       timezone_src,
        "data_source":  DATA_SOURCE,
    })


# ---------------------------------------------------------------------------
# Command: bbox
# ---------------------------------------------------------------------------

def cmd_bbox(args):
    """Find POIs within a bounding box using the Overpass API."""
    try:
        lat1 = float(args.lat1)
        lon1 = float(args.lon1)
        lat2 = float(args.lat2)
        lon2 = float(args.lon2)
    except ValueError:
        error_exit("All coordinate arguments must be numeric values.")

    # Normalize: south/west < north/east
    south = min(lat1, lat2)
    north = max(lat1, lat2)
    west  = min(lon1, lon2)
    east  = max(lon1, lon2)

    category = args.category.lower()
    if category not in CATEGORY_TAGS:
        error_exit(
            f"Unknown category '{category}'. "
            f"Valid categories: {', '.join(VALID_CATEGORIES)}"
        )

    limit = int(args.limit)
    if limit <= 0:
        error_exit("Limit must be a positive integer.")

    tag_pairs = _tags_for(category)
    religion = RELIGION_FILTER.get(category)
    query = build_overpass_bbox(None, None, south, west, north, east,
                                limit, religion=religion, tag_pairs=tag_pairs)

    raw = overpass_query(query)

    elements = raw.get("elements", [])

    # Use center of bbox as reference for distance sorting
    center_lat = (south + north) / 2
    center_lon = (west + east) / 2
    places = parse_overpass_elements(elements, ref_lat=center_lat,
                                     ref_lon=center_lon)

    for p in places:
        p["category"] = category

    print_json({
        "bounding_box": {
            "south": south,
            "west":  west,
            "north": north,
            "east":  east,
        },
        "category":    category,
        "count":       len(places),
        "results":     places,
        "data_source": DATA_SOURCE,
    })


# ---------------------------------------------------------------------------
# Command: area
# ---------------------------------------------------------------------------

def cmd_area(args):
    """Get bounding box and area info for a named place."""
    query = " ".join(args.place)
    raw = nominatim_search(query, limit=1)

    if not raw:
        error_exit(f"Could not find place: {query}")

    item = raw[0]
    bb = item.get("boundingbox", [])

    if len(bb) < 4:
        error_exit(f"No bounding box data available for: {query}")

    min_lat = float(bb[0])
    max_lat = float(bb[1])
    min_lon = float(bb[2])
    max_lon = float(bb[3])

    # Approximate area in km² using the bounding box
    # Width in km at the average latitude
    avg_lat = (min_lat + max_lat) / 2
    height_km = haversine_m(min_lat, min_lon, max_lat, min_lon) / 1000
    width_km  = haversine_m(avg_lat, min_lon, avg_lat, max_lon) / 1000
    approx_area_km2 = round(height_km * width_km, 3)

    print_json({
        "query":        query,
        "display_name": item.get("display_name", ""),
        "lat":          float(item["lat"]),
        "lon":          float(item["lon"]),
        "type":         item.get("type", ""),
        "category":     item.get("category", ""),
        "bounding_box": {
            "south": min_lat,
            "north": max_lat,
            "west":  min_lon,
            "east":  max_lon,
        },
        "dimensions": {
            "width_km":  round(width_km, 3),
            "height_km": round(height_km, 3),
        },
        "approx_area_km2": approx_area_km2,
        "osm_type":        item.get("osm_type", ""),
        "osm_id":          item.get("osm_id", ""),
        "data_source":     DATA_SOURCE,
    })


# ---------------------------------------------------------------------------
# Command: supplier-geo — 1688供应商地理位置分析
# ---------------------------------------------------------------------------

def _parse_suppliers_file(filepath):
    """Parse a CSV-like supplier file.

    Supported formats per line:
      - "<address>"                         (plain address)
      - "<name>,<city>"                     (name + city)
      - "<name>,<address>,<city>"           (full)

    Returns list of dicts: [{"name": ..., "query": ...}, ...]
    """
    suppliers = []
    with open(os.path.expanduser(filepath), encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) == 1:
                suppliers.append({"name": f"供应商{lineno}", "query": parts[0]})
            elif len(parts) >= 2:
                # Last part that looks like a city name → city, rest → address
                name = parts[0]
                rest = parts[1:]
                # Try to detect city vs full address by checking if last part
                # is a known Chinese city-ish pattern (short, not containing 区/路/街)
                maybe_city = rest[-1]
                if len(maybe_city) <= 6 and not any(k in maybe_city for k in ["区", "路", "街", "镇", "村", "工业园"]):
                    city = maybe_city
                    address = ",".join(rest[:-1])
                else:
                    city = ""
                    address = ",".join(rest)
                query = city if len(rest) == 1 else f"{address},{city}" if city else address
                suppliers.append({"name": name, "query": query, "city": city})
    return suppliers


def cmd_supplier_geo(args):
    """Batch geocode supplier names/addresses and produce geographic summary."""
    if args.file:
        suppliers = _parse_suppliers_file(args.file)
    elif args.json:
        try:
            suppliers = json.loads(args.json)
            if isinstance(suppliers, dict):
                suppliers = [suppliers]
        except json.JSONDecodeError as e:
            error_exit(f"Invalid JSON: {e}")
    else:
        error_exit("Provide --file or --json with supplier data.")

    if not suppliers:
        error_exit("No suppliers found in input.")

    results = []
    city_counts = {}
    lats, lons = [], []

    for s in suppliers:
        query = s.get("query", s.get("address", ""))
        try:
            lat, lon, display = geocode_single(query)
            s["lat"] = lat
            s["lon"] = lon
            s["display_name"] = display
            s["geocode_status"] = "ok"
            lats.append(lat)
            lons.append(lon)
            # Extract city/state from display for distribution
            parts = [p.strip() for p in display.split(",")]
            city = parts[-3] if len(parts) >= 3 else (parts[-1] if parts else "")
            city_counts[city] = city_counts.get(city, 0) + 1
        except Exception as e:
            s["geocode_status"] = "error"
            s["error"] = str(e)

        results.append({
            "name":     s.get("name", ""),
            "query":    s.get("query", ""),
            "lat":      s.get("lat"),
            "lon":      s.get("lon"),
            "city":     s.get("city", ""),
            "display_name": s.get("display_name", ""),
            "geocode_status": s.get("geocode_status", "unknown"),
        })
        time.sleep(NOMINATIM_RATE_LIMIT)

    # Geographic bounding box of successfully geocoded suppliers
    geocoded = [(r["lat"], r["lon"]) for r in results if r.get("lat")]
    summary = {}
    if geocoded:
        min_lat, max_lat = min(g[0] for g in geocoded), max(g[0] for g in geocoded)
        min_lon, max_lon = min(g[1] for g in geocoded), max(g[1] for g in geocoded)
        avg_lat = sum(g[0] for g in geocoded) / len(geocoded)
        width_km  = haversine_m(avg_lat, min_lon, avg_lat, max_lon) / 1000
        height_km = haversine_m(min_lat, min_lon, max_lat, min_lon) / 1000
        total_spread_km2 = round(width_km * height_km, 3)
        summary = {
            "geocoded_count": len(geocoded),
            "failed_count":   len(results) - len(geocoded),
            "bounding_box": {
                "south": round(min_lat, 5),
                "north": round(max_lat, 5),
                "west":  round(min_lon, 5),
                "east":  round(max_lon, 5),
            },
            "dimensions_km": {
                "width_km":  round(width_km, 3),
                "height_km": round(height_km, 3),
            },
            "approx_area_km2": total_spread_km2,
            "center_lat": round(avg_lat, 5),
            "center_lon": round((min_lon + max_lon) / 2, 5),
        }

    output = {
        "suppliers": results,
        "city_distribution": city_counts,
        "summary": summary,
        "data_source": DATA_SOURCE,
    }

    if args.output:
        with open(os.path.expanduser(args.output), "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        output["_note"] = f"Results written to {args.output}"

    print_json(output)


# ---------------------------------------------------------------------------
# Command: logistics-cost — 物流成本估算
# ---------------------------------------------------------------------------

# 内置物流计价参数（元）
LOGISTICS_PARAMS = {
    "express": {  # 快递（首重1kg + 续重）
        "first_kg":    8.0,
        "续重_per_kg": 5.0,
        "时效_days":   "2-4",
    },
    "truck": {  # 陆运（吨公里）
        "per_ton_km":  0.35,
        "min_charge":  50.0,
        "时效_days":   "3-7",
    },
    "air": {  # 空运
        "per_kg":      18.0,
        "min_charge":  120.0,
        "时效_days":   "1-2",
    },
}


def cmd_logistics_cost(args):
    """Estimate logistics costs from origin(s) to destination.

    支持 --from 传入单点（"深圳"）、多点（"广州,深圳,东莞"）或 --suppliers JSON。
    --to 为单一目的港。
    """
    mode = args.mode.lower()
    if mode not in LOGISTICS_PARAMS:
        error_exit(f"Invalid mode '{mode}'. Choose: {', '.join(LOGISTICS_PARAMS)}")

    params = LOGISTICS_PARAMS[mode]
    weight_kg = float(args.weight)

    # 体积重计算
    billable_kg = weight_kg
    if args.volume:
        try:
            l, w, h = [float(x.strip()) for x in args.volume.split(",")]
            vol_kg = (l * w * h) / 6000.0
            billable_kg = max(weight_kg, vol_kg)
        except Exception:
            error_exit("--volume must be L,W,H in cm, e.g. '60,40,30'")

    # 解析 from
    from_queries = []
    if args.suppliers_json:
        try:
            supplier_list = json.loads(args.suppliers_json)
            from_queries = [s.get("city") or s.get("address", "") for s in supplier_list]
        except json.JSONDecodeError as e:
            error_exit(f"Invalid --suppliers JSON: {e}")
    elif args.from_places:
        from_queries = [f.strip() for f in args.from_places.split(",")]
    else:
        error_exit("Provide --from or --suppliers.")

    # 解析 to
    to_query = " ".join(args.to) if isinstance(args.to, list) else args.to

    # Geocode 目的港
    try:
        to_lat, to_lon, to_name = geocode_single(to_query)
    except Exception as e:
        error_exit(f"Could not geocode destination: {e}")

    routes = []
    total_cost = 0.0

    for from_q in from_queries:
        if not from_q:
            continue
        time.sleep(NOMINATIM_RATE_LIMIT)
        try:
            from_lat, from_lon, from_name = geocode_single(from_q)
        except Exception:
            routes.append({"origin_query": from_q, "status": "geocode_error", "error": "Could not geocode"})
            continue

        # OSRM 道路距离
        profile = OSRM_PROFILES.get(args.route_mode or "driving", "driving")
        url = (
            f"{OSRM_BASE}/{profile}/"
            f"{from_lon},{from_lat};{to_lon},{to_lat}"
            f"?overview=false&steps=false"
        )
        road_km = None
        try:
            osrm_data = http_get(url, silent=True)
            if osrm_data.get("code") == "Ok" and osrm_data.get("routes"):
                road_km = osrm_data["routes"][0]["distance"] / 1000
        except Exception:
            pass

        # Fallback 直线距离
        straight_km = haversine_m(from_lat, from_lon, to_lat, to_lon) / 1000
        dist_km = round(road_km, 3) if road_km else round(straight_km, 3)

        # 费用计算
        if mode == "express":
            cost = params["first_kg"] + max(0, billable_kg - 1) * params["续重_per_kg"]
        elif mode == "truck":
            ton_km = (billable_kg / 1000.0) * dist_km
            cost = max(params["min_charge"], ton_km * params["per_ton_km"])
        else:  # air
            cost = max(params["min_charge"], billable_kg * params["per_kg"])

        cost = round(cost, 2)
        total_cost += cost

        routes.append({
            "origin_query":   from_q,
            "origin_name":    from_name,
            "origin_lat":     from_lat,
            "origin_lon":     from_lon,
            "dest_name":      to_name,
            "dest_lat":       to_lat,
            "dest_lon":       to_lon,
            "distance_km":    dist_km,
            "road_distance_km": round(road_km, 3) if road_km else None,
            "straight_km":    round(straight_km, 3),
            "weight_kg":      weight_kg,
            "billable_kg":    round(billable_kg, 2),
            "cost_rmb":       cost,
            "eta_days":       params["时效_days"],
            "mode":           mode,
            "status":         "ok",
        })

    print_json({
        "destination": {
            "query":   to_query,
            "name":    to_name,
            "lat":     to_lat,
            "lon":     to_lon,
        },
        "mode":          mode,
        "route_mode":     args.route_mode or "driving",
        "total_cost_rmb": round(total_cost, 2),
        "routes":         routes,
        "logistics_params": params,
        "data_source":    DATA_SOURCE,
    })


# ---------------------------------------------------------------------------
# Command: supplier-clusters — 供应商聚类分析
# ---------------------------------------------------------------------------

def _kmeans_simple(points, k, max_iter=50):
    """Simple K-Means clustering using Euclidean distance on (lat, lon).
    points: list of (lat, lon) tuples.
    Returns: list of cluster assignments (0..k-1), list of centroids.
    """
    import random
    # K-Means++ initialization
    centroids = [points[random.randint(0, len(points) - 1)]]
    for _ in range(k - 1):
        dists = [min((p[0] - c[0])**2 + (p[1] - c[1])**2 for c in centroids) for p in points]
        probs = [d / sum(dists) for d in dists]
        centroids.append(points[random.choices(range(len(points)), weights=probs)[0]])

    assignments = [-1] * len(points)
    for _ in range(max_iter):
        # Assign
        new_assign = []
        for p in points:
            dists = [(p[0] - c[0])**2 + (p[1] - c[1])**2 for c in centroids]
            new_assign.append(dists.index(min(dists)))
        # Check convergence
        if new_assign == assignments:
            break
        assignments = new_assign
        # Update centroids
        for ci in range(k):
            members = [points[i] for i, a in enumerate(assignments) if a == ci]
            if members:
                centroids[ci] = (
                    sum(m[0] for m in members) / len(members),
                    sum(m[1] for m in members) / len(members),
                )
    return assignments, centroids


def _silhouette_score(points, assignments, centroids):
    """Approximate silhouette score. Higher=better separation."""
    k = len(centroids)
    scores = []
    for i, p in enumerate(points):
        ci = assignments[i]
        # intra-cluster distance to centroid
        a = ((p[0] - centroids[ci][0])**2 + (p[1] - centroids[ci][1])**2) ** 0.5
        # nearest other cluster
        b = min(
            ((p[0] - centroids[oc][0])**2 + (p[1] - centroids[oc][1])**2) ** 0.5
            for oc in range(k) if oc != ci
        ) if k > 1 else 0
        s = (b - a) / max(a, b, 1e-9)
        scores.append(s)
    return sum(scores) / len(scores) if scores else 0


def cmd_supplier_clusters(args):
    """Cluster supplier coordinates and output GeoJSON for visualization."""
    # Parse suppliers
    if args.file:
        suppliers_raw = _parse_suppliers_file(args.file)
        # Geocode all
        suppliers = []
        for s in suppliers_raw:
            time.sleep(NOMINATIM_RATE_LIMIT)
            try:
                lat, lon, _ = geocode_single(s.get("query", ""))
                suppliers.append({"name": s.get("name", ""), "lat": lat, "lon": lon})
            except Exception:
                pass
    elif args.coords:
        try:
            suppliers = json.loads(args.coords)
        except json.JSONDecodeError as e:
            error_exit(f"Invalid --coords JSON: {e}")
    elif args.suppliers:
        try:
            suppliers = json.loads(args.suppliers)
        except json.JSONDecodeError as e:
            error_exit(f"Invalid --suppliers JSON: {e}")
    else:
        error_exit("Provide --file, --coords, or --suppliers with supplier data.")

    if not suppliers:
        error_exit("No valid suppliers with coordinates found.")

    points = [(s["lat"], s["lon"]) for s in suppliers]

    # Auto-K
    if args.auto_k:
        best_k, best_score = 2, -1
        for k in range(2, min(8, len(points))):
            assign, cents = _kmeans_simple(points, k)
            score = _silhouette_score(points, assign, cents)
            if score > best_score:
                best_k, best_score, best_assign, best_cents = k, score, assign, cents
        k = best_k
        assignments = best_assign
        centroids = best_cents
        sil_score = round(best_score, 4)
    else:
        k = int(args.k) if args.k else 3
        k = min(k, len(points))
        assignments, centroids = _kmeans_simple(points, k)
        sil_score = round(_silhouette_score(points, assignments, centroids), 4)

    # Build per-cluster info
    CLUSTER_COLORS = ["#E63946", "#457B9D", "#2A9D8F", "#E9C46A", "#F4A261", "#A855F7"]
    clusters = []
    for ci in range(k):
        members = [s for i, s in enumerate(suppliers) if assignments[i] == ci]
        member_coords = [(s["lat"], s["lon"]) for s in members]
        # Cluster radius = max distance from centroid
        radius_km = 0.0
        if member_coords:
            radius_km = max(
                haversine_m(m[0], m[1], centroids[ci][0], centroids[ci][1]) / 1000
                for m in member_coords
            )
        # Average intra-cluster spacing
        if len(member_coords) > 1:
            spacing = sum(
                haversine_m(member_coords[i][0], member_coords[i][1],
                             member_coords[j][0], member_coords[j][1])
                for i in range(len(member_coords))
                for j in range(i + 1, len(member_coords))
            ) / (len(member_coords) * (len(member_coords) - 1) / 2)
            avg_spacing_km = round(spacing / 1000, 3)
        else:
            avg_spacing_km = 0

        clusters.append({
            "cluster_id":    ci,
            "center_lat":    round(centroids[ci][0], 6),
            "center_lon":    round(centroids[ci][1], 6),
            "member_count":  len(members),
            "radius_km":     round(radius_km, 3),
            "avg_spacing_km": avg_spacing_km,
            "color":         CLUSTER_COLORS[ci % len(CLUSTER_COLORS)],
            "members":       [{"name": m.get("name", ""), "lat": m["lat"], "lon": m["lon"]} for m in members],
        })

    # Build GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [s["lon"], s["lat"]],
                },
                "properties": {
                    "name":   s.get("name", ""),
                    "cluster": assignments[i],
                    "color":  CLUSTER_COLORS[assignments[i] % len(CLUSTER_COLORS)],
                },
            }
            for i, s in enumerate(suppliers)
        ] + [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [centroids[ci][1], centroids[ci][0]],
                },
                "properties": {
                    "name":    f"Cluster {ci} Center",
                    "cluster": ci,
                    "center":  True,
                    "color":   CLUSTER_COLORS[ci % len(CLUSTER_COLORS)],
                },
            }
            for ci in range(k)
        ],
    }

    output = {
        "k":             k,
        "silhouette_score": sil_score,
        "clusters":      clusters,
        "geojson":       geojson,
        "data_source":   DATA_SOURCE,
    }

    if args.output:
        out_path = os.path.expanduser(args.output)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(geojson, f, indent=2, ensure_ascii=False)
        output["_note"] = f"GeoJSON written to {out_path}"

    print_json(output)


# ---------------------------------------------------------------------------
# Command: delivery-heatmap — 交货距离热力图
# ---------------------------------------------------------------------------

HEAT_COLORS = {
    "near":   "#2ECC71",   # < 100km 绿
    "medium": "#F39C12",   # 100-300km 黄
    "far":    "#E74C3C",   # > 300km 红
}


def _distance_band(dist_km):
    if dist_km < 100:
        return "near", "<100km", HEAT_COLORS["near"]
    elif dist_km < 300:
        return "medium", "100-300km", HEAT_COLORS["medium"]
    else:
        return "far", ">300km", HEAT_COLORS["far"]


def cmd_delivery_heatmap(args):
    """Compute supplier-to-destination distances and render heatmap."""
    # Parse suppliers
    if args.file:
        suppliers_raw = _parse_suppliers_file(args.file)
        suppliers = []
        for s in suppliers_raw:
            time.sleep(NOMINATIM_RATE_LIMIT)
            try:
                lat, lon, _ = geocode_single(s.get("query", ""))
                suppliers.append({"name": s.get("name", ""), "lat": lat, "lon": lon})
            except Exception:
                pass
    elif args.suppliers:
        try:
            suppliers = json.loads(args.suppliers)
        except json.JSONDecodeError as e:
            error_exit(f"Invalid --suppliers JSON: {e}")
    else:
        error_exit("Provide --file or --suppliers with supplier data.")

    if not suppliers:
        error_exit("No valid suppliers with coordinates found.")

    # Geocode destination
    dest_query = " ".join(args.dest) if isinstance(args.dest, list) else args.dest
    time.sleep(NOMINATIM_RATE_LIMIT)
    try:
        dest_lat, dest_lon, dest_name = geocode_single(dest_query)
    except Exception as e:
        error_exit(f"Could not geocode destination: {e}")

    use_road = (args.mode or "straight") == "driving"
    profile = OSRM_PROFILES.get("driving", "driving")

    rows = []
    for s in suppliers:
        lat, lon = s["lat"], s["lon"]
        straight_km = haversine_m(lat, lon, dest_lat, dest_lon) / 1000
        road_km = None
        if use_road:
            url = (
                f"{OSRM_BASE}/{profile}/"
                f"{lon},{lat};{dest_lon},{dest_lat}"
                f"?overview=false&steps=false"
            )
            try:
                osrm_data = http_get(url, silent=True)
                if osrm_data.get("code") == "Ok" and osrm_data.get("routes"):
                    road_km = osrm_data["routes"][0]["distance"] / 1000
            except Exception:
                pass

        dist_km = round(road_km, 3) if road_km else round(straight_km, 3)
        band_key, band_label, color = _distance_band(dist_km)
        rows.append({
            "name":          s.get("name", ""),
            "lat":           lat,
            "lon":           lon,
            "straight_km":   round(straight_km, 3),
            "road_km":       round(road_km, 3) if road_km else None,
            "distance_km":   dist_km,
            "band_key":      band_key,
            "band_label":    band_label,
            "color":         color,
        })

    # Sort by distance
    rows.sort(key=lambda r: r["distance_km"])

    # Band summary
    band_summary = {
        "near":   {"count": 0, "color": HEAT_COLORS["near"], "label": "<100km"},
        "medium": {"count": 0, "color": HEAT_COLORS["medium"], "label": "100-300km"},
        "far":    {"count": 0, "color": HEAT_COLORS["far"], "label": ">300km"},
    }
    for r in rows:
        band_summary[r["band_key"]]["count"] += 1

    # SVG heatmap (simple scatter-style)
    if args.format == "svg":
        svg_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600">',
            f'  <title>供应商交货距离热力图 - {dest_name}</title>',
            f'  <rect width="800" height="600" fill="#f8f9fa"/>',
            f'  <text x="400" y="30" text-anchor="middle" font-size="16" font-weight="bold">',
            f'    供应商→{dest_name} 交货距离热力图</text>',
        ]
        # Legend
        for bi, (key, info) in enumerate(band_summary.items()):
            x, y = 20 + bi * 140, 560
            svg_lines.append(
                f'  <rect x="{x}" y="{y}" width="20" height="14" fill="{info["color"]}"/>'
                f'<text x="{x+25}" y="{y+12}" font-size="12">{info["label"]} ({info["count"]}家)</text>'
            )
        # Destination marker
        svg_lines.append(
            f'  <circle cx="650" cy="300" r="12" fill="#333" stroke="#fff" stroke-width="2"/>'
            f'<text x="650" y="330" text-anchor="middle" font-size="11">目的地</text>'
        )
        # Supplier dots — positioned roughly by lat/lon spread
        all_lats = [r["lat"] for r in rows]
        all_lons = [r["lon"] for r in rows]
        lat_min, lat_max = min(all_lats), max(all_lats)
        lon_min, lon_max = min(all_lons), max(all_lons)
        lat_range = max(lat_max - lat_min, 0.001)
        lon_range = max(lon_max - lon_min, 0.001)
        for r in rows:
            # Map supplier coords to SVG area (50,50 to 600,550)
            px = int(50 + (r["lon"] - lon_min) / lon_range * 550)
            py = int(550 - (r["lat"] - lat_min) / lat_range * 500)
            svg_lines.append(
                f'  <circle cx="{px}" cy="{py}" r="8" fill="{r["color"]}" opacity="0.85"/>'
                f'<title>{r["name"]}: {r["distance_km"]}km</title>'
            )
        svg_lines.append('</svg>')
        svg_content = "\n".join(svg_lines)

        out_path = os.path.expanduser(args.output) if args.output else "/tmp/delivery_heatmap.svg"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
        svg_note = f"SVG saved to {out_path}"
    else:
        svg_note = None

    output = {
        "destination": {
            "query": dest_query,
            "name":   dest_name,
            "lat":    dest_lat,
            "lon":    dest_lon,
        },
        "mode":          args.mode or "straight",
        "supplier_count": len(rows),
        "band_summary":  band_summary,
        "distance_table": rows,
        "svg_path":      out_path if svg_note else None,
        "data_source":   DATA_SOURCE,
    }
    if svg_note:
        output["_note"] = svg_note

    if args.output and args.format != "svg":
        with open(os.path.expanduser(args.output), "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        output["_note"] = f"Results written to {args.output}"

    print_json(output)


# ---------------------------------------------------------------------------
# CLI setup
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="maps_client.py",
        description=(
            "CLI maps tool: geocoding, reverse geocoding, POI search, "
            "routing, directions, timezone, and area lookup. "
            "Powered by OpenStreetMap, OSRM, Overpass, and TimeAPI.io. "
            "No API keys required."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  maps_client.py search Times Square\n"
            "  maps_client.py reverse 40.758 -73.985\n"
            "  maps_client.py nearby 40.758 -73.985 restaurant --radius 800\n"
            "  maps_client.py distance New York --to Los Angeles --mode driving\n"
            "  maps_client.py directions Paris --to Berlin --mode driving\n"
            "  maps_client.py timezone 48.8566 2.3522\n"
            "  maps_client.py bbox 40.70 -74.02 40.78 -73.95 restaurant\n"
            "  maps_client.py area Manhattan"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True,
                                 metavar="COMMAND")

    # -- search --
    p_search = sub.add_parser(
        "search",
        help="Geocode a place name to coordinates.",
        description="Search for a place by name and return coordinates and details.",
    )
    p_search.add_argument(
        "query", nargs="+",
        help="Place name or address to search.",
    )

    # -- reverse --
    p_reverse = sub.add_parser(
        "reverse",
        help="Reverse geocode coordinates to an address.",
        description="Convert latitude/longitude coordinates to a human-readable address.",
    )
    p_reverse.add_argument("lat", help="Latitude (decimal degrees).")
    p_reverse.add_argument("lon", help="Longitude (decimal degrees).")

    # -- nearby --
    p_nearby = sub.add_parser(
        "nearby",
        help="Find nearby places of a given category.",
        description=(
            "Find points of interest near a location using the Overpass API.\n"
            "Provide either LAT/LON, or use --near \"<address>\" to auto-geocode.\n"
            "Categories can be specified positionally OR repeated via --category\n"
            "to merge multiple types in one query (e.g. --category bar --category cafe).\n"
            f"Categories: {', '.join(VALID_CATEGORIES)}"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_nearby.add_argument(
        "lat", nargs="?", default=None,
        help="Center latitude (decimal degrees). Omit if using --near.",
    )
    p_nearby.add_argument(
        "lon", nargs="?", default=None,
        help="Center longitude (decimal degrees). Omit if using --near.",
    )
    p_nearby.add_argument(
        "category", nargs="?", default=None,
        help="POI category (use --help for full list). Omit if using --category flags.",
    )
    p_nearby.add_argument(
        "--near", nargs="+", metavar="PLACE",
        help="Address, city, or landmark to search around (geocoded via Nominatim).",
    )
    p_nearby.add_argument(
        "--category", action="append", dest="category_list", default=[],
        metavar="CAT",
        help="POI category (repeatable — adds a type to the search).",
    )
    p_nearby.add_argument(
        "--radius", "-r",
        default=500, type=int, metavar="METRES",
        help="Search radius in metres (default: 500).",
    )
    p_nearby.add_argument(
        "--limit", "-n",
        default=10, type=int, metavar="N",
        help="Maximum number of results (default: 10).",
    )

    # -- distance --
    p_dist = sub.add_parser(
        "distance",
        help="Calculate road distance and travel time.",
        description=(
            "Calculate road distance and estimated travel time between two places.\n"
            "Example: maps_client.py distance New York --to Los Angeles"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_dist.add_argument(
        "origin", nargs="+",
        help="Origin address or place name.",
    )
    p_dist.add_argument(
        "--to", nargs="+", required=True, metavar="DEST",
        help="Destination address or place name (required).",
    )
    p_dist.add_argument(
        "--mode", "-m",
        default="driving",
        choices=list(OSRM_PROFILES.keys()),
        help="Travel mode (default: driving).",
    )

    # -- directions --
    p_dir = sub.add_parser(
        "directions",
        help="Get turn-by-turn directions between two places.",
        description=(
            "Get step-by-step navigation directions between two places.\n"
            "Example: maps_client.py directions Paris --to Berlin --mode driving"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_dir.add_argument(
        "origin", nargs="+",
        help="Origin address or place name.",
    )
    p_dir.add_argument(
        "--to", nargs="+", required=True, metavar="DEST",
        help="Destination address or place name (required).",
    )
    p_dir.add_argument(
        "--mode", "-m",
        default="driving",
        choices=list(OSRM_PROFILES.keys()),
        help="Travel mode (default: driving).",
    )

    # -- timezone --
    p_tz = sub.add_parser(
        "timezone",
        help="Get timezone information for coordinates.",
        description="Look up timezone and current local time for a lat/lon coordinate.",
    )
    p_tz.add_argument("lat", help="Latitude (decimal degrees).")
    p_tz.add_argument("lon", help="Longitude (decimal degrees).")

    # -- bbox --
    p_bbox = sub.add_parser(
        "bbox",
        help="Find POIs within a bounding box.",
        description=(
            "Search for points of interest within a geographic bounding box.\n"
            "Tip: use the 'area' command to find bounding boxes for named places.\n"
            f"Categories: {', '.join(VALID_CATEGORIES)}"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_bbox.add_argument("lat1", help="First corner latitude.")
    p_bbox.add_argument("lon1", help="First corner longitude.")
    p_bbox.add_argument("lat2", help="Second corner latitude.")
    p_bbox.add_argument("lon2", help="Second corner longitude.")
    p_bbox.add_argument("category", help="POI category to search for.")
    p_bbox.add_argument(
        "--limit", "-n",
        default=20, type=int, metavar="N",
        help="Maximum number of results (default: 20).",
    )

    # -- area --
    p_area = sub.add_parser(
        "area",
        help="Get bounding box and area info for a named place.",
        description=(
            "Look up a place by name and return its bounding box, dimensions, "
            "and approximate area. Useful as input to the 'bbox' command."
        ),
    )
    p_area.add_argument(
        "place", nargs="+",
        help="Place name to look up (e.g., 'Manhattan' or 'downtown Seattle').",
    )

    # -- supplier-geo --
    p_sg = sub.add_parser(
        "supplier-geo",
        help="1688供应商地理位置分析 — 批量解析供应商地址→GPS坐标+分布统计",
        description=(
            "Parse a supplier list (name/address/city), batch geocode to GPS, "
            "and produce geographic distribution statistics.\n"
            "Input: --file CSV or --json array. Output: coordinate table, "
            "city histogram, bounding box, and coverage area."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_sg.add_argument(
        "--file", "-f", metavar="PATH",
        help="CSV-like file with one supplier per line (see SKILL.md for format).",
    )
    p_sg.add_argument(
        "--json", "-j", metavar="JSON",
        help="JSON array of supplier objects: [{\"name\":..., \"city\":...}, ...].",
    )
    p_sg.add_argument(
        "--output", "-o", metavar="PATH",
        help="Save full JSON output to a file.",
    )

    # -- logistics-cost --
    p_lc = sub.add_parser(
        "logistics-cost",
        help="物流成本估算 — 距离×重量×运输模式计价",
        description=(
            "Estimate logistics costs from origin(s) to a destination port.\n"
            "Modes: express (快递, 首重+续重), truck (陆运, 吨公里), air (空运).\n"
            "Example: logistics-cost --from '广州,深圳' --to '北京' --weight 500 --mode truck"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_lc.add_argument(
        "--from", "-f", dest="from_places", metavar="ORIGINS",
        help="Comma-separated origin cities/addresses. Example: '广州,深圳,东莞'",
    )
    p_lc.add_argument(
        "--to", "-t", nargs="+", metavar="DEST",
        help="Destination (city or address).",
    )
    p_lc.add_argument(
        "--weight", "-w", required=True, metavar="KG",
        help="Cargo weight in kilograms.",
    )
    p_lc.add_argument(
        "--mode", "-m", default="truck",
        choices=["express", "truck", "air"],
        help="Transport mode (default: truck).",
    )
    p_lc.add_argument(
        "--volume", "-v", metavar="L,W,H",
        help="Package dimensions in cm (e.g. '60,40,30'). Used for volumetric weight.",
    )
    p_lc.add_argument(
        "--route-mode", "-r", default="driving",
        choices=["driving", "walking", "cycling"],
        help="OSRM routing profile for distance (default: driving).",
    )
    p_lc.add_argument(
        "--suppliers", "-s", dest="suppliers_json", metavar="JSON",
        help="JSON array of suppliers [{city/address}, ...] as origins.",
    )

    # -- supplier-clusters --
    p_sc = sub.add_parser(
        "supplier-clusters",
        help="供应商集群可视化 — KMeans聚类+GeoJSON地图",
        description=(
            "Cluster supplier coordinates using K-Means and output GeoJSON.\n"
            "Useful for identifying geographic supplier hubs.\n"
            "Example: supplier-clusters --coords '[{\"name\":\"A\",\"lat\":22.5,\"lon\":113.9}]' --k 3"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_sc.add_argument(
        "--file", "-f", metavar="PATH",
        help="Supplier CSV file (auto-geocodes each entry).",
    )
    p_sc.add_argument(
        "--coords", "-c", metavar="JSON",
        help="JSON array of {name, lat, lon} objects (pre-geocoded).",
    )
    p_sc.add_argument(
        "--suppliers", "-s", metavar="JSON",
        help="Alias for --coords (same format).",
    )
    p_sc.add_argument(
        "--k", "-k", metavar="N", default="3",
        help="Number of clusters (default: 3). Use --auto-k to auto-select.",
    )
    p_sc.add_argument(
        "--auto-k", action="store_true",
        help="Automatically select optimal K using silhouette score (2-7).",
    )
    p_sc.add_argument(
        "--output", "-o", metavar="PATH",
        help="Save GeoJSON to file.",
    )

    # -- delivery-heatmap --
    p_dh = sub.add_parser(
        "delivery-heatmap",
        help="交货距离热力图 — 供应商→目的港距离分级+SVG地图",
        description=(
            "Calculate supplier-to-destination distances and render a heatmap.\n"
            "Distance bands: <100km (green), 100-300km (yellow), >300km (red).\n"
            "Example: delivery-heatmap --suppliers '[{...}]' --dest '广州' --format svg"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_dh.add_argument(
        "--file", "-f", metavar="PATH",
        help="Supplier CSV file (auto-geocodes each entry).",
    )
    p_dh.add_argument(
        "--suppliers", "-s", metavar="JSON",
        help="JSON array of {name, lat, lon} or {name, city/address}.",
    )
    p_dh.add_argument(
        "--dest", "-d", nargs="+", metavar="DEST",
        help="Destination city or address (required).",
    )
    p_dh.add_argument(
        "--mode", "-m", default="straight",
        choices=["straight", "driving"],
        help="Distance mode: straight (default) or driving (OSRM road distance).",
    )
    p_dh.add_argument(
        "--format", default="json",
        choices=["json", "svg"],
        help="Output format (default: json). svg generates a simple scatter map.",
    )
    p_dh.add_argument(
        "--output", "-o", metavar="PATH",
        help="Save output to file.",
    )

    return parser


def main():
    parser = build_parser()
    args   = parser.parse_args()

    dispatch = {
        "search":            cmd_search,
        "reverse":           cmd_reverse,
        "nearby":           cmd_nearby,
        "distance":          cmd_distance,
        "directions":        cmd_directions,
        "timezone":          cmd_timezone,
        "bbox":             cmd_bbox,
        "area":             cmd_area,
        "supplier-geo":     cmd_supplier_geo,
        "logistics-cost":   cmd_logistics_cost,
        "supplier-clusters": cmd_supplier_clusters,
        "delivery-heatmap":  cmd_delivery_heatmap,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        error_exit(f"Unknown command: {args.command}")

    handler(args)


if __name__ == "__main__":
    main()
