"""DataUpdateCoordinator for Sentinel."""

from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class SentinelCoordinator(DataUpdateCoordinator):
    """Polls /status and provides send_command for all entities."""

    def __init__(self, hass: HomeAssistant, host: str, port: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.speed_setting: int = 75  # desired speed; updated by the speed number entity

    async def _async_update_data(self) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/status",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    resp.raise_for_status()
                    return await resp.json()
        except Exception as err:
            raise UpdateFailed(f"Cannot reach Sentinel at {self.base_url}: {err}") from err

    async def send_command(self, action: str, speed: int | None = None) -> None:
        payload: dict = {"action": action}
        if speed is not None:
            payload["speed"] = speed
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/command",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    resp.raise_for_status()
        except Exception as err:
            raise HomeAssistantError(f"Sentinel is unavailable: {err}") from err
