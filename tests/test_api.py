"""Tests for the Wiener Linien Monitor API helper."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.wiener_linien_monitor.api import async_fetch_departures


def _make_session(json_data: dict, raise_error: Exception | None = None) -> MagicMock:
    """Create a mock aiohttp session."""
    response = AsyncMock()
    response.json = AsyncMock(return_value=json_data)

    session = MagicMock(spec=aiohttp.ClientSession)
    if raise_error:
        session.get = AsyncMock(side_effect=raise_error)
    else:
        session.get = AsyncMock(return_value=response)

    return session


SAMPLE_API_RESPONSE = {
    "data": {
        "monitors": [
            {
                "locationStop": {"properties": {"title": "Karlsplatz"}},
                "lines": [
                    {
                        "name": "U1",
                        "towards": "Oberlaa",
                        "platform": "1",
                        "departures": {
                            "departure": [
                                {
                                    "departureTime": {
                                        "timePlanned": "2025-01-01T12:00:00.000+0100",
                                        "timeReal": "2025-01-01T12:01:00.000+0100",
                                        "countdown": 3,
                                    },
                                    "vehicle": {
                                        "barrierFree": True,
                                        "foldingRamp": False,
                                        "type": "U-Bahn",
                                    },
                                },
                                {
                                    "departureTime": {
                                        "timePlanned": "2025-01-01T12:05:00.000+0100",
                                        "timeReal": None,
                                        "countdown": 8,
                                    },
                                    "vehicle": {
                                        "barrierFree": True,
                                        "foldingRamp": True,
                                        "type": "U-Bahn",
                                    },
                                },
                            ]
                        },
                    },
                    {
                        "name": "U4",
                        "towards": "Hütteldorf",
                        "platform": "2",
                        "departures": {
                            "departure": [
                                {
                                    "departureTime": {
                                        "timePlanned": "2025-01-01T12:02:00.000+0100",
                                        "timeReal": "2025-01-01T12:02:30.000+0100",
                                        "countdown": 5,
                                    },
                                    "vehicle": {
                                        "barrierFree": False,
                                        "foldingRamp": False,
                                        "type": "U-Bahn",
                                    },
                                }
                            ]
                        },
                    },
                ],
            }
        ]
    },
    "message": {"serverTime": "2025-01-01T12:00:00.000+0100"},
}


@pytest.mark.asyncio
async def test_fetch_departures_success() -> None:
    """Test successful departure fetch and parsing."""
    session = _make_session(SAMPLE_API_RESPONSE)

    result = await async_fetch_departures(session, "4609")

    assert result["departures_count"] == 3
    assert result["stop_id"] == "4609"
    assert result["stop_name"] == "Karlsplatz"
    assert result["server_time"] == "2025-01-01T12:00:00.000+0100"
    assert "message" not in result

    # Should be sorted by countdown
    countdowns = [d["countdown"] for d in result["departures"]]
    assert countdowns == [3, 5, 8]


@pytest.mark.asyncio
async def test_fetch_departures_sorted_by_countdown() -> None:
    """Test that departures are sorted by countdown."""
    session = _make_session(SAMPLE_API_RESPONSE)

    result = await async_fetch_departures(session, "4609")

    departures = result["departures"]
    assert departures[0]["line"] == "U1"
    assert departures[0]["countdown"] == 3
    assert departures[1]["line"] == "U4"
    assert departures[1]["countdown"] == 5
    assert departures[2]["line"] == "U1"
    assert departures[2]["countdown"] == 8


@pytest.mark.asyncio
async def test_fetch_departures_parses_fields() -> None:
    """Test that all fields are parsed correctly."""
    session = _make_session(SAMPLE_API_RESPONSE)

    result = await async_fetch_departures(session, "4609")

    first = result["departures"][0]
    assert first["line"] == "U1"
    assert first["direction"] == "Oberlaa"
    assert first["platform"] == "1"
    assert first["time_planned"] == "2025-01-01T12:00:00.000+0100"
    assert first["time_real"] == "2025-01-01T12:01:00.000+0100"
    assert first["countdown"] == 3
    assert first["barrier_free"] is True
    assert first["folding_ramp"] is False
    assert first["type"] == "U-Bahn"


@pytest.mark.asyncio
async def test_fetch_departures_no_monitors() -> None:
    """Test response when no monitors are available."""
    data = {"data": {"monitors": []}}
    session = _make_session(data)

    result = await async_fetch_departures(session, "9999")

    assert result == {"message": "No data"}


@pytest.mark.asyncio
async def test_fetch_departures_no_data_key() -> None:
    """Test response when data key is missing."""
    session = _make_session({})

    result = await async_fetch_departures(session, "9999")

    assert result == {"message": "No data"}


@pytest.mark.asyncio
async def test_fetch_departures_client_error() -> None:
    """Test handling of aiohttp client errors."""
    session = _make_session({}, raise_error=aiohttp.ClientError("Connection failed"))

    result = await async_fetch_departures(session, "4609")

    assert result == {"message": "No data"}


@pytest.mark.asyncio
async def test_fetch_departures_timeout() -> None:
    """Test handling of timeout errors."""
    session = _make_session({}, raise_error=TimeoutError())

    result = await async_fetch_departures(session, "4609")

    assert result == {"message": "Timeout"}


@pytest.mark.asyncio
async def test_fetch_departures_empty_departures() -> None:
    """Test a monitor with no departures."""
    data = {
        "data": {
            "monitors": [
                {
                    "locationStop": {"properties": {"title": "Stephansplatz"}},
                    "lines": [
                        {
                            "name": "U3",
                            "towards": "Ottakring",
                            "platform": "1",
                            "departures": {"departure": []},
                        }
                    ],
                }
            ]
        },
        "message": {"serverTime": "2025-01-01T12:00:00.000+0100"},
    }
    session = _make_session(data)

    result = await async_fetch_departures(session, "1234")

    assert result["departures_count"] == 0
    assert result["departures"] == []
    assert result["stop_name"] == "Stephansplatz"
