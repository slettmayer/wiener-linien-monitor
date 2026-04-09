# Wiener Linien Monitor
> Home Assistant custom integration for real-time Vienna public transport departures via the Wiener Linien OGD Realtime API.

## Quick Reference
- **Lint**: `ruff check .`
- **Format**: `ruff format .`
- **Test**: `pytest tests/ -v`
- **Validate (CI)**: Ruff + Hassfest + HACS + pytest (all must pass via `gate` job)

## Architecture Overview
Standard HA coordinator pattern with isolated API layer. All code lives in `custom_components/wiener_linien_monitor/`.

- `api.py` -- pure async HTTP client (no HA imports, independently testable)
- `coordinator.py` -- `DataUpdateCoordinator` subclass, one per stop, polls every 60s
- `sensor.py` -- `CoordinatorEntity` + `SensorEntity`, supports YAML and config entry setup
- `__init__.py` -- entry lifecycle, service registration (`fetch_departures`)
- `config_flow.py` -- `ConfigFlow` + `OptionsFlow` for UI-driven setup
- `const.py` -- all constants (URLs, keys, defaults)

Data flow: config -> coordinator -> `api.async_fetch_departures()` -> Wiener Linien API -> normalized departures -> sensor entity attributes.

## Tech Stack
- Python 3.12+, `from __future__ import annotations` in every file
- Home Assistant custom integration framework (`DataUpdateCoordinator`, `ConfigFlow`)
- `aiohttp` for async HTTP, `voluptuous` for schema validation
- `ruff` for linting/formatting, `pytest` + `pytest-asyncio` for testing
- `uv` for local environment management
- GitHub Actions CI (validate + auto-release from `manifest.json` version)

## Core Conventions
- All async functions use `async_` prefix (HA convention)
- Constants in `const.py` only -- no inline magic values
- Logger: `_LOGGER = logging.getLogger(__name__)` with `%s` formatting (not f-strings)
- Import order: `__future__` -> stdlib -> third-party -> HA -> local relative
- Classes: `WienerLinien*` prefix with HA suffix (e.g., `WienerLinienDataUpdateCoordinator`)
- Errors signaled via sentinel dict with `"message"` key, not exceptions
- Coordinator returns stale data on API error (prevents sensor unavailability)
- See [CONVENTIONS.md](docs/tech/CONVENTIONS.md) for full detail

## Business Domain
Vienna public transport departure monitoring. Each configured RBL stop ID becomes a sensor entity showing departure count and details. The Wiener Linien OGD Realtime API is the sole external dependency (public, no auth). See [Domain Overview](docs/domain/OVERVIEW.md) for concepts and terminology.

## Structural Risks
- Test coverage only exists for `api.py` -- coordinator, sensor, config flow are untested
- Version in `pyproject.toml` out of sync with `manifest.json` (CI uses manifest only)
- Sentinel dict error pattern is fragile -- callers must check `if "message" in result`
- YAML and config entry setup paths duplicate coordinator creation logic
- `trafficInfoList` endpoint constant defined but unused

## Detailed Guides
- [Technical Context](docs/tech/README.md) -- architecture, tech stack, conventions, testing
- [Domain Context](docs/domain/README.md) -- business domain, entities, terminology, integrations
- [Documentation Contributing Guide](docs/README.md) -- how to maintain these docs
