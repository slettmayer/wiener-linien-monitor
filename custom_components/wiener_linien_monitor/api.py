"""API helpers for the Wiener Linien Monitor integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import API_ENDPOINT, API_TIMEOUT

_LOGGER = logging.getLogger(__name__)


async def async_fetch_departures(
    session: aiohttp.ClientSession, stop_id: str
) -> dict[str, Any]:
    """Fetch and parse departure data for a stop from the Wiener Linien API.

    Returns a dict with departures_count, stop_id, stop_name, departures list,
    and server_time. Returns a dict with just 'message' on error.
    """
    try:
        url = f"{API_ENDPOINT}?stopId={stop_id}"
        async with asyncio.timeout(API_TIMEOUT):
            response = await session.get(url)
            data = await response.json()

        if not data.get("data", {}).get("monitors"):
            _LOGGER.warning("No monitor data for stop %s", stop_id)
            return {"message": "No data"}

        monitors = data["data"]["monitors"]
        departures: list[dict[str, Any]] = []
        stop_name = "Unknown"

        if monitors:
            stop_name = (
                monitors[0]
                .get("locationStop", {})
                .get("properties", {})
                .get("title", "Unknown")
            )

            for monitor in monitors:
                lines = monitor.get("lines", [])
                for line in lines:
                    line_departures = line.get("departures", {}).get(
                        "departure", []
                    )
                    for departure in line_departures:
                        dep_time = departure.get("departureTime", {})
                        vehicle = departure.get("vehicle", {})

                        departures.append(
                            {
                                "line": line.get("name"),
                                "direction": line.get("towards"),
                                "platform": line.get("platform"),
                                "time_planned": dep_time.get("timePlanned"),
                                "time_real": dep_time.get("timeReal"),
                                "countdown": dep_time.get("countdown"),
                                "barrier_free": vehicle.get(
                                    "barrierFree", False
                                ),
                                "folding_ramp": vehicle.get(
                                    "foldingRamp", False
                                ),
                                "type": vehicle.get("type"),
                            }
                        )

        departures.sort(key=lambda x: x.get("countdown", 999))

        return {
            "departures_count": len(departures),
            "stop_id": stop_id,
            "stop_name": stop_name,
            "departures": departures,
            "server_time": data.get("message", {}).get("serverTime"),
        }

    except asyncio.TimeoutError:
        _LOGGER.error("Timeout fetching data for stop %s", stop_id)
        return {"message": "Timeout"}
    except aiohttp.ClientError as err:
        _LOGGER.error("Error fetching data for stop %s: %s", stop_id, err)
        return {"message": "No data"}
    except Exception as err:
        _LOGGER.warning("Unexpected error for stop %s: %s", stop_id, err)
        return {"message": "No data"}
