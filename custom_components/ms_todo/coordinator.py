"""DataUpdateCoordinator — pollt die To-Do-API und cached das Ergebnis.

Eine Instanz pro konfigurierter Liste. Hält die Tasks frisch und
signalisert Entities, wenn sich was ändert.
"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import MatonAuthError, MatonTodoApi, MatonTodoApiError
from .const import (
    CONF_LIST_ID,
    CONF_LIST_NAME,
    CONF_SCAN_INTERVAL,
    CONF_SHOW_COMPLETED,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SHOW_COMPLETED,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class MsTodoCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Pollt eine einzelne To-Do-Liste."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: MatonTodoApi,
        list_id: str,
        list_name: str,
    ) -> None:
        """Setze Scan-Intervall + Initial-State."""
        scan = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({list_name})",
            update_interval=timedelta(seconds=scan),
        )
        self.entry = entry
        self.api = api
        self.list_id = list_id
        self.list_name = list_name
        self.show_completed = entry.options.get(
            CONF_SHOW_COMPLETED,
            entry.data.get(CONF_SHOW_COMPLETED, DEFAULT_SHOW_COMPLETED),
        )

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Hole Tasks. Bei Auth-Fehler Config-Flow neu starten lassen."""
        try:
            return await self.api.get_tasks(self.list_id, self.show_completed)
        except MatonAuthError as err:
            # Wirft UpdateFailed, HA markiert Entity als unavailable
            # und der User kann in der UI neu konfigurieren.
            raise UpdateFailed(str(err)) from err
        except MatonTodoApiError as err:
            raise UpdateFailed(str(err)) from err
