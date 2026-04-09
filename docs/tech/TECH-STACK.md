# Tech Stack

## Purpose
Documents the languages, frameworks, build tools, testing infrastructure, and external dependencies used by the Wiener Linien Monitor integration.

## Responsibilities
- Enumerating all runtime and development dependencies
- Documenting build, lint, and test tooling
- Describing CI/CD pipeline structure

## Non-Responsibilities
- Architectural patterns and data flow (see [ARCHITECTURE.md](ARCHITECTURE.md))
- Coding style rules and naming conventions (see [CONVENTIONS.md](CONVENTIONS.md))
- Test patterns and coverage details (see [TESTING.md](TESTING.md))

## Overview

### Language
- Python 3.12+ (minimum required)
- `from __future__ import annotations` in every source file
- Type annotations used consistently on function signatures and non-trivial locals

### Framework
- Home Assistant custom integration framework (`custom_components` convention)
- Key HA abstractions used: `DataUpdateCoordinator`, `CoordinatorEntity`, `SensorEntity`, `ConfigFlow`, `OptionsFlow`, `async_get_clientsession`
- All I/O is fully async via `asyncio` and HA's shared `aiohttp` session
- `iot_class: cloud_polling` -- polls a remote API, no local device communication

### Key Libraries
- `aiohttp` -- async HTTP client (used in `api.py`, session provided by HA)
- `voluptuous` -- schema validation for config flows and service input
- `homeassistant` -- HA core APIs (coordinator, entity, config flow, services)

### Build and Dev Tools
- `uv` -- Python package/environment manager (local dev)
- `ruff` -- linter and formatter (configured in `pyproject.toml`)
- `pytest` + `pytest-asyncio` -- test runner with `asyncio_mode = "auto"`

### CI/CD
- GitHub Actions with three workflows:
  - `validate.yml` -- runs on push to `main` and PRs: Ruff lint+format, Hassfest, HACS validation, pytest. A `gate` job aggregates results.
  - `release.yml` -- triggered after validate succeeds on `main`: reads version from `manifest.json`, extracts `CHANGELOG.md` section, creates GitHub Release.
  - `dependabot-version-bump.yml` -- auto-bumps patch version in `manifest.json` and prepends `CHANGELOG.md` entry for Dependabot PRs.
- Dependabot configured for weekly GitHub Actions dependency updates.

### External APIs
- Wiener Linien OGD Realtime API (`https://www.wienerlinien.at/ogd_realtime/monitor`) -- sole external dependency, read-only, public, no auth required.
- A second endpoint (`trafficInfoList`) is defined in `const.py` but not currently used.

### Distribution
- HACS (Home Assistant Community Store) -- configured via `hacs.json`
- No Docker, Kubernetes, or other infrastructure tooling

## Dependencies
- Runtime: `homeassistant`, `aiohttp`, `voluptuous` (all provided by the HA environment)
- Dev: `ruff`, `pytest`, `pytest-asyncio`, `uv`
- External: Wiener Linien OGD Realtime API

## Design Decisions
- `manifest.json` is the single source of truth for versioning (CI reads it exclusively). `pyproject.toml` version exists but is not authoritative.
- Ruff replaces separate linter/formatter/isort tools with a single unified tool.
- `uv` chosen over pip/pipenv/poetry for local environment management.

## Known Risks
- Version in `pyproject.toml` is out of sync with `manifest.json` -- could cause confusion if `pyproject.toml` version is ever referenced.
- `trafficInfoList` endpoint constant is defined but unused -- dead code.

## Extension Guidelines
- Add new Python dependencies to `manifest.json` under `requirements` (HA convention), not `pyproject.toml`.
- New CI jobs should be added to `validate.yml` and included in the `gate` job's dependency list.
- Ruff rule sets can be extended in `pyproject.toml` under `[tool.ruff.lint]`.
