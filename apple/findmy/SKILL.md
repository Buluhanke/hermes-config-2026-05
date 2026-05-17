---
name: findmy
description: "Track Apple devices/AirTags via FindMy.app on macOS."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [FindMy, AirTag, location, tracking, macOS, Apple]
---

# Find My (Apple)

Track Apple devices and AirTags via the FindMy.app on macOS. Since Apple doesn't
provide a CLI for FindMy, this skill uses AppleScript to open the app and
screen capture to read device locations.

## Table of Contents

1. [Core Tracking](#core-tracking)
2. [Procurement: Warehouse Asset Tracking](#procurement-warehouse-asset-tracking)
3. [Procurement: Logistics Tracking Integration](#procurement-logistics-tracking-integration)
4. [Procurement: Supplier Factory Verification](#procurement-supplier-factory-verification)
5. [Prerequisites](#prerequisites)
6. [Methods](#methods)
7. [Limitations](#limitations)
8. [Rules](#rules)

---

## Core Tracking

> *Standard Apple device/AirTag location tracking — the foundation for all procurement applications below.*

### When to Use

- User asks "where is my [device/cat/keys/bag]?"
- Tracking AirTag locations
- Checking device locations (iPhone, iPad, Mac, AirPods)
- Monitoring pet or item movement over time (AirTag patrol routes)

### Method 1: AppleScript + Screenshot (Basic)

```bash
# Open Find My app
osascript -e 'tell application "FindMy" to activate'
sleep 3

# Take a screenshot of the Find My window
screencapture -w -o /tmp/findmy.png
```

Analyze with vision:
```
vision_analyze(image_url="/tmp/findmy.png", question="What devices/items are shown and what are their locations?")
```

### Switch Between Tabs

```bash
# Switch to Devices tab
osascript -e '
tell application "System Events"
    tell process "FindMy"
        click button "Devices" of toolbar 1 of window 1
    end tell
end tell'

# Switch to Items tab (AirTags)
osascript -e '
tell application "System Events"
    tell process "FindMy"
        click button "Items" of toolbar 1 of window 1
    end tell
end tell'
```

### Method 2: Peekaboo UI Automation (Recommended)

```bash
# Open Find My
osascript -e 'tell application "FindMy" to activate'
sleep 3

# Capture and annotate the UI
peekaboo see --app "FindMy" --annotate --path /tmp/findmy-ui.png

# Click on a specific device/item by element ID
peekaboo click --on B3 --app "FindMy"

# Capture the detail view
peekaboo image --app "FindMy" --path /tmp/findmy-detail.png
```

### Workflow: Track AirTag Location Over Time

For monitoring an AirTag (e.g., tracking a cat's patrol route):

```bash
# 1. Open FindMy to Items tab
osascript -e 'tell application "FindMy" to activate'
sleep 3

# 2. Click on the AirTag item (stay on page — AirTag only updates when page is open)

# 3. Periodically capture location
while true; do
    screencapture -w -o /tmp/findmy-$(date +%H%M%S).png
    sleep 300  # Every 5 minutes
done
```

---

## Procurement: Warehouse Asset Tracking

> *Attach AirTags to high-value inventory pallets, equipment, and shipments to build a real-time warehouse asset tracking system.*

### Use Cases

- **Pallet-level tracking**: Attach AirTag to wooden pallets carrying expensive components
- **Equipment localization**: Find fork lifts, scanners, ladders within large warehouses in seconds
- **Seasonal inventory moves**: Track asset movement during warehouse reconfiguration
- **Loss prevention**: Alert when assets leave designated geofenced zones

### Workflow: One-Time Asset Registration

```bash
# 1. Create an asset manifest CSV
cat > /tmp/asset-registry.csv << 'EOF'
asset_id,description,airtag_name,zone,threshold_meters
PALLET-001,Server rack shipment,FindMy-A1B2C3D4,Zone-A,50
PALLET-002,Router batch lot-2026,FindMy-E5F6G7H8,Zone-B,30
EQUIP-003,Forklift CAT-YP-07,FindMy-I9J0K1L2,Loading-Dock,100
TOOL-004,Barcode scanner batch,FindMy-M3N4O5P6,Zone-C,20
EOF

# 2. Open FindMy Items tab and photograph each AirTag location
osascript -e 'tell application "FindMy" to activate'
sleep 2
# Navigate to Items tab
osascript -e '
tell application "System Events"
    tell process "FindMy"
        click button "Items" of toolbar 1 of window 1
    end tell
end tell'
sleep 3

# 3. Screenshot the Items list
screencapture -x /tmp/findmy-items-$(date +%Y%m%d).png
```

### Workflow: Rapid Asset Location (Real-Time Query)

```bash
# Open FindMy and wait for network update
osascript -e 'tell application "FindMy" to activate'
sleep 4

# Capture current Items view
screencapture -x /tmp/findmy-assets.png

# Analyze: ask vision to identify all visible AirTags and locations
# Then cross-reference with asset registry to flag anomalies
```

### Workflow: Warehouse Zone Validation

Verify assets are in their expected zones:

```bash
# For each expected location, click the AirTag in FindMy and read the address
peekaboo click --on <element_id> --app "FindMy"
sleep 3
peekaboo image --app "FindMy" --path /tmp/asset-detail.png

# Ask vision:
# "What is the precise address and any location name shown?"
```

### Procurement Tip: AirTag Placement for Warehouse Use

| Asset Type | Recommended Placement | Notes |
|---|---|---|
| Wooden pallets | Tucked between items, not visible | Hide from casual theft |
| Equipment | Bracket-mounted or zip-tied | Ensure battery access for replacement |
| Cartons/boxes | Inside top flap, taped shut | Retrieve when unpacking |
| Tools | Drill into tool body or handle cavity | Permanent mount for frequently-lost items |

---

## Procurement: Logistics Tracking Integration

> *Combine FindMy with logistics provider APIs to correlate physical movement with shipping status.*

### Use Cases

- **Multi-modal tracking**: Compare FindMy location with DHL/Alibaba logistics/顺丰 status
- **ETA cross-verification**: Confirm FindMy coordinates match declared destination
- **Route deviation alerts**: Detect when shipments deviate from expected routes
- **Proof of delivery**: Confirm physical arrival matches logistics milestone

### Workflow: Dual-Track Shipment Monitoring

```bash
# STEP 1: Get shipping carrier tracking number from procurement system
TRACKING_NUMBER="SF1234567890"  # Example: 顺丰
CARRIER="shunfeng"  # or "yto", "zto", "jd", "dhl", "ups"

# STEP 2: Fetch carrier API status (use procurement/logistics skill)
# See: logistics-tracking skill for carrier-specific API calls

# STEP 3: Capture FindMy physical location
osascript -e 'tell application "FindMy" to activate'
sleep 4
screencapture -x /tmp/findmy-shipment.png

# STEP 4: Cross-reference — ask vision:
# "What location is shown? Extract any address, city, or coordinates."
# Then compare against logistics API's declared current location
```

### Workflow: Geofence Breach Detection

```bash
# 1. Define expected route geofence (polygon coordinates)
# For a Shanghai→Shenzhen shipment, roughly:
EXPECTED_BOUNDS="lat:22.5-31.2,lon:113.8-121.5"

# 2. Capture FindMy location
osascript -e 'tell application "FindMy" to activate'
sleep 4
screencapture -x /tmp/shipment-gps.png

# 3. Ask vision to extract coordinates
# "What are the latitude and longitude coordinates shown?"
# Example response: "31.2304° N, 121.4737° E (Shanghai)"
```

### Logistics Integration Reference

| Carrier | Tracking URL Pattern | API Endpoint |
|---|---|---|
| 顺丰 (SF Express) | sf-express.com/track/sfw?lang=sc&trackingno={code} | open-api |
| 中通 (ZTO) | zto.com/track?ballcode={code} | open-api |
| 圆通 (YTO) | yto.net.cn/track?trackingNo={code} | open-api |
| 京东 (JD) | jd.com/track?vocode={code} | open-api |
| DHL | dhl.com/track?tracking-id={code} | dhl-api |
| UPS | ups.com/track?trackingnum={code} | ups-api |

> **Note**: Use the `logistics-tracking` skill for up-to-date carrier API integration.

---

## Procurement: Supplier Factory Verification

> *Use FindMy + Vision to verify a supplier's claimed factory location matches physical reality — a key anti-fraud control in procurement.*

### Use Cases

- **Factory location audit**: Confirm supplier's registered address matches their claimed production site
- **Multi-facility verification**: Verify which facilities a supplier actually operates
- **Drop-ship validation**: Confirm a dropshipper isn't pretending to be a manufacturer
- **Cross-border sourcing**: Verify overseas factory exists at claimed GPS coordinates

### Workflow: Supplier Factory Location Check

```bash
# STEP 1: Get supplier-declared address from procurement records
DECLARED_ADDRESS="广东省深圳市宝安区福永街道凤凰社区兴山路凤凰工业区"

# STEP 2: If supplier provided an AirTag for tracking production equipment:
# Ask supplier for their internal AirTag name (FindMy sharee name)
# Then track it via your own FindMy (shared via iCloud Family sharing or share invite)

# STEP 3: Open FindMy and locate the shared AirTag
osascript -e 'tell application "FindMy" to activate'
sleep 4

# Navigate to Items tab
osascript -e '
tell application "System Events"
    tell process "FindMy"
        click button "Items" of toolbar 1 of window 1
    end tell
end tell'
sleep 3

# Capture the shared item location
screencapture -x /tmp/supplier-factory.png

# STEP 4: Ask vision to extract location details
# "What address or location name is shown? What are the coordinates?"
# Compare against the declared address
```

### Workflow: Supplier On-Site Audit Assist

During an in-person factory audit:

```bash
# 1. Open FindMy on your iPhone or iPad
# 2. Put the supplier's AirTag into Lost Mode before entering facility
#    (This activates precise location broadcasting for 24 hours)
osascript -e '
tell application "FindMy"
    activate
end tell'
# Use FindMy UI to enable Lost Mode on the supplier's AirTag

# 3. Walk the facility with FindMy open — the AirTag will report
#    ultra-wideband precise location (if iPhone 11+ and within range)

# 4. Capture evidence photos as you locate equipment
screencapture -x /tmp/factory-audit-$(date +%Y%m%d-%H%M).png

# 5. Build audit map: each screenshot = GPS proof of equipment presence
```

### Workflow: Remote Factory Existence Check

For verifying factories without visiting:

```bash
# Pre-requisite: Supplier has shared an AirTag with you via iCloud
# Ask supplier: "Please share the AirTag attached to your main production
# equipment via iCloud. The share invite will go to your Apple ID."

# 1. Accept the iCloud share invite (check email/FindMy notifications)

# 2. Once shared, the AirTag appears in YOUR FindMy Items tab
osascript -e 'tell application "FindMy" to activate'
sleep 3

# 3. Click on the shared AirTag
osascript -e '
tell application "System Events"
    tell process "FindMy"
        click button "Items" of toolbar 1 of window 1
    end tell
end tell'
sleep 2

# 4. Capture location and address
screencapture -x /tmp/remote-factory.png

# 5. Vision analysis:
# "What facility name, address, or landmark is visible in this screenshot?
#  Are there any signs of industrial activity (warehouse rows, loading docks,
#  industrial equipment)?
```

### Anti-Fraud Red Flags

| Red Flag | What to Investigate |
|---|---|
| Address is residential, not industrial | Supplier may be a trading company, not manufacturer |
| Coordinates in wrong province | Supplier gave wrong address entirely |
| No FindMy sharing offered | Supplier hesitant to share real-time location |
| Location changes frequently | AirTag may be on a person/vehicle, not a fixed facility |
| Precise location mismatch | Supplier's declared address vs. actual GPS differs by >1km |

---

## Prerequisites

- **macOS** with Find My app and iCloud signed in
- Devices/AirTags already registered in Find My
- Screen Recording permission for terminal (System Settings → Privacy → Screen Recording)
- **Optional but recommended**: Install `peekaboo` for better UI automation:
  `brew install steipete/tap/peekaboo`

---

## Methods

### Method 1: AppleScript + Screenshot (Basic)

```bash
# Open Find My app
osascript -e 'tell application "FindMy" to activate'

# Wait for it to load
sleep 3

# Take a screenshot of the Find My window
screencapture -w -o /tmp/findmy.png
```

Then use `vision_analyze` to read the screenshot:
```
vision_analyze(image_url="/tmp/findmy.png", question="What devices/items are shown and what are their locations?")
```

### Switch Between Tabs

```bash
# Switch to Devices tab
osascript -e '
tell application "System Events"
    tell process "FindMy"
        click button "Devices" of toolbar 1 of window 1
    end tell
end tell'

# Switch to Items tab (AirTags)
osascript -e '
tell application "System Events"
    tell process "FindMy"
        click button "Items" of toolbar 1 of window 1
    end tell
end tell'
```

### Method 2: Peekaboo UI Automation (Recommended)

If `peekaboo` is installed, use it for more reliable UI interaction:

```bash
# Open Find My
osascript -e 'tell application "FindMy" to activate'
sleep 3

# Capture and annotate the UI
peekaboo see --app "FindMy" --annotate --path /tmp/findmy-ui.png

# Click on a specific device/item by element ID
peekaboo click --on B3 --app "FindMy"

# Capture the detail view
peekaboo image --app "FindMy" --path /tmp/findmy-detail.png
```

Then analyze with vision:
```
vision_analyze(image_url="/tmp/findmy-detail.png", question="What is the location shown for this device/item? Include address and coordinates if visible.")
```

### Workflow: Track AirTag Location Over Time

For monitoring an AirTag (e.g., tracking a cat's patrol route):

```bash
# 1. Open FindMy to Items tab
osascript -e 'tell application "FindMy" to activate'
sleep 3

# 2. Click on the AirTag item (stay on page — AirTag only updates when page is open)

# 3. Periodically capture location
while true; do
    screencapture -w -o /tmp/findmy-$(date +%H%M%S).png
    sleep 300  # Every 5 minutes
done
```

Analyze each screenshot with vision to extract coordinates, then compile a route.

---

## Limitations

- FindMy has **no CLI or API** — must use UI automation
- AirTags only update location while the FindMy page is actively displayed
- Location accuracy depends on nearby Apple devices in the FindMy network
- Screen Recording permission required for screenshots
- AppleScript UI automation may break across macOS versions
- Shared AirTags require supplier cooperation (iCloud sharing invite)
- Factory verification only works if AirTag is physically at the factory

---

## Rules

1. Keep FindMy app in the foreground when tracking AirTags (updates stop when minimized)
2. Use `vision_analyze` to read screenshot content — don't try to parse pixels
3. For ongoing tracking, use a cronjob to periodically capture and log locations
4. Respect privacy — only track devices/items the user owns
5. For supplier verification, always cross-reference FindMy with official business registration data
6. Lost Mode provides strongest location signal — use it during critical tracking moments
