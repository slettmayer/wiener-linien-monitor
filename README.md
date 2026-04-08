# Wiener Linien Monitor

Home Assistant custom integration to fetch real-time departure data from the [Wiener Linien OGD Realtime API](https://www.wienerlinien.at/ogd_realtime).

Can be used standalone or together with [vienna-transport-card](https://github.com/0Paul89/vienna-transport-card).

## Installation

In HACS UI: **Integrations** -> three-dot menu -> **Custom repositories** -> paste this repo URL -> select type **Integration** -> **Add**

Then search for **"Wiener Linien Monitor"** in HACS and install.

## Setup

Add an entry to your `configuration.yaml`. You can find stop IDs using this tool: https://till.mabe.at/rbl/

```yaml
sensor:
  - platform: wl_monitor
    name: "WL Monitor"
    stops:
      - "1442"
      - "4609"
```

Each stop ID creates a sensor entity (`sensor.wl_monitor_<stop_id>`) with:
- **State:** number of upcoming departures
- **Attributes:** stop name, next 5 departures (line, direction, countdown, planned/real time, accessibility info), server time

## Service

### `wiener_linien_monitor.fetch_departures`

Fetches all departures for a given stop ID on demand (returns data directly, does not update sensors).

| Field     | Required | Description                                          |
|-----------|----------|------------------------------------------------------|
| `stop_id` | Yes      | Stop ID from https://till.mabe.at/rbl/               |

Example automation:
```yaml
service: wiener_linien_monitor.fetch_departures
data:
  stop_id: "4609"
response_variable: departures
```

The response includes `departures_count`, `stop_id`, `stop_name`, `departures` (list), and `server_time`.
