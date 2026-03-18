"""Base entity shared by all Sentinel platforms."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SentinelCoordinator


class SentinelEntity(CoordinatorEntity[SentinelCoordinator]):
    """Base class — groups all entities under a single device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SentinelCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.host}:{coordinator.port}")},
            name="Sentinel",
            manufacturer="DIY",
            model="Raspberry Pi Zero 2 W",
        )
