# Testing

## Purpose
Documents the testing framework, patterns, conventions, and current coverage of the Wiener Linien Monitor integration.

## Responsibilities
- Documenting test tooling and configuration
- Describing test patterns and mocking approach
- Tracking coverage gaps

## Non-Responsibilities
- Code conventions outside tests (see [CONVENTIONS.md](CONVENTIONS.md))
- CI pipeline configuration (see [TECH-STACK.md](TECH-STACK.md))

## Overview

### Test Structure
```
tests/
  conftest.py                  # HA mock injection via sys.modules
  test_api.py                  # Unit tests for api.py
  test_oebb_api.py             # Unit tests for oebb_api.py
  test_oebb_api_integration.py # Integration tests (real OeBB API)
```

### Framework and Configuration
- `pytest` with `pytest-asyncio`
- `asyncio_mode = "auto"` in `pyproject.toml` -- async test functions run without explicit `@pytest.mark.asyncio` decorator
- Existing tests still include the decorator explicitly (redundant but harmless)

### HA Mock Strategy
- `conftest.py` stubs out the entire `homeassistant` package via `sys.modules` patching
- This allows `api.py` to be imported and tested without a running HA instance
- The mock injection happens at import time, before any test module loads

### Mocking Approach
- `unittest.mock.AsyncMock` for coroutine methods (`session.get`/`session.post`, `response.json`)
- `unittest.mock.MagicMock` for synchronous objects
- No third-party mock libraries
- A private factory function `_make_session()` in each test file creates mock `aiohttp.ClientSession` objects (not a pytest fixture, a plain helper)
- `test_api.py` mocks `session.get` (Wiener Linien uses GET)
- `test_oebb_api.py` mocks `session.post` (OeBB uses POST); supports sequential responses via a list of json_data dicts for multi-call tests (e.g., LocMatch followed by StationBoard)

### Test Naming
- Files: `test_<module>.py`
- Functions: `test_<what>_<condition>()` (e.g., `test_fetch_departures_timeout`, `test_fetch_departures_sorted_by_countdown`)
- All test functions have a docstring describing intent

### Test Pattern
- Flat arrange-act-assert structure
- No explicit AAA comment markers
- Each test: set up mock session, call function, assert on result dict

### Integration Tests
- `test_oebb_api_integration.py` hits the real OeBB API to verify response parsing against live data
- Marked with `@pytest.mark.integration` so they are excluded from CI
- The `integration` marker is registered in `pyproject.toml`

### Commands
- Run unit tests: `pytest tests/ -v -m "not integration"`
- Run integration tests: `pytest tests/ -v -m integration`
- Run all tests: `pytest tests/ -v`
- Run specific file: `pytest tests/test_api.py -v`

## Dependencies
- `pytest`, `pytest-asyncio`, `unittest.mock` (stdlib)
- `aiohttp`, `voluptuous` (for type compatibility in mocks)

## Design Decisions
- `api.py` was designed with zero HA imports specifically to enable testing without HA mocking complexity. Other modules require the `sys.modules` stub.
- `asyncio_mode = "auto"` chosen to reduce boilerplate in async tests.

## Known Risks
- Only `api.py` and `oebb_api.py` have unit tests. `coordinator.py`, `sensor.py`, `config_flow.py`, and `__init__.py` are untested.
- The `sys.modules` patching approach in `conftest.py` is fragile -- adding HA imports to `api.py` or `oebb_api.py` would break the existing test setup.
- No integration tests against the real Wiener Linien API (OeBB integration tests exist).
- Integration tests depend on OeBB API availability and may fail if the API is down or changes its response format.

## Extension Guidelines
- New test files follow the `test_<module>.py` naming pattern in the `tests/` directory.
- Test functions follow `test_<what>_<condition>()` naming with docstrings.
- Use `AsyncMock` for async methods, `MagicMock` for sync objects.
- If testing a module with HA imports, rely on the `conftest.py` `sys.modules` stub or extend it as needed.
- Keep the `api.py` test suite independent of HA -- do not add HA imports to `api.py`.
