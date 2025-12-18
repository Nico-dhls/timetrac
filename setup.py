import sys
from cx_Freeze import setup, Executable

# --- WICHTIG: UUID Generieren ---
# Damit Windows erkennt, dass eine neue Version ein Update ist (und nicht eine zweite App),
# braucht man eine feste ID. Ändere diesen Wert NICHT, wenn du Updates veröffentlichst.
# Du kannst dir online eine UUID generieren oder diese hier nutzen:
upgrade_code = "{93789642-1234-5678-ABCD-1234567890AB}" 

build_exe_options = {
    "packages": ["os"], 
    "excludes": [],
    "include_files": ["timetable_icon.ico"] 
}

bdist_msi_options = {
    "initial_target_dir": r"[AppDataFolder]\TimeTrac", # Installiert lokal (%AppData%)
    "add_to_path": False,
    "install_icon": "timetable_icon.ico",
    "upgrade_code": upgrade_code,
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="TimeTrac",
    # Dieser Platzhalter "VERSION_PLACEHOLDER" wird gleich von GitHub Actions ersetzt
    version="VERSION_PLACEHOLDER", 
    description="TimeTrac Zeiterfassung",
    author="Nico Dahlhaus", # Taucht in den Datei-Eigenschaften auf
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
    executables=[Executable(
        "main.py",
        base=base,
        target_name="TimeTrac.exe",
        icon="timetable_icon.ico",
        shortcut_name="TimeTrac",
        shortcut_dir="DesktopFolder",
        copyright="© 2025 Nico Dahlhaus" # Taucht in den Datei-Eigenschaften auf
    )]
)
