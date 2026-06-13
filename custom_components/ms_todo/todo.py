"""To-Do-Entity — bringt die Liste in HA's native To-Do-UI.

HA 2024.12+ hat eine eigene `todo`-Platform. Unsere Entity liefert
Items + Status und reagiert auf Add/Update/Delete-Service-Calls.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_LIST_ID, CONF_LIST_NAME, DOMAIN
from .coordinator import MsTodoCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Erzeuge eine TodoEntity pro ConfigEntry (= pro Liste)."""
    coordinator: MsTodoCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([MsTodoListEntity(coordinator, entry)], True)


class MsTodoListEntity(
    CoordinatorEntity[MsTodoCoordinator], TodoListEntity
):
    """Repräsentiert eine einzelne MS-To-Do-Liste in HA."""

    _attr_has_entity_name = True
    _attr_translation_key = "todo"
    # Welche Aktionen unterstuetzt diese Entity? Ohne diese Deklaration
    # zeigt die HA-UI KEINE Buttons fuer Hinzufuegen/Abhaken/Loeschen.
    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
    )

    def __init__(
        self, coordinator: MsTodoCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialisiere Entity mit Coordinator-Daten."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_todo"
        self._entry = entry
        self._list_name = entry.data[CONF_LIST_NAME]
        self._list_id = entry.data[CONF_LIST_ID]

    @property
    def name(self) -> str:
        """Entity-Name: List-Name statt generisch 'todo'."""
        return self._list_name

    @property
    def available(self) -> bool:
        """Entity nur verfügbar, wenn Coordinator-Daten da sind."""
        return super().available and self.coordinator.data is not None

    @property
    def todo_items(self) -> list[TodoItem] | None:
        """Konvertiere API-Tasks in HA-TodoItem-Objekte."""
        if not self.coordinator.data:
            return None
        items: list[TodoItem] = []
        for task in self.coordinator.data:
            items.append(
                TodoItem(
                    uid=task["id"],
                    summary=task.get("title", ""),
                    status=(
                        TodoItemStatus.COMPLETED
                        if task.get("status") == "completed"
                        else TodoItemStatus.NEEDS_ACTION
                    ),
                )
            )
        return items

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Wird von der UI aufgerufen, wenn der User was hinzufügt."""
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        await api.create_task(
            self._list_id,
            item.summary,
            item.description,
        )
        await self.coordinator.async_request_refresh()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Toggle Status oder Titel-Update."""
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        # Erst Status toggle, falls geändert
        await api.update_task_status(
            self._list_id, item.uid, item.status == TodoItemStatus.COMPLETED
        )
        # Falls Titel geändert, separat patchen
        existing = next(
            (t for t in (self.coordinator.data or []) if t["id"] == item.uid),
            None,
        )
        if existing and existing.get("title") != item.summary:
            await api.update_task_title(self._list_id, item.uid, item.summary)
        await self.coordinator.async_request_refresh()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Lösche eine oder mehrere Aufgaben."""
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        for uid in uids:
            try:
                await api.delete_task(self._list_id, uid)
            except Exception:  # noqa: BLE001
                _LOGGER.warning("Konnte Task %s nicht löschen", uid)
        await self.coordinator.async_request_refresh()
