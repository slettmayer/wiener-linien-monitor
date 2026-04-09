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
Smart home / IoT integration for public transit. Bridges Vienna's public transport real-time departure API into the Home Assistant platform as automatable sensor entities.

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

### On-Demand Service
`wiener_linien_monitor.fetch_departures` fetches departures for any stop ID on demand. Returns data directly as a service response -- does not update sensor state. Intended for use in automations.

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

### External Integrations

**Wiener Linien OGD Realtime API** -- Sole external dependency. Public, no authentication.
- Active endpoint: `https://www.wienerlinien.at/ogd_realtime/monitor?stopId=<id>`
- Unused endpoint: `https://www.wienerlinien.at/ogd_realtime/trafficInfoList` (defined in `const.py`, likely a stub for future traffic disruption features)

**vienna-transport-card** -- Companion HA frontend card (`https://github.com/0Paul89/vienna-transport-card`). Not a code dependency; a separate Lovelace card that can display data from this integration's sensors.

## Dependencies
- Wiener Linien OGD Realtime API (external, public)
- Home Assistant platform (runtime host)

## Design Decisions
- One sensor per stop (not per line or per departure) -- keeps the entity model simple and aligned with how users think about their transit stops.
- Departures capped at `max_departures` at the sensor level, not in the API layer -- the full data is available to the coordinator and on-demand service.
- `server_time` passed through unchanged from the API -- no timezone conversion or formatting applied.

## Known Risks
- The RBL stop ID system is Wiener Linien-specific. If the numbering scheme changes, all user configurations break.
- The `trafficInfoList` endpoint is defined but not integrated -- users may expect disruption/delay information that is not yet available.
- No data validation on API responses beyond checking for empty monitors. Malformed API responses could propagate unexpected data to sensor attributes.

## Extension Guidelines
- New domain features (e.g., traffic disruptions, line filtering) should be documented here with their own concept definitions.
- New external integrations should be listed in the External Integrations section.
- Terminology additions should be added to the glossary table.
