"""Mock homeassistant imports so api.py can be tested standalone."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

# Mock the homeassistant package so that importing the custom_components
# package doesn't fail in a test environment without HA installed.
# Only the api.py and const.py modules are actually exercised by these tests.
ha_mock = MagicMock()
sys.modules.setdefault("homeassistant", ha_mock)
sys.modules.setdefault("homeassistant.config_entries", ha_mock)
sys.modules.setdefault("homeassistant.core", ha_mock)
sys.modules.setdefault("homeassistant.const", ha_mock)
sys.modules.setdefault("homeassistant.components", ha_mock)
sys.modules.setdefault("homeassistant.components.sensor", ha_mock)
sys.modules.setdefault("homeassistant.helpers", ha_mock)
sys.modules.setdefault("homeassistant.helpers.aiohttp_client", ha_mock)
sys.modules.setdefault("homeassistant.helpers.config_validation", ha_mock)
sys.modules.setdefault("homeassistant.helpers.entity_platform", ha_mock)
sys.modules.setdefault("homeassistant.helpers.typing", ha_mock)
sys.modules.setdefault("homeassistant.helpers.update_coordinator", ha_mock)
sys.modules.setdefault("homeassistant.data_entry_flow", ha_mock)
sys.modules.setdefault("homeassistant.util", ha_mock)
