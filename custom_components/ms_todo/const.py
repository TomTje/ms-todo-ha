"""Konstanten für die MS To Do Integration."""
from typing import Final

DOMAIN: Final = "ms_todo"
MANUFACTURER: Final = "Microsoft"
MODEL: Final = "Microsoft To Do (via Maton)"

# Maton API Endpoint für Microsoft Graph To Do
# Maton proxied die offizielle Microsoft Graph API
API_BASE: Final = "https://api.maton.ai/microsoft-to-do/v1.0"

# Config-Flow Keys
CONF_TOKEN: Final = "token"
CONF_LIST_ID: Final = "list_id"
CONF_LIST_NAME: Final = "list_name"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_SHOW_COMPLETED: Final = "show_completed"

# Defaults
DEFAULT_SCAN_INTERVAL: Final = 300  # 5 Minuten
MIN_SCAN_INTERVAL: Final = 60       # 1 Minute
MAX_SCAN_INTERVAL: Final = 3600     # 1 Stunde
DEFAULT_SHOW_COMPLETED: Final = True

# Action Keys (für HA Todo-Entity Service-Calls)
ATTR_LIST_ID: Final = "list_id"
ATTR_TASK_ID: Final = "task_id"
ATTR_TITLE: Final = "title"
ATTR_DESCRIPTION: Final = "description"
ATTR_DUE_DATE: Final = "due_date"
