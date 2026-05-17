---
name: maps
description: "Geocode, POIs, routes, timezones via OpenStreetMap/OSRM."
version: 1.3.0
author: Mibayy
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [maps, geocoding, places, routing, distance, directions, nearby, location, openstreetmap, nominatim, overpass, osrm]
    category: productivity
    requires_toolsets: [terminal]
    supersedes: [find-nearby]
---

# Maps Skill

Location intelligence using free, open data sources. 8 commands, 44 POI
categories, zero dependencies (Python stdlib only), no API key required.

Data sources: OpenStreetMap/Nominatim, Overpass API, OSRM, TimeAPI.io.

This skill supersedes the old `find-nearby` skill — all of find-nearby's
functionality is covered by the `nearby` command below, with the same
`--near "<place>"` shortcut and multi-category support.

## When to Use

- User sends a Telegram location pin (latitude/longitude in the message) → `nearby`
- User wants coordinates for a place name → `search`
- User has coordinates and wants the address → `reverse`
- User asks for nearby restaurants, hospitals, pharmacies, hotels, etc. → `nearby`
- User wants driving/walking/cycling distance or travel time → `distance`
- User wants turn-by-turn directions between two places → `directions`
- User wants timezone information for a location → `timezone`
- User wants to search for POIs within a geographic area → `area` + `bbox`

## Prerequisites

Python 3.8+ (stdlib only — no pip installs needed).

Script path: `~/.hermes/skills/maps/scripts/maps_client.py`

## Commands

```bash
MAPS=~/.hermes/skills/maps/scripts/maps_client.py
```

### search — Geocode a place name

```bash
python3 $MAPS search "Eiffel Tower"
python3 $MAPS search "1600 Pennsylvania Ave, Washington DC"
```

Returns: lat, lon, display name, type, bounding box, importance score.

### reverse — Coordinates to address

```bash
python3 $MAPS reverse 48.8584 2.2945
```

Returns: full address breakdown (street, city, state, country, postcode).

### nearby — Find places by category

```bash
# By coordinates (from a Telegram location pin, for example)
python3 $MAPS nearby 48.8584 2.2945 restaurant --limit 10
python3 $MAPS nearby 40.7128 -74.0060 hospital --radius 2000

# By address / city / zip / landmark — --near auto-geocodes
python3 $MAPS nearby --near "Times Square, New York" --category cafe
python3 $MAPS nearby --near "90210" --category pharmacy

# Multiple categories merged into one query
python3 $MAPS nearby --near "downtown austin" --category restaurant --category bar --limit 10
```

46 categories: restaurant, cafe, bar, hospital, pharmacy, hotel, guest_house,
camp_site, supermarket, atm, gas_station, parking, museum, park, school,
university, bank, police, fire_station, library, airport, train_station,
bus_stop, church, mosque, synagogue, dentist, doctor, cinema, theatre, gym,
swimming_pool, post_office, convenience_store, bakery, bookshop, laundry,
car_wash, car_rental, bicycle_rental, taxi, veterinary, zoo, playground,
stadium, nightclub.

Each result includes: `name`, `address`, `lat`/`lon`, `distance_m`,
`maps_url` (clickable Google Maps link), `directions_url` (Google Maps
directions from the search point), and promoted tags when available —
`cuisine`, `hours` (opening_hours), `phone`, `website`.

### distance — Travel distance and time

```bash
python3 $MAPS distance "Paris" --to "Lyon"
python3 $MAPS distance "New York" --to "Boston" --mode driving
python3 $MAPS distance "Big Ben" --to "Tower Bridge" --mode walking
```

Modes: driving (default), walking, cycling. Returns road distance, duration,
and straight-line distance for comparison.

### directions — Turn-by-turn navigation

```bash
python3 $MAPS directions "Eiffel Tower" --to "Louvre Museum" --mode walking
python3 $MAPS directions "JFK Airport" --to "Times Square" --mode driving
```

Returns numbered steps with instruction, distance, duration, road name, and
maneuver type (turn, depart, arrive, etc.).

### timezone — Timezone for coordinates

```bash
python3 $MAPS timezone 48.8584 2.2945
python3 $MAPS timezone 35.6762 139.6503
```

Returns timezone name, UTC offset, and current local time.

### area — Bounding box and area for a place

```bash
python3 $MAPS area "Manhattan, New York"
python3 $MAPS area "London"
```

Returns bounding box coordinates, width/height in km, and approximate area.
Useful as input for the bbox command.

### bbox — Search within a bounding box

```bash
python3 $MAPS bbox 40.75 -74.00 40.77 -73.98 restaurant --limit 20
```

Finds POIs within a geographic rectangle. Use `area` first to get the
bounding box coordinates for a named place.

## Working With Telegram Location Pins

When a user sends a location pin, the message contains `latitude:` and
`longitude:` fields. Extract those and pass them straight to `nearby`:

```bash
# User sent a pin at 36.17, -115.14 and asked "find cafes nearby"
python3 $MAPS nearby 36.17 -115.14 cafe --radius 1500
```

Present results as a numbered list with names, distances, and the
`maps_url` field so the user gets a tap-to-open link in chat. For "open
now?" questions, check the `hours` field; if missing or unclear, verify
with `web_search` since OSM hours are community-maintained and not always
current.

## Workflow Examples

**"Find Italian restaurants near the Colosseum":**
1. `nearby --near "Colosseum Rome" --category restaurant --radius 500`
   — one command, auto-geocoded

