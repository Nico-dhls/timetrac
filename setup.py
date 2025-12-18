import sys
from cx_Freeze import setup, Executable

# Optionen für den Build
build_exe_options = {
    "packages": ["os"],  # Hier weitere Pakete einfügen, falls nötig (z.B. "pandas")
    "excludes": [],
    "include_files": ["timetable_icon.ico"] # Deine Dateien hier
}

# WICHTIG: Damit keine Admin-Rechte nötig sind
bdist_msi_options = {
    "initial_target_dir": r"[AppDataFolder]\TimeTrac", # Installiert nach AppData
    "add_to_path": False,
    "install_icon": "timetable_icon.ico",
}

base = None
if sys.platform == "win32":
    base = "Win32GUI" # Nutze "Win32GUI" für GUI-Apps (keine Konsole), sonst None

setup(
    name="TimeTrac",
    version="1.2.5", # Hier Version anpassen oder dynamisch laden
    description="TimeTrac Zeiterfassung",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options, # MSI Optionen aktivieren
    },
    executables=[Executable(
        "main.py",
        base=base,
        target_name="TimeTrac.exe",
        icon="timetable_icon.ico",
        shortcut_name="TimeTrac", # Erstellt Desktop Shortcut
        shortcut_dir="DesktopFolder"
    )]
)
