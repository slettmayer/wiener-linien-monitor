# Domain Overview

## Purpose
Documents the business domain, core concepts, terminology, and data flow of the Wiener Linien Monitor integration.

## Responsibilities
- Defining domain concepts and their relationships
- Documenting external API structure and data model
- Providing a glossary of domain-specific terminology

## Non-Responsibilities
- Technical architecture and module boundaries (see [Architecture](../tech/ARCHITECTURE.md))
- Coding conventions (see [Conventions](../tech/CONVENTIONS.md))

## Overview

### Domain Classification
Smart home / IoT integration for public transit. Bridges Vienna's public transport real-time departure API and the Austrian Federal Railways (OeBB) train data API into the Home Assistant platform as automatable sensor entities and on-demand services.

### Core Concepts

**Stop** -- A physical transit stop identified by a numeric RBL stop ID (e.g., "4609" for Karlsplatz). The primary unit of configuration and sensor creation. One coordinator and one sensor entity are created per stop.

**Departure** -- A single upcoming vehicle departure at a stop. Key fields:
- `line` -- route name (e.g., "U1", "13A")
- `towards` / `direction` -- terminal destination (e.g., "Oberlaa")
- `countdown` -- minutes until departure (sort key)
- `time_planned` -- ISO 8601 scheduled departure time
- `time_real` -- ISO 8601 real-time updated time (may be null)
- `barrier_free` -- vehicle accessibility (boolean)
- `folding_ramp` -- deployable wheelchair ramp (boolean)
- `type` -- vehicle type (e.g., "U-Bahn", "Straßenbahn")
- `platform` -- platform identifier at the stop

**Monitor** -- The API's grouping unit. A single stop response contains multiple monitors, each covering different lines or platforms. The integration flattens monitors and lines into a single sorted departure list per stop.

### Sensor Representation
Each configured stop becomes a `WienerLinienSensor` entity:
- Entity ID: `sensor.wl_monitor_<stop_id>` (YAML) or `sensor.<name>_<stop_id>` (config entry)
- State value: total count of upcoming departures
- Attributes: `stop_id`, `stop_name`, departures list (capped at `max_departures`, default 5), `server_time`

### On-Demand Services

**Wiener Linien:**
`wiener_linien_monitor.fetch_departures` fetches departures for any stop ID on demand. Returns data directly as a service response -- does not update sensor state. Intended for use in automations.

**OeBB (Austrian Federal Railways):**
Three on-demand services for OeBB train data. All return data as service responses (no sensor entities).

`wiener_linien_monitor.oebb_search_station` -- Search stations by name to discover station IDs. Returns station name, ID (`extId`), location identifier (`lid`), type, and coordinates.

`wiener_linien_monitor.oebb_station_board` -- Fetch departures or arrivals at a station. Accepts `station_id` or `station_name` (auto-resolved via LocMatch). Returns product name, direction, planned/real-time times, and platform.

`wiener_linien_monitor.oebb_trip_search` -- Search connections between two stations. Accepts `from_station_id`/`from_station_name` and `to_station_id`/`to_station_name`. Returns connections with departure/arrival times, duration, number of changes, and individual legs with product, stations, times, and platforms.

### Terminology Glossary

| Term | Definition |
|------|-----------|
| RBL | Rechnergestuetztes Betriebsleitsystem -- Wiener Linien's numeric stop identifier system |
| Stop ID | Numeric RBL identifier for a transit stop. Lookup tool: `https://till.mabe.at/rbl/` |
| Countdown | Minutes remaining until departure. Used as sort key |
| Barrier-free | Vehicle is accessible to passengers with mobility impairments |
| Folding ramp | Deployable ramp on the vehicle for wheelchair access |
| OGD | Open Government Data -- Austrian open-data initiative under which the API is published |
| Monitor | API-level grouping per stop, covering different lines/platforms |
| `towards` | API field name for terminal destination, exposed in HA as `direction` |
| `server_time` | Timestamp from the API indicating when data was generated server-side |
| `cloud_polling` | HA iot_class: integration fetches data by periodically calling a remote cloud API |
| OeBB | Oesterreichische Bundesbahnen -- Austrian Federal Railways |
| Scotty | OeBB's journey planning system, accessed via `fahrplan.oebb.at/bin/mgate.exe` |
| `extId` | OeBB's external station identifier (e.g., "1190100" for Wien Hbf) |
| `lid` | Location identifier string used internally by the OeBB API to reference stations |
| LocMatch | OeBB API method for searching stations/locations by name |
| StationBoard | OeBB API method for fetching departures/arrivals at a station |
| TripSearch | OeBB API method for planning connections between two stations |
| `prodL` / `prodX` | OeBB response pattern: products (train types) are in a shared list; journeys reference them by index |

### External Integrations

**Wiener Linien OGD Realtime API** -- Public, no authentication.
- Active endpoint: `https://www.wienerlinien.at/ogd_realtime/monitor?stopId=<id>`
- Unused endpoint: `https://www.wienerlinien.at/ogd_realtime/trafficInfoList` (defined in `const.py`, likely a stub for future traffic disruption features)

**OeBB Scotty API** -- Public, embedded authentication (AID token in request body).
- Single endpoint: `https://fahrplan.oebb.at/bin/mgate.exe` (POST with JSON body)
- Methods used: LocMatch (station search), StationBoard (departures/arrivals), TripSearch (connections)
- Response pattern: shared reference lists (`common.prodL`, `common.locL`) with index-based references from journey data
- Not officially documented -- reverse-engineered from the OeBB webapp

**vienna-transport-card** -- Companion HA frontend card (`https://github.com/0Paul89/vienna-transport-card`). Not a code dependency; a separate Lovelace card that can display data from this integration's sensors.

## Dependencies
- Wiener Linien OGD Realtime API (external, public)
- OeBB Scotty API (external, public with embedded auth)
- Home Assistant platform (runtime host)

## Design Decisions
- One sensor per stop (not per line or per departure) -- keeps the entity model simple and aligned with how users think about their transit stops.
- Departures capped at `max_departures` at the sensor level, not in the API layer -- the full data is available to the coordinator and on-demand service.
- `server_time` passed through unchanged from the API -- no timezone conversion or formatting applied.

## Known Risks
- The RBL stop ID system is Wiener Linien-specific. If the numbering scheme changes, all user configurations break.
- The `trafficInfoList` endpoint is defined but not integrated -- users may expect disruption/delay information that is not yet available.
- No data validation on API responses beyond checking for empty monitors. Malformed API responses could propagate unexpected data to sensor attributes.
- The OeBB Scotty API is reverse-engineered and undocumented -- response structures or auth tokens may change without notice.
- OeBB station name auto-resolution picks the first LocMatch result, which may be ambiguous for short queries (e.g., "Wien" matches many stations).

## Extension Guidelines
- New domain features (e.g., traffic disruptions, line filtering) should be documented here with their own concept definitions.
- New external integrations should be listed in the External Integrations section.
- Terminology additions should be added to the glossary table.
