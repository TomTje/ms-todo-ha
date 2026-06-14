"""MS To Do (Maton) — Setup, Plattformen."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MatonAuthError, MatonTodoApi, MatonTodoApiError
from .const import CONF_ACCOUNT_EMAIL, CONF_ACCOUNT_NAME, CONF_LIST_ID, CONF_LIST_NAME, DOMAIN
from .coordinator import MsTodoCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.TODO]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Richte eine einzelne Liste als Integration ein."""
    session = async_get_clientsession(hass)
    api = MatonTodoApi(session, entry.data[CONF_TOKEN])

    # Token beim Start einmal testen — schlägt das fehl, ConfigEntryNotReady
    # lässt HA es automatisch nochmal versuchen.
    try:
        await api.validate()
    except MatonAuthError as err:
        _LOGGER.error("Token ungültig: %s", err)
        raise ConfigEntryNotReady("Token ungültig — bitte neu konfigurieren") from err
    except MatonTodoApiError as err:
        raise ConfigEntryNotReady(str(err)) from err

    list_id = entry.data[CONF_LIST_ID]
    list_name = entry.data[CONF_LIST_NAME]

    coordinator = MsTodoCoordinator(hass, entry, api, list_id, list_name)
    await coordinator.async_config_entry_first_refresh()

    # Listener: wenn der User das Intervall in der UI ändert,
    # wird der Coordinator mit den neuen Werten neu geladen.
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Räume beim Entfernen der Integration auf."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_update_listener(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Lade die Integration neu, wenn der User Optionen geändert hat."""
    await hass.config_entries.async_reload(entry.entry_id)
