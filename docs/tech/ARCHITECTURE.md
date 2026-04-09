# Architecture

## Purpose
Documents the project structure, module boundaries, data flow, and architectural patterns of the Wiener Linien Monitor integration.

## Responsibilities
- Defining module boundaries and ownership
- Describing data flow between layers
- Documenting the HA integration lifecycle (setup, polling, teardown)

## Non-Responsibilities
- Technology choices and tooling (see [TECH-STACK.md](TECH-STACK.md))
- Code style and naming rules (see [CONVENTIONS.md](CONVENTIONS.md))
- Domain concepts and terminology (see [Domain Overview](../domain/OVERVIEW.md))

## Overview

### Project Structure
```
custom_components/wiener_linien_monitor/
  __init__.py       # Entry point: setup, teardown, service registration
  api.py            # Pure async API client (no HA imports)
  coordinator.py    # DataUpdateCoordinator subclass (polling, error recovery)
  sensor.py         # SensorEntity platform (YAML + config entry setup)
  config_flow.py    # ConfigFlow + OptionsFlow (UI-driven setup)
  const.py          # All constants (URLs, keys, defaults)
  manifest.json     # HA/HACS metadata, version source-of-truth
  strings.json      # UI strings (English, canonical)
  services.yaml     # Service schema for HA UI
  translations/     # en.json, de.json
tests/
  conftest.py       # HA mock injection via sys.modules
  test_api.py       # Unit tests for api.py
```

### Architectural Pattern
Standard HA coordinator pattern with a clean API isolation layer:

```
api.py  <--  coordinator.py  <--  sensor.py
  ^               ^                    ^
  |               |                    |
  pure async      HA polling           HA entity
  no HA deps      orchestration        representation
```

### Module Boundaries

**`api.py`** -- Owns all HTTP communication with the Wiener Linien API.
- Input: `aiohttp.ClientSession`, `stop_id` (string)
- Output: normalized departure dict or error dict with `"message"` key
- Zero HA imports. Independently testable.

**`coordinator.py`** -- Owns polling lifecycle for a single stop.
- Wraps `api.py` in a `DataUpdateCoordinator`
- Polls every 60 seconds (configurable via `const.SCAN_INTERVAL`)
- On API error with existing data: returns stale data (prevents sensor unavailability)
- One coordinator instance per configured stop ID

**`sensor.py`** -- Owns translation of coordinator data into HA sensor entities.
- Subclasses `CoordinatorEntity` and `SensorEntity`
- State: departure count. Attributes: stop name, departures list (capped at `max_departures`), server time.
- Supports dual setup: YAML (`async_setup_platform`) and config entry (`async_setup_entry`)

**`__init__.py`** -- Owns entry lifecycle and service registration.
- Creates one coordinator per stop on `async_setup_entry`
- Registers `wiener_linien_monitor.fetch_departures` service (calls API directly, bypasses coordinator)
- Stores coordinators in `hass.data[DOMAIN][entry.entry_id]`

**`config_flow.py`** -- Owns UI setup and options editing.
- `ConfigFlow`: initial setup (name + comma-separated stop IDs)
- `OptionsFlow`: post-setup editing (stops + max_departures)
- Options take precedence over data via `.options.get(key, .data.get(key))`

**`const.py`** -- Pure data module. All magic values live here exclusively.

### Data Flow

1. User configures stop IDs (YAML or config flow)
2. `__init__.py` creates one `WienerLinienDataUpdateCoordinator` per stop
3. Coordinator polls `api.async_fetch_departures(session, stop_id)` every 60s
4. `api.py` sends GET to `https://www.wienerlinien.at/ogd_realtime/monitor?stopId=<id>`
5. API response is normalized: monitors and lines flattened into a sorted departure list
6. Coordinator caches the result; sensor reads from `coordinator.data`
7. Sensor exposes departure count as state, truncated list as attributes

The on-demand service (`fetch_departures`) bypasses steps 2-3 and calls `api.py` directly, returning data as a service response without updating sensor state.

### Dual Setup Support
Both YAML and config entry setup paths are supported for backwards compatibility:
- YAML: `async_setup_platform` in `sensor.py` creates coordinators and sensors directly
- Config entry: `async_setup_entry` in `__init__.py` creates coordinators, then `async_setup_entry` in `sensor.py` creates sensors from stored coordinators

## Dependencies
- Internal: `const.py` is imported by all other modules. `api.py` is imported by `coordinator.py` and `__init__.py`. `coordinator.py` is imported by `sensor.py` and `__init__.py`.
- External: `homeassistant` core, `aiohttp`, `voluptuous`

## Design Decisions
- API layer has zero HA imports -- enables unit testing without a running HA instance or complex mocking. Rationale: explicit isolation for testability.
- One coordinator per stop (not one coordinator for all stops) -- enables independent polling and error recovery per stop. Rationale: a single stop's API failure should not affect other stops.
- Error signaling via sentinel dicts (`{"message": "..."}`) instead of exceptions. Rationale not documented -- needs team input.
- Stale data fallback on error -- coordinator returns previous good data rather than raising. Rationale: prevents sensor unavailability on transient API errors.

## Known Risks
- Sentinel dict error pattern is fragile: callers must remember to check `if "message" in result`. An exception-based approach would be more Pythonic and harder to miss.
- YAML setup path duplicates coordinator creation logic that also exists in `__init__.py`. If one path is updated, the other may be forgotten.
- No rate limiting or backoff on API errors -- repeated failures still poll every 60s.

## Extension Guidelines
- New modules should follow the existing layering: pure logic with no HA deps where possible, HA integration in a separate module.
- New entity platforms (e.g., binary_sensor) should follow the same `CoordinatorEntity` pattern as `sensor.py`.
- New services should be registered in `__init__.py` alongside the existing `fetch_departures` service.
- New config options should be added to both `ConfigFlow` and `OptionsFlow` in `config_flow.py`, with defaults in `const.py`.
