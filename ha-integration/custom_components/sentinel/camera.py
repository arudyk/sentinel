"""Sentinel camera — grabs JPEG frames from the MJPEG stream."""

from __future__ import annotations

import aiohttp
from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SentinelCoordinator
from .entity import SentinelEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SentinelCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SentinelCamera(coordinator)])


class SentinelCamera(SentinelEntity, Camera):
    """Pulls one JPEG frame at a time from the MJPEG stream for HA's camera card."""

    _attr_name = "Camera"

    def __init__(self, coordinator: SentinelCoordinator) -> None:
        SentinelEntity.__init__(self, coordinator)
        Camera.__init__(self)
        self._attr_unique_id = f"{coordinator.host}_{coordinator.port}_camera"
        self._stream_url = f"{coordinator.base_url}/stream"

    @property
    def is_streaming(self) -> bool:
        return bool(self.coordinator.data and self.coordinator.data.get("camera_ok"))

    async def handle_async_mjpeg_stream(self, request):
        """Proxy the live MJPEG stream directly from Sentinel."""
        from aiohttp import web

        response = web.StreamResponse()
        response.content_type = "multipart/x-mixed-replace; boundary=frame"
        await response.prepare(request)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self._stream_url,
                    timeout=aiohttp.ClientTimeout(connect=5, total=None),
                ) as upstream:
                    async for chunk in upstream.content.iter_chunked(8192):
                        await response.write(chunk)
        except Exception:
            pass
        return response

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Extract one JPEG frame from the MJPEG stream (used for snapshots)."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self._stream_url, timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    buf = b""
                    async for chunk in resp.content.iter_chunked(4096):
                        buf += chunk
                        start = buf.find(b"\xff\xd8")
                        if start == -1:
                            continue
                        end = buf.find(b"\xff\xd9", start + 2)
                        if end != -1:
                            return buf[start : end + 2]
                        if len(buf) > 500_000:
                            break
        except Exception:
            return None
