# Release v0.1.1 — async_timeout Fix

## 🐛 Bug Fix

- **Fix:** `cannot import name 'Timeout' from 'homeassistant.util.timeout'`
  - Ursache: `homeassistant.util.timeout` exportiert kein `Timeout`
  - Lösung: `async_timeout` (im HA-Container vorhanden) wird jetzt korrekt importiert
  - `async_timeout>=4.0.0` als Requirement in `manifest.json` deklariert

## 📦 Installation (HACS)

1. HACS → Integrationen → **MS To Do (Maton)**
2. Update-Indikator sollte erscheinen (kann 15 Min dauern)
3. **Aktualisieren** klicken
4. HA neu starten

## 🔧 Manuelle Installation

```bash
cd /config/custom_components
rm -rf ms_todo
git clone https://github.com/TomTje/ms-todo-ha.git /tmp/ms-todo-ha
cp -r /tmp/ms-todo-ha/custom_components/ms_todo .
rm -rf /tmp/ms-todo-ha
```

Danach HA neu starten.

## 🔗 Links

- Repository: https://github.com/TomTje/ms-todo-ha
- Issues: https://github.com/TomTje/ms-todo-ha/issues

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
