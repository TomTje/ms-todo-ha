# MS To Do Card — Lovelace Custom Card

**MS To Do Card** ist eine benutzerdefinierte Lovelace-Karte für Home Assistant, die erweiterte MS To Do-Felder direkt in der UI anzeigt und bearbeitbar macht.

## Features

- 🔴🟡🟢 **Wichtigkeit setzen** — per Klick auf das Badge
- 🏷️ **Kategorien** — Anzeige und Bearbeitung
- 📝 **Beschreibung** — wird unter dem Titel angezeigt
- 📅 **Fälligkeitsdatum** — mit Emoji
- ✅ **Erledigt-Status** — Checkbox zum Umschalten

## Installation (HACS)

1. **HACS → Integrations** → MS To Do (Maton) bereits installiert ✓
2. **HACS → Plugins** → `MS To Do Card` suchen → **Install**
3. **Lovelace Resource** hinzufügen (geschieht automatisch via HACS)

ODER manuell:
```yaml
lovelace:
  resources:
    - url: /hacsfiles/ms_todo/ms-todo-card.js
      type: module
```

## Verwendung

```yaml
type: custom:ms-todo-card
entity: todo.aufgaben
title: Meine Aufgaben
```

## Voraussetzungen

- [MS To Do (Maton) Integration](https://github.com/TomTje/ms-todo-ha) installiert
- Home Assistant 2024.9+
