"""Sensors: battery %, battery voltage, speed, uptime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfElectricPotential, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SentinelCoordinator
from .entity import SentinelEntity


@dataclass(frozen=True)
class SentinelSensorDescription(SensorEntityDescription):
    data_key: str = ""


SENSORS: tuple[SentinelSensorDescription, ...] = (
    SentinelSensorDescription(
        key="battery_pct",
        name="Battery",
        data_key="battery_pct",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery",
    ),
    SentinelSensorDescription(
        key="battery_v",
        name="Battery Voltage",
        data_key="battery_v",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        icon="mdi:flash",
    ),
    SentinelSensorDescription(
        key="speed",
        name="Speed",
        data_key="speed",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:speedometer",
    ),
    SentinelSensorDescription(
        key="uptime_s",
        name="Uptime",
        data_key="uptime_s",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        icon="mdi:timer",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SentinelCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SentinelSensor(coordinator, desc) for desc in SENSORS])


class SentinelSensor(SentinelEntity, SensorEntity):

    def __init__(
        self, coordinator: SentinelCoordinator, description: SentinelSensorDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.host}_{coordinator.port}_{description.key}"

    @property
    def native_value(self) -> Any:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self.entity_description.data_key)
