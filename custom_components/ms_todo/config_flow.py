"""Config-Flow — UI-Setup für die MS To Do Integration.

Schritt 1: Token eingeben + testen
Schritt 2: Liste auswählen
Schritt 3: Polling-Intervall + Completed-Option
"""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MatonAuthError, MatonTodoApi, MatonTodoApiError
from .const import (
    CONF_ACCOUNT_EMAIL,
    CONF_ACCOUNT_NAME,
    CONF_LIST_ID,
    CONF_LIST_NAME,
    CONF_SCAN_INTERVAL,
    CONF_SHOW_COMPLETED,
    CONF_TOKEN,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SHOW_COMPLETED,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


def _user_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_TOKEN): str,
        }
    )


def _list_schema(lists: list[dict[str, Any]]) -> vol.Schema:
    """Schema mit allen verfügbaren Listen als Multi-Select Checkboxen."""
    return vol.Schema(
        {
            vol.Required(CONF_LIST_ID): cv.multi_select(
                {lst["id"]: lst.get("displayName", lst["id"]) for lst in lists}
            ),
        }
    )


def _options_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
            ): vol.All(int, vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)),
            vol.Required(
                CONF_SHOW_COMPLETED, default=DEFAULT_SHOW_COMPLETED
            ): bool,
        }
    )


class MsTodoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Initialer Setup-Flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialisiere Flow-State."""
        self._token: str | None = None
        self._lists: list[dict[str, Any]] = []
        self._profile: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Schritt 1: Token entgegennehmen + testen."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._token = user_input[CONF_TOKEN]
            session = async_get_clientsession(self.hass)
            api = MatonTodoApi(session, self._token)
            try:
                self._lists = await api.get_lists()
                self._profile = await api.get_profile()
            except MatonAuthError:
                errors["base"] = "invalid_auth"
            except MatonTodoApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unerwarteter Fehler")
                errors["base"] = "unknown"
            else:
                if not self._lists:
                    errors["base"] = "no_lists"
                else:
                    return await self.async_step_list()

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(),
            errors=errors,
        )

    async def async_step_list(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Schritt 2: Liste(n) auswählen."""
        if user_input is not None:
            try:
                selected_ids = user_input[CONF_LIST_ID]
                # Multi-Select gibt Liste zurück, Single-Select einen String
                if isinstance(selected_ids, str):
                    selected_ids = [selected_ids]
                
                # Account-Info für Titel und data
                account_name = self._profile.get("displayName", "Microsoft")
                account_email = self._profile.get("userPrincipalName", "")

                # Erstelle einen ConfigEntry pro ausgewählter Liste
                for list_id in selected_ids:
                    list_name = next(
                        (l.get("displayName", l["id"]) for l in self._lists if l["id"] == list_id),
                        list_id,
                    )
                    await self.async_set_unique_id(f"{DOMAIN}_{list_id}")
                    self._abort_if_unique_id_configured()
                    self.hass.config_entries.async_add(
                        ConfigEntry(
                            version=1,
                            domain=DOMAIN,
                            title=f"{account_name}: {list_name}",
                            data={
                                CONF_TOKEN: self._token,
                                CONF_LIST_ID: list_id,
                                CONF_LIST_NAME: list_name,
                                CONF_ACCOUNT_NAME: account_name,
                                CONF_ACCOUNT_EMAIL: account_email,
                                CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                                CONF_SHOW_COMPLETED: DEFAULT_SHOW_COMPLETED,
                            },
                            options={
                                CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                                CONF_SHOW_COMPLETED: DEFAULT_SHOW_COMPLETED,
                            },
                            discovery_keys={},
                            minor_version=1,
                            source="user",
                            subentries_data={},
                            unique_id=f"{DOMAIN}_{list_id}",
                        )
                    )
                
                return self.async_abort(reason="entries_created")
            except Exception as err:
                _LOGGER.exception("Fehler in async_step_list: %s", err)
                return self.async_show_form(
                    step_id="list",
                    data_schema=_list_schema(self._lists),
                    errors={"base": str(err)},
                )

        return self.async_show_form(
            step_id="list",
            data_schema=_list_schema(self._lists),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> "MsTodoOptionsFlow":
        """Verknüpfe den Options-Flow mit diesem Entry."""
        return MsTodoOptionsFlow()


class MsTodoOptionsFlow(OptionsFlow):
    """Options-Flow — Intervall + Completed-Toggle anpassen."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Zeige Optionen-Form, speichere User-Eingaben."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Defaults: aktuelle Optionen, falls gesetzt
        current = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=current.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): vol.All(
                    int,
                    vol.Range(
                        min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL
                    ),
                ),
                vol.Required(
                    CONF_SHOW_COMPLETED,
                    default=current.get(
                        CONF_SHOW_COMPLETED, DEFAULT_SHOW_COMPLETED
                    ),
                ): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
