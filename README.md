# TimeTrac

[![Build and Sign EXE](https://github.com/Nico-dhls/timetrac/actions/workflows/build-and-sign.yml/badge.svg)](https://github.com/Nico-dhls/timetrac/actions/workflows/build-and-sign.yml)
[![Python tests](https://github.com/Nico-dhls/timetrac/actions/workflows/tests.yml/badge.svg)](https://github.com/Nico-dhls/timetrac/actions/workflows/tests.yml)

TimeTrac ist eine desktopbasierte Zeiterfassung mit moderner Tk-Oberfläche. Das Tool hilft dir, Tätigkeiten pro Tag zu protokollieren, Zeiten zu gruppieren und häufig genutzte Werte schneller auszuwählen.

## Funktionen
- Tagesbasierte Erfassung mit Kalenderauswahl und Anzeige des Wochentags.
- Wahlweise Eingabe von Start-/Endzeit oder direkter Stundenzahl; automatische Plausibilitätsprüfung.
- Gruppierte Darstellung im Treeview nach PSP/Projekt, Tätigkeitstyp und Beschreibung.
- Verwaltung von Schnellwahllisten (PSP, Tätigkeitstyp, Beschreibung) basierend auf den letzten Einträgen.
- Dark-Theme, kompakte Tastatursteuerung und automatische Spaltenbreiten.
- Speicherung der Daten in `time_entries.json` im Projektverzeichnis.

## Voraussetzungen
- Python 3.12 (oder kompatibel)
- Abhängigkeiten aus `requirements.txt`

Installiere die Pakete am besten in einem virtuellen Environment:

```bash
python -m venv .venv
source .venv/bin/activate  # unter Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Anwendung starten

```bash
python main.py
```

Beim Start lädt TimeTrac bestehende Einträge aus `time_entries.json` oder legt die Datei automatisch an. Änderungen werden beim Speichern dauerhaft abgelegt.

## Build und Signatur
Das GitHub-Workflow **Build and Sign EXE** erstellt mit PyInstaller eine ausführbare Datei und signiert sie. Der Workflow läuft bei getaggten Releases (`v*`) oder manuell via "Run workflow". Die gebaute EXE steht anschließend als Artefakt zum Download bereit.

Für lokale Builds kannst du PyInstaller direkt nutzen:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name "timetrac" --icon "timetable_icon.ico" --version-file "version_info.txt" --add-data "timetable_icon.ico;." main.py
```

## Datenstruktur
Die gespeicherten Daten bestehen aus einem Wörterbuch mit den Schlüsseln `entries` und `presets`. Pro Tag (`YYYY-MM-DD`) wird eine Liste von Einträgen mit Feldern wie `psp`, `type`, `desc`, `start`, `end` oder `hours` abgelegt. TimeTrac berechnet Fehlzeiten automatisch und gruppiert die Sicht nach Projekten.

## Lizenz
© 2025 – Developed by Nico Dahlhaus.
