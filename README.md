# Wiener Linien Monitor

Home Assistant custom integration to fetch real-time departure data from the [Wiener Linien OGD Realtime API](https://www.wienerlinien.at/ogd_realtime) and train data from the [OeBB Scotty API](https://fahrplan.oebb.at).

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

## Services

### `wiener_linien_monitor.fetch_departures`

Fetches all departures for a given Wiener Linien stop ID on demand (returns data directly, does not update sensors).

| Field     | Required | Description                                          |
|-----------|----------|------------------------------------------------------|
| `stop_id` | Yes      | Stop ID from https://till.mabe.at/rbl/               |

Example:
```yaml
service: wiener_linien_monitor.fetch_departures
data:
  stop_id: "4609"
response_variable: departures
```

The response includes `departures_count`, `stop_id`, `stop_name`, `departures` (list), and `server_time`.

---

### `wiener_linien_monitor.oebb_search_station`

Search OeBB stations by name to find station IDs.

| Field         | Required | Description                              |
|---------------|----------|------------------------------------------|
| `query`       | Yes      | Station name or partial name             |
| `max_results` | No       | Max stations to return (default: 10)     |

Example:
```yaml
service: wiener_linien_monitor.oebb_search_station
data:
  query: "Wien Hauptbahnhof"
response_variable: stations
```

The response includes `results_count` and `stations` (list with `name`, `station_id`, `lid`, `type`, `latitude`, `longitude`).

---

### `wiener_linien_monitor.oebb_station_board`

Fetch departures or arrivals at an OeBB station. Provide either `station_id` or `station_name` (auto-resolved).

| Field          | Required | Description                                        |
|----------------|----------|----------------------------------------------------|
| `station_id`   | No*      | OeBB station ID (use `oebb_search_station` to find)|
| `station_name` | No*      | Station name (auto-resolved via search)            |
| `board_type`   | No       | `DEP` for departures, `ARR` for arrivals (default: `DEP`) |
| `max_journeys` | No       | Max journeys to return (default: 10)               |

\* At least one of `station_id` or `station_name` is required.

Example:
```yaml
service: wiener_linien_monitor.oebb_station_board
data:
  station_name: "Wien Hbf"
  board_type: "DEP"
  max_journeys: 5
response_variable: board
```

The response includes `station_name`, `station_id`, `board_type`, `journeys_count`, and `journeys` (list with `product`, `direction`, `time_planned`, `time_real`, `platform`).

---

### `wiener_linien_monitor.oebb_trip_search`

Search for train connections between two OeBB stations. Provide either ID or name for each station.

| Field               | Required | Description                              |
|---------------------|----------|------------------------------------------|
| `from_station_id`   | No*      | Departure station ID                     |
| `from_station_name` | No*      | Departure station name (auto-resolved)   |
| `to_station_id`     | No*      | Arrival station ID                       |
| `to_station_name`   | No*      | Arrival station name (auto-resolved)     |
| `max_connections`   | No       | Max connections to return (default: 5)   |

\* At least one of `from_station_id`/`from_station_name` and one of `to_station_id`/`to_station_name` required.

Example:
```yaml
service: wiener_linien_monitor.oebb_trip_search
data:
  from_station_name: "Wien Hbf"
  to_station_name: "Salzburg Hbf"
  max_connections: 3
response_variable: trips
```

The response includes `from_station`, `to_station`, `connections_count`, and `connections` (list with `departure`, `arrival`, `duration`, `changes`, `platform_departure`, `platform_arrival`, and `legs` with per-segment details).
