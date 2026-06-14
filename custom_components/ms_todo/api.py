"""API-Wrapper für die Maton-Microsoft-To-Do-Schnittstelle.

Kapselt alle HTTP-Calls, damit der Coordinator und der Config-Flow
saubere, testbare Funktionen bekommen.
"""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import async_timeout

from .const import API_BASE

_LOGGER = logging.getLogger(__name__)


class MatonTodoApiError(Exception):
    """Wird geworfen, wenn die Maton-API einen Fehler zurückgibt."""


class MatonAuthError(MatonTodoApiError):
    """401/403 — Token ist ungültig oder abgelaufen."""


class MatonTodoApi:
    """Async-Wrapper für die Maton-Microsoft-To-Do-API."""

    def __init__(self, session: aiohttp.ClientSession, token: str) -> None:
        self._session = session
        self._token = token
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(
        self, method: str, path: str, **kwargs: Any
    ) -> dict[str, Any] | list[Any] | None:
        """Generischer Request-Wrapper mit Fehlerbehandlung."""
        url = f"{API_BASE}{path}"
        try:
            async with async_timeout.timeout(15):
                resp = await self._session.request(
                    method, url, headers=self._headers, **kwargs
                )
                if resp.status in (401, 403):
                    raise MatonAuthError(
                        f"Auth fehlgeschlagen ({resp.status}). "
                        "Token prüfen oder neuen in Maton erzeugen."
                    )
                if resp.status == 404:
                    return None
                if resp.status >= 400:
                    text = await resp.text()
                    raise MatonTodoApiError(
                        f"API-Fehler {resp.status}: {text[:200]}"
                    )
                if resp.status == 204:
                    return None
                return await resp.json()
        except MatonTodoApiError:
            raise
        except (aiohttp.ClientError, TimeoutError) as err:
            raise MatonTodoApiError(f"Netzwerk-Fehler: {err}") from err

    # ----- Profile -----

    async def get_profile(self) -> dict[str, Any]:
        """Hole Profil-Info (Name, Email) für Account-Anzeige."""
        result = await self._request("GET", "/me")
        if not isinstance(result, dict):
            return {}
        return result

    # ----- Listen -----

    async def get_lists(self) -> list[dict[str, Any]]:
        """Hole alle Todo-Listen des Users."""
        result = await self._request("GET", "/me/todo/lists")
        if not isinstance(result, dict):
            return []
        return result.get("value", [])

    # ----- Tasks -----

    async def get_tasks(
        self, list_id: str, show_completed: bool = True
    ) -> list[dict[str, Any]]:
        """Hole alle Tasks einer Liste.

        Microsoft Graph liefert completed-Tasks standardmäßig;
        show_completed=False filtert sie clientseitig raus.
        """
        result = await self._request(
            "GET", f"/me/todo/lists/{list_id}/tasks"
        )
        if not isinstance(result, dict):
            return []
        tasks = result.get("value", [])
        if not show_completed:
            tasks = [t for t in tasks if t.get("status") != "completed"]
        return tasks

    async def create_task(
        self,
        list_id: str,
        title: str,
        description: str | None = None,
        due_date: str | None = None,
        importance: str | None = None,
        categories: list[str] | None = None,
        recurrence: dict | None = None,
        reminder: str | None = None,
    ) -> dict[str, Any]:
        """Lege eine neue Aufgabe an."""
        body: dict[str, Any] = {"title": title}
        if description:
            body["body"] = {"content": description, "contentType": "text"}
        if due_date:
            body["dueDateTime"] = {
                "dateTime": due_date,
                "timeZone": "Europe/Berlin",
            }
        if importance:
            body["importance"] = importance
        if categories:
            body["categories"] = categories
        if recurrence:
            body["recurrence"] = recurrence
        if reminder:
            body["reminderDateTime"] = {
                "dateTime": reminder,
                "timeZone": "Europe/Berlin",
            }
        result = await self._request(
            "POST", f"/me/todo/lists/{list_id}/tasks", json=body
        )
        if not isinstance(result, dict):
            raise MatonTodoApiError("Leere Antwort beim Anlegen")
        return result

    async def update_task_status(
        self, list_id: str, task_id: str, completed: bool
    ) -> None:
        """Hake eine Aufgabe ab oder reaktiviere sie."""
        status = "completed" if completed else "notStarted"
        body: dict[str, Any] = {"status": status}
        await self._request(
            "PATCH", f"/me/todo/lists/{list_id}/tasks/{task_id}", json=body
        )

    async def update_task_title(
        self, list_id: str, task_id: str, title: str
    ) -> None:
        """Ändere den Titel einer Aufgabe."""
        await self._request(
            "PATCH",
            f"/me/todo/lists/{list_id}/tasks/{task_id}",
            json={"title": title},
        )

    async def update_task_description(
        self, list_id: str, task_id: str, description: str
    ) -> None:
        """Ändere die Notiz/Beschreibung einer Aufgabe."""
        body = {"body": {"content": description, "contentType": "text"}}
        await self._request(
            "PATCH",
            f"/me/todo/lists/{list_id}/tasks/{task_id}",
            json=body,
        )

    async def update_task_details(
        self,
        list_id: str,
        task_id: str,
        due_date: str | None = None,
        importance: str | None = None,
        categories: list[str] | None = None,
        recurrence: dict | None = None,
        reminder: str | None = None,
    ) -> None:
        """Aktualisiere erweiterte Felder einer Aufgabe."""
        body: dict[str, Any] = {}
        if due_date is not None:
            if due_date:
                body["dueDateTime"] = {
                    "dateTime": due_date,
                    "timeZone": "Europe/Berlin",
                }
            else:
                body["dueDateTime"] = {"dateTime": None, "timeZone": "UTC"}
        if importance is not None:
            body["importance"] = importance or "normal"
        if categories is not None:
            body["categories"] = categories
        if recurrence is not None:
            body["recurrence"] = recurrence
        if reminder is not None:
            if reminder:
                body["reminderDateTime"] = {
                    "dateTime": reminder,
                    "timeZone": "Europe/Berlin",
                }
            else:
                body["reminderDateTime"] = {"dateTime": None, "timeZone": "UTC"}
        if body:
            await self._request(
                "PATCH",
                f"/me/todo/lists/{list_id}/tasks/{task_id}",
                json=body,
            )

    async def delete_task(self, list_id: str, task_id: str) -> None:
        """Lösche eine Aufgabe unwiderruflich."""
        await self._request(
            "DELETE", f"/me/todo/lists/{list_id}/tasks/{task_id}"
        )

    # ----- Test im Config-Flow -----

    async def validate(self) -> bool:
        """Testet Token + Listen-Zugriff. Wirft MatonAuthError bei 401."""
        await self.get_lists()
        return True
