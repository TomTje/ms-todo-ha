"""To-Do-Entity — bringt die Liste in HA's native To-Do-UI.

HA 2024.12+ hat eine eigene `todo`-Platform. Unsere Entity liefert
Items + Status und reagiert auf Add/Update/Delete-Service-Calls.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
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

from .const import CONF_ACCOUNT_EMAIL, CONF_ACCOUNT_NAME, CONF_LIST_ID, CONF_LIST_NAME, DOMAIN, _CLEAR_DATE
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
        | TodoListEntityFeature.SET_DUE_DATE_ON_ITEM
        | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
    )
    _attr_extra_state_attributes = {}

    def __init__(
        self, coordinator: MsTodoCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialisiere Entity mit Coordinator-Daten."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_todo"
        self._entry = entry
        self._list_name = entry.data[CONF_LIST_NAME]
        self._list_id = entry.data[CONF_LIST_ID]
        # Account-Info als Extra-State-Attribute für Developer-Tools-Sichtbarkeit
        self._attr_extra_state_attributes = {
            "account_name": entry.data.get(CONF_ACCOUNT_NAME, ""),
            "account_email": entry.data.get(CONF_ACCOUNT_EMAIL, ""),
        }

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
            # Notes/Beschreibung aus body.content lesen
            body = task.get("body", {})
            description = body.get("content", "") if isinstance(body, dict) else ""

            # Fälligkeitsdatum parsen
            due: datetime | None = None
            due_raw = task.get("dueDateTime")
            if due_raw and isinstance(due_raw, dict):
                dt_str = due_raw.get("dateTime")
                if dt_str:
                    try:
                        due = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                    except ValueError:
                        pass

            items.append(
                TodoItem(
                    uid=task["id"],
                    summary=task.get("title", ""),
                    status=(
                        TodoItemStatus.COMPLETED
                        if task.get("status") == "completed"
                        else TodoItemStatus.NEEDS_ACTION
                    ),
                    description=description,
                    due=due,
                )
            )
        return items

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Wird von der UI aufgerufen, wenn der User was hinzufügt."""
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        due_str: str | None = None
        if item.due:
            due_str = item.due.isoformat()
        await api.create_task(
            self._list_id,
            item.summary,
            item.description,
            due_date=due_str,
        )
        await self.coordinator.async_request_refresh()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Toggle Status oder Titel/Description-Update."""
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
        # Falls Description geändert, separat patchen
        existing_body = existing.get("body", {}) if existing else {}
        existing_desc = existing_body.get("content", "") if isinstance(existing_body, dict) else ""
        # HA sendet "" wenn Feld geleert, None wenn unchanged → compare directly
        if item.description != existing_desc:
            await api.update_task_description(self._list_id, item.uid, item.description or "")
        # Falls dueDate geändert, separat patchen
        existing_due = existing.get("dueDateTime", {}) if existing else {}
        existing_due_str = existing_due.get("dateTime") if isinstance(existing_due, dict) else None
        new_due_val: datetime | None = item.due
        if new_due_val is not None:
            new_due_str = new_due_val.isoformat()
        else:
            new_due_str = _CLEAR_DATE  # sentinel: löschen
        if existing_due_str != new_due_str:
            await api.update_task_details(self._list_id, item.uid, due_date=new_due_str)
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
