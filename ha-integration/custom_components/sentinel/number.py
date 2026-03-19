"""Speed control — number entity (0–100 %)."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .coordinator import SentinelCoordinator
from .entity import SentinelEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SentinelCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        SentinelSpeedNumber(coordinator),
        SentinelPanNumber(coordinator),
        SentinelTiltNumber(coordinator),
    ])


class SentinelSpeedNumber(SentinelEntity, RestoreEntity, NumberEntity):
    """Sets the speed used by drive buttons and patrol automations."""

    _attr_name = "Speed"
    _attr_icon = "mdi:speedometer"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 5
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER
    _attr_native_value = 75.0

    def __init__(self, coordinator: SentinelCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.host}_{coordinator.port}_speed_setting"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            try:
                self._attr_native_value = float(last.state)
            except (ValueError, TypeError):
                pass
        self.coordinator.speed_setting = int(self._attr_native_value)

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.coordinator.speed_setting = int(value)
        self.async_write_ha_state()


class SentinelPanNumber(SentinelEntity, NumberEntity):
    """Pan angle for the camera (0–180°)."""

    _attr_name = "Pan"
    _attr_icon = "mdi:pan-horizontal"
    _attr_native_min_value = 0
    _attr_native_max_value = 180
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "°"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SentinelCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.host}_{coordinator.port}_pan"
        self._attr_native_value = float(
            coordinator.data.get("pan", 90) if coordinator.data else 90
        )

    @property
    def native_value(self) -> float:
        if self.coordinator.data and "pan" in self.coordinator.data:
            return float(self.coordinator.data["pan"])
        return self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        await self.coordinator.set_pan_tilt(pan=int(value))
        self.async_write_ha_state()


class SentinelTiltNumber(SentinelEntity, NumberEntity):
    """Tilt angle for the camera (0–180°)."""

    _attr_name = "Tilt"
    _attr_icon = "mdi:pan-vertical"
    _attr_native_min_value = 0
    _attr_native_max_value = 180
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "°"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SentinelCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.host}_{coordinator.port}_tilt"
        self._attr_native_value = float(
            coordinator.data.get("tilt", 90) if coordinator.data else 90
        )

    @property
    def native_value(self) -> float:
        if self.coordinator.data and "tilt" in self.coordinator.data:
            return float(self.coordinator.data["tilt"])
        return self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        await self.coordinator.set_pan_tilt(tilt=int(value))
        self.async_write_ha_state()
