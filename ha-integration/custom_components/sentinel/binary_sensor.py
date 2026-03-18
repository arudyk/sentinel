"""Binary sensors: camera health, plugged in, charging."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SentinelCoordinator
from .entity import SentinelEntity


@dataclass(frozen=True)
class SentinelBinarySensorDescription(BinarySensorEntityDescription):
    data_key: str = ""


BINARY_SENSORS: tuple[SentinelBinarySensorDescription, ...] = (
    SentinelBinarySensorDescription(
        key="camera_ok",
        name="Camera",
        data_key="camera_ok",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:camera",
    ),
    SentinelBinarySensorDescription(
        key="battery_plugged",
        name="Plugged In",
        data_key="battery_plugged",
        device_class=BinarySensorDeviceClass.PLUG,
        icon="mdi:power-plug",
    ),
    SentinelBinarySensorDescription(
        key="battery_charging",
        name="Charging",
        data_key="battery_charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        icon="mdi:battery-charging",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SentinelCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [SentinelBinarySensor(coordinator, desc) for desc in BINARY_SENSORS]
    )


class SentinelBinarySensor(SentinelEntity, BinarySensorEntity):

    def __init__(
        self,
        coordinator: SentinelCoordinator,
        description: SentinelBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.host}_{coordinator.port}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self.entity_description.data_key)
