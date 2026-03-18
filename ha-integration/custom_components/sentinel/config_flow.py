"""Config flow — UI setup wizard."""

from __future__ import annotations

import aiohttp
import voluptuous as vol
from homeassistant import config_entries

from .const import DEFAULT_PORT, DOMAIN


async def _validate(host: str, port: int) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://{host}:{port}/status",
            timeout=aiohttp.ClientTimeout(total=5),
        ) as resp:
            resp.raise_for_status()


class SentinelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await _validate(user_input["host"], user_input["port"])
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"Sentinel ({user_input['host']})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host"): str,
                vol.Required("port", default=DEFAULT_PORT): int,
            }),
            errors=errors,
        )
