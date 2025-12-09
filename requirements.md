# Application dependencies
# Tkinter is bundled with most Python installations; no external packages required.
If you want to create an executable, consider using PyInstaller or cx_Freeze.

You can use PyInstaller by installing it using:`pip install pyinstaller` 

and then running `pyinstaller --onefile --noconsole --icon=".\timetable_icon.ico" --add-data=".\timetable_icon.ico;." .\main.py`