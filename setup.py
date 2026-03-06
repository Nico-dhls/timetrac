import os
import sys
from cx_Freeze import setup, Executable

upgrade_code = "{93789642-1234-5678-ABCD-1234567890AB}"

# VERSION_PLACEHOLDER is replaced by CI; fall back to 2.0.0 for local builds
_version = "VERSION_PLACEHOLDER"
if not _version[0].isdigit():
    _version = os.environ.get("TIMETRAC_VERSION", "2.0.0")

build_exe_options = {
    "packages": ["os", "PySide6", "timetrac"],
    "excludes": ["tkinter", "customtkinter"],
    "include_files": ["timetable_icon.ico"],
}

bdist_msi_options = {
    "initial_target_dir": r"[AppDataFolder]\TimeTrac",
    "add_to_path": False,
    "install_icon": "timetable_icon.ico",
    "upgrade_code": upgrade_code,
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="TimeTrac",
    version=_version,
    description="TimeTrac Zeiterfassung für SAP ITP",
    author="Nico Dahlhaus",
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
        copyright="© 2025 Nico Dahlhaus",
    )],
)
