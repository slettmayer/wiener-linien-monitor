"""Integration tests for the OeBB API (hits the real API).

Run with: pytest tests/ -v -m integration
"""

from __future__ import annotations

import aiohttp
import pytest

from custom_components.wiener_linien_monitor.oebb_api import (
    async_oebb_search_station,
    async_oebb_station_board,
    async_oebb_trip_search,
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_oebb_search_station() -> None:
    """Search for Wien Hauptbahnhof and verify results."""
    async with aiohttp.ClientSession() as session:
        result = await async_oebb_search_station(session, "Wien Hauptbahnhof")

    assert "message" not in result, f"API error: {result.get('message')}"
    assert result["results_count"] > 0
    assert any("Wien" in s["name"] for s in result["stations"])

    first = result["stations"][0]
    assert first["station_id"]
    assert first["name"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_oebb_station_board_by_name() -> None:
    """Fetch departures from Wien Hbf by name."""
    async with aiohttp.ClientSession() as session:
        result = await async_oebb_station_board(session, station_name="Wien Hbf")

    assert "message" not in result, f"API error: {result.get('message')}"
    assert result["board_type"] == "DEP"
    assert result["journeys_count"] > 0

    first = result["journeys"][0]
    assert first["product"]
    assert first["time_planned"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_oebb_station_board_by_id() -> None:
    """Fetch departures from Wien Hbf by station ID."""
    async with aiohttp.ClientSession() as session:
        result = await async_oebb_station_board(session, station_id="1190100")

    assert "message" not in result, f"API error: {result.get('message')}"
    assert result["journeys_count"] > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_oebb_trip_search() -> None:
    """Search connections from Wien Hbf to Salzburg Hbf."""
    async with aiohttp.ClientSession() as session:
        result = await async_oebb_trip_search(
            session,
            from_station_name="Wien Hbf",
            to_station_name="Salzburg Hbf",
        )

    assert "message" not in result, f"API error: {result.get('message')}"
    assert result["connections_count"] > 0

    first = result["connections"][0]
    assert first["departure"]
    assert first["arrival"]
    assert first["duration"]
    assert isinstance(first["changes"], int)
    assert len(first["legs"]) > 0

    leg = first["legs"][0]
    assert leg["product"]
    assert leg["from_station"]
    assert leg["to_station"]
