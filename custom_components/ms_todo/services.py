"""Custom Services für MS To Do."""
from __future__ import annotations

import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_SET_IMPORTANCE = "set_importance"
SERVICE_SET_CATEGORIES = "set_categories"

SCHEMA_SET_IMPORTANCE = vol.Schema(
    {
        vol.Required("task_id"): str,
        vol.Required("importance"): vol.In(["high", "normal", "low"]),
    }
)

SCHEMA_SET_CATEGORIES = vol.Schema(
    {
        vol.Required("task_id"): str,
        vol.Required("categories"): vol.All([str], vol.Length(min=1)),
    }
)


async def async_register_services(hass: HomeAssistant) -> None:
    """Registriere die Custom Services."""

    async def set_importance(call: ServiceCall) -> None:
        """Setze die Wichtigkeit einer Aufgabe."""
        task_id: str = call.data["task_id"]
        importance: str = call.data["importance"]

        for entry_id in hass.data[DOMAIN]:
            entry: ConfigEntry = hass.data[DOMAIN][entry_id]["entry"]
            api = hass.data[DOMAIN][entry_id]["api"]
            coordinator = hass.data[DOMAIN][entry_id]["coordinator"]

            # Finde den Task in den Coordinator-Daten
            task = next(
                (t for t in (coordinator.data or []) if t["id"] == task_id),
                None,
            )
            if task:
                list_id = entry.data["list_id"]
                await api.update_task_details(
                    list_id, task_id, importance=importance
                )
                await coordinator.async_request_refresh()
                _LOGGER.debug(
                    "Set importance=%s for task %s", importance, task_id
                )
                return

        _LOGGER.warning("Task %s nicht gefunden", task_id)

    async def set_categories(call: ServiceCall) -> None:
        """Setze die Kategorien einer Aufgabe."""
        task_id: str = call.data["task_id"]
        categories: list[str] = call.data["categories"]

        for entry_id in hass.data[DOMAIN]:
            entry: ConfigEntry = hass.data[DOMAIN][entry_id]["entry"]
            api = hass.data[DOMAIN][entry_id]["api"]
            coordinator = hass.data[DOMAIN][entry_id]["coordinator"]

            task = next(
                (t for t in (coordinator.data or []) if t["id"] == task_id),
                None,
            )
            if task:
                list_id = entry.data["list_id"]
                await api.update_task_details(
                    list_id, task_id, categories=categories
                )
                await coordinator.async_request_refresh()
                _LOGGER.debug(
                    "Set categories=%s for task %s", categories, task_id
                )
                return

        _LOGGER.warning("Task %s nicht gefunden", task_id)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_IMPORTANCE,
        set_importance,
        SCHEMA_SET_IMPORTANCE,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_CATEGORIES,
        set_categories,
        SCHEMA_SET_CATEGORIES,
    )