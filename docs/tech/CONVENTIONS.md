# Conventions

## Purpose
Documents the coding conventions, naming patterns, import ordering, error handling, and style rules followed by the Wiener Linien Monitor integration.

## Responsibilities
- Defining naming conventions for files, classes, functions, variables, and constants
- Documenting import ordering and style enforcement
- Describing error handling and logging patterns

## Non-Responsibilities
- Project structure and module boundaries (see [ARCHITECTURE.md](ARCHITECTURE.md))
- Technology choices (see [TECH-STACK.md](TECH-STACK.md))
- Test-specific patterns (see [TESTING.md](TESTING.md))

## Overview

### File Naming
- `snake_case.py` for all Python modules, matching HA convention
- Standard HA module names: `__init__.py`, `config_flow.py`, `coordinator.py`, `sensor.py`, `const.py`, `api.py`

### Class Naming
- `PascalCase` with HA-idiomatic suffixes
- Domain name spelled out in full, never abbreviated
- Examples: `WienerLinienDataUpdateCoordinator`, `WienerLinienMonitorConfigFlow`, `WienerLinienSensor`

### Function and Method Naming
- `async_` prefix on all async functions (HA convention)
- Setup functions: `async_setup`, `async_setup_entry`, `async_setup_platform`, `async_unload_entry`
- Private helpers: leading underscore (e.g., `_async_update_listener`)

### Variable and Constant Naming
- Variables: `snake_case` with type annotations where non-obvious
- Constants: `UPPER_SNAKE_CASE` in `const.py` exclusively
- Config keys prefixed `CONF_*`, defaults prefixed `DEFAULT_*`
- Boolean attributes follow HA's `_attr_*` class-variable pattern (no `is_` prefix)

### Logger Convention
- Module-level: `_LOGGER = logging.getLogger(__name__)` in every module
- Log messages use `%s` printf-style formatting (not f-strings) -- HA and Python logging convention

### Import Ordering (enforced by Ruff isort)
1. `from __future__ import annotations` (always first, present in every file)
2. Standard library (`import logging`, `from typing import Any`)
3. Third-party (`import aiohttp`, `import voluptuous`)
4. Home Assistant (`from homeassistant.*`)
5. Local relative (`from .api import ...`, `from .const import ...`)

### Style Enforcement
- Ruff with rule sets: `E` (pycodestyle), `W` (warnings), `F` (pyflakes), `I` (isort), `UP` (pyupgrade), `B` (flake8-bugbear), `SIM` (flake8-simplify)
- Line length: 88 characters
- Quote style: double quotes
- Indentation: 4 spaces

### Error Handling Pattern
- No custom exceptions in the codebase
- Errors signaled via sentinel dict with `"message"` key (e.g., `{"message": "Timeout"}`)
- Callers check `if "message" in result`
- Coordinator returns stale data on error (prevents sensor unavailability)
- Logging levels: `_LOGGER.error()` for `TimeoutError`/`ClientError`, `_LOGGER.warning()` for unexpected exceptions and empty responses

### Constants Centralization
- All magic values (URLs, timeouts, config keys, defaults, service names) live exclusively in `const.py`
- No string literals scattered across other modules

## Dependencies
- Ruff (linting and formatting enforcement)
- HA coding conventions (async naming, logger pattern, entity attribute pattern)

## Design Decisions
- `from __future__ import annotations` is a hard requirement in every file -- enables modern type syntax without runtime cost.
- Printf-style logging chosen over f-strings per Python logging best practice (deferred string formatting).
- Sentinel dict error pattern chosen over exceptions. Rationale not documented -- needs team input.

## Known Risks
- No pre-commit hooks or local enforcement beyond Ruff -- conventions are only checked in CI.

## Extension Guidelines
- New files must include `from __future__ import annotations` as the first import.
- New constants go in `const.py`, never inline.
- New classes follow the `WienerLinien*` naming pattern with appropriate HA suffix.
- All async functions must use the `async_` prefix.
- Error logging must use printf-style `%s` formatting, not f-strings.
