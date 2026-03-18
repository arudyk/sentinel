"""Drive command buttons."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SentinelCoordinator
from .entity import SentinelEntity


@dataclass(frozen=True)
class SentinelButtonDescription(ButtonEntityDescription):
    action: str = ""


BUTTONS: tuple[SentinelButtonDescription, ...] = (
    SentinelButtonDescription(key="forward",    name="Forward",    icon="mdi:arrow-up",    action="forward"),
    SentinelButtonDescription(key="reverse",    name="Reverse",    icon="mdi:arrow-down",  action="reverse"),
    SentinelButtonDescription(key="turn_left",  name="Turn Left",  icon="mdi:arrow-left",  action="turn_left"),
    SentinelButtonDescription(key="turn_right", name="Turn Right", icon="mdi:arrow-right", action="turn_right"),
    SentinelButtonDescription(key="stop",       name="Stop",       icon="mdi:stop",        action="stop"),
    SentinelButtonDescription(key="brake",      name="Brake",      icon="mdi:car-brake-hold", action="brake"),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SentinelCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SentinelButton(coordinator, desc) for desc in BUTTONS])


class SentinelButton(SentinelEntity, ButtonEntity):

    def __init__(
        self, coordinator: SentinelCoordinator, description: SentinelButtonDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.host}_{coordinator.port}_{description.key}"

    async def async_press(self) -> None:
        action = self.entity_description.action
        speed = None if action in ("stop", "brake") else self.coordinator.speed_setting
        await self.coordinator.send_command(action, speed)