**"What's near this location pin they sent?":**
1. Extract lat/lon from the Telegram message
2. `nearby LAT LON cafe --radius 1500`

**"How do I walk from hotel to conference center?":**
1. `directions "Hotel Name" --to "Conference Center" --mode walking`

**"What restaurants are in downtown Seattle?":**
1. `area "Downtown Seattle"` → get bounding box
2. `bbox S W N E restaurant --limit 30`

---

## 1688 Supplier Intelligence Commands

Four commands purpose-built for 1688 wholesale supplier analysis and procurement
logistics. All use Nominatim/OSRM with no API key required.

### supplier-geo — 供应商地理位置分析

解析供应商列表（名称/地址/城市），批量获取GPS坐标，进行地理分布统计分析。

```bash
# 从CSV文件读取供应商（格式：名称,地址 或 名称,城市）
python3 $MAPS supplier-geo --file suppliers.csv
# 文件格式：每行一条记录，支持以下格式
#   深圳市龙华区XXX工业园  （纯地址）
#   广州白云区XXX公司,广州  （名称,城市）

# 纯坐标列表（JSON数组，每项包含 name + address/city）
python3 $MAPS supplier-geo --json '[{"name":"A工厂","city":"深圳"},{"name":"B公司","city":"广州"}]'

# 指定输出文件保存结果
python3 $MAPS supplier-geo --file suppliers.csv --output supplier_locations.json
```

返回：供应商坐标表、省/城市分布直方图、地理边界外接矩形（convex hull近似）、总覆盖面积。

### logistics-cost — 物流成本估算

基于距离和运输模式估算物流成本。模型：快递(首重+续重)、陆运(吨公里计价)、空运(急件)。

```bash
# 单供应商→目的港估算
python3 $MAPS logistics-cost --from "深圳" --to "北京" --weight 500 --mode express
# weight: 公斤 | mode: express(快递)/truck(陆运)/air(空运)

# 多供应商到同一目的港（批量）
python3 $MAPS logistics-cost --from "广州,深圳,东莞" --to "上海" --weight 200 --mode truck

# 带体积重估算（长×宽×高 cm，体积重=体积/6000）
python3 $MAPS logistics-cost --from "义乌" --to "乌鲁木齐" --weight 100 --mode truck \
  --volume "60,40,30"
```

返回：各路线距离(km)、估算时效(天)、费用(元)、总成本。模型参数内置（快递首重1kg约8元+5元/续重kg；陆运0.35元/吨公里；空运18元/kg）。

### supplier-clusters — 供应商集群可视化

对供应商坐标进行聚类分析（KMeans），识别地理集群，生成可视化地图。

```bash
# 从坐标列表识别3个集群
python3 $MAPS supplier-clusters \
  --coords '[{"name":"A厂","lat":22.5,"lon":113.9},{"name":"B厂","lat":22.6,"lon":113.8},...]' \
  --k 3

# 从CSV读取坐标，自动选择最优K（轮廓系数）
python3 $MAPS supplier-clusters --file suppliers.csv --auto-k

# 保存聚类结果为GeoJSON
python3 $MAPS supplier-clusters --file suppliers.csv --k 4 --output clusters.json
```

返回：每个簇的中心坐标、成员列表、簇半径(km)、簇内平均间距。生成GeoJSON含颜色标记的供应商点，可在 geojson.io 查看。

### delivery-heatmap — 交货距离热力图

以目的地为中心，计算各供应商到目的地的距离，生成距离分级表和SVG热力图。

```bash
# 单一目的港
python3 $MAPS delivery-heatmap \
  --suppliers '[{"name":"A厂","lat":22.5,"lon":113.9},{"name":"B厂","lat":23.1,"lon":113.3}]' \
  --dest "广州" \
  --output heatmap.json

# 从CSV读取供应商
python3 $MAPS delivery-heatmap --file suppliers.csv --dest "上海" --mode driving

# 生成SVG热力图（ASCII热力图+距离分级表）
python3 $MAPS delivery-heatmap --file suppliers.csv --dest "成都" --format svg
```

返回：距离分级（<100km绿/100-300km黄/>300km红）、各供应商距离排序表、SVG热力图文件路径。可选OSRM道路距离（--mode driving）或直线距离（默认）。

## Pitfalls

- Nominatim ToS: max 1 req/s (handled automatically by the script)
- **macOS machine-specific**: Nominatim blocks direct urllib calls from this host
  (connection reset). OSRM routing works fine. Use `--coords` / `--suppliers`
  with pre-geocoded lat/lon to bypass. Full diagnosis in `references/network-notes.md`.
- `nearby` requires lat/lon OR `--near "<address>"` — one of the two is needed
- OSRM routing coverage is best for Europe and North America
- Overpass API can be slow during peak hours; the script automatically
  falls back between mirrors (overpass-api.de → overpass.kumi.systems)
- `distance` and `directions` use `--to` flag for the destination (not positional)
- If a zip code alone gives ambiguous results globally, include country/state
- 1688供应商命令（supplier-geo / logistics-cost / delivery-heatmap）：
  需要Nominatim geocoding的操作在此机器上可能失败，
  用 `--coords` 传入预计算坐标可绕过 geocoding

## Verification

```bash
python3 ~/.hermes/skills/maps/scripts/maps_client.py search "Statue of Liberty"
# Should return lat ~40.689, lon ~-74.044

python3 ~/.hermes/skills/maps/scripts/maps_client.py nearby --near "Times Square" --category restaurant --limit 3
# Should return a list of restaurants within ~500m of Times Square
```
