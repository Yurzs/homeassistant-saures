import asyncio
import logging

from homeassistant import config_entries, core

from . import const

LOG = logging.getLogger(__name__)


async def options_updates_listener(hass: core.HomeAssistant, entry: config_entries.ConfigEntry):
    """Handles options update."""

    await hass.config_entries.async_reload(entry.entry_id)


async def unsub_options_update_listener(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Removes config entry."""

    unset_results = await asyncio.gather(
        *[hass.config_entries.async_forward_entry_unload(entry, "sensor")]
    )

    hass.data[const.DOMAIN][entry.entry_id]["unsub_options_update_listener"]()

    unset_result_status = all(unset_results)

    if unset_result_status:
        hass.data[const.DOMAIN].pop(entry.entry_id)

    return unset_result_status


async def async_setup_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Sets up integration entries from config."""

    hass_data = dict(entry.data)

    entry.add_update_listener(options_updates_listener)

    hass_data["unsub_options_update_listener"] = unsub_options_update_listener

    hass.data.setdefault(const.DOMAIN, {})[entry.entry_id] = hass_data

    hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, "sensor"))

    return True


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the SAURES component."""

    hass.data.setdefault(const.DOMAIN, {})

    return True
