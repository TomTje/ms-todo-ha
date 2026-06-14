# MS To Do (Maton) für Home Assistant

Bringt deine **Microsoft To Do**-Listen in Home Assistants native To-Do-UI.
Läuft über die [Maton API](https://maton.ai) — einem API-Aggregator, der die
offizielle Microsoft-Graph-API proxied.

## Features

- ✅ **Alle Listen** automatisch erkannt (dynamisch im Setup)
- ✅ **HA-eigene To-Do-UI** mit Checkboxen, Add-Button, Delete
- ✅ **Polling-Intervall einstellbar** (60–3600 Sekunden) — änderbar in den Optionen
- ✅ **Completed-Tasks toggle** (zeigen oder ausblenden)
- ✅ **Token über UI** eintragen — kein YAML-Edit nötig
- ✅ **Mehrere Listen** möglich (jede als eigener ConfigEntry)
- ✅ **Fälligkeitsdatum** — Anzeige + Editieren direkt in HA Todo-UI
- ✅ **Beschreibung** — Anzeige + Editieren direkt in HA Todo-UI
- 🔒 Token bleibt in HA, wird nicht an Dritte weitergegeben

## Voraussetzungen

1. **Home Assistant 2024.12+** (für die `todo`-Platform)
2. **Maton-Konto** mit Microsoft-To-Do-Connection
3. **Maton API-Token** — siehe unten

## Maton API-Token holen

1. Gehe zu https://maton.ai
2. Verbinde dein Microsoft-Konto unter **Connections → Microsoft To Do**
3. Erstelle einen API-Token unter **API Keys**

## Installation

### Variante A — manuell (empfohlen für private Repos)

1. Klone das Repo in dein HA-Config-Verzeichnis:
   ```bash
   cd /config  # oder wo dein HA-Config liegt
   git clone https://github.com/TomTje/ms-todo-ha.git
   cp -r ms-todo-ha/custom_components/ms_todo custom_components/
   ```
2. HA neu starten
3. **Einstellungen → Geräte & Dienste → Integration hinzufügen → "Microsoft To Do (Maton)"**

### Variante B — HACS (sobald veröffentlicht)

1. **HACS → Integrationen → Menü → Custom Repositories**
2. URL: `https://github.com/TomTje/ms-todo-ha`, Kategorie: **Integration**
3. Installieren, HA neu starten, dann wie oben einrichten

## Einrichtung

Nach der Installation:

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen**
2. Suche **"Microsoft To Do (Maton)"**
3. **Schritt 1:** Maton-API-Token eintragen → "Verbinden" testet sofort
4. **Schritt 2:** Liste aus Dropdown wählen
5. **Schritt 3:** Fertig — taucht im Dashboard als To-Do-Entity auf

### Optionen anpassen

Klicke auf die Integration → **"Einstellungen"**:
- **Update-Intervall:** 60–3600 Sekunden (Default: 300 = 5 Min)
- **Erledigte Aufgaben anzeigen:** Toggle

## Im Dashboard verwenden

Füge eine **To-Do-List Card** hinzu:
```yaml
type: todo-list
entity: todo.ms_todo_privat  # Name deiner Liste
```

## Mehrere Listen einbinden

Die Integration erlaubt pro Setup **eine** Liste. Für mehrere Listen:
- Wiederhole das Setup (andere Liste wählen)
- Jede Liste wird als eigene Integration + eigene To-Do-Entity angelegt

## Entwicklung / Debug

Logs einschalten:
```yaml
logger:
  default: warning
  logs:
    custom_components.ms_todo: debug
```

## Lizenz

MIT — privater Gebrauch, gerne erweitern.

## Bekannte Limitierungen

- Polling-basiert (kein Webhook von Microsoft-Seite)
- Keine Sub-Tasks (Microsoft To Do hat das, aber unsere API nicht)
- Wichtigkeit, Kategorien, Wiederholung, Erinnerung, Zugewiesen — werden von MS Graph abgerufen und sind in den `extra_state_attributes` sichtbar, aber nicht über die HA Todo-UI editierbar
