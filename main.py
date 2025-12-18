import json
from datetime import datetime, date, timedelta
from pathlib import Path
import calendar
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

# Configure CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class Tooltip:
    def __init__(self, widget, text, bg="#1e293b", fg="#f8fafc"):
        self.widget = widget
        self.text = text
        self.bg = bg
        self.fg = fg
        self.tipwindow = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, _event=None):
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert") or (0, 0, 0, 0)
        x = x + self.widget.winfo_rootx() + 10
        y = y + cy + self.widget.winfo_rooty() + 10
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.configure(bg=self.bg)
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background=self.bg,
            foreground=self.fg,
            relief=tk.SOLID,
            borderwidth=1,
            padx=8,
            pady=6,
            font=("Segoe UI", 10),
        )
        label.pack()
        tw.wm_geometry(f"+{x}+{y}")

    def hide_tip(self, _event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

DATA_FILE = Path("time_entries.json")
ICON_FILE = Path(__file__).resolve().parent / "timetable_icon.ico"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"
MAX_RECENTS = 10


def load_data():
    if DATA_FILE.exists():
        try:
            raw = json.loads(DATA_FILE.read_text())
        except json.JSONDecodeError:
            return {"entries": {}, "presets": []}
        if "entries" in raw or "presets" in raw:
            raw.setdefault("entries", {})
            raw.setdefault("presets", [])
            return raw
        return {"entries": raw, "presets": []}
    return {"entries": {}, "presets": []}


def save_data(data):
    DATA_FILE.write_text(json.dumps(data, indent=2))


def ensure_date_bucket(entries, day_key):
    if day_key not in entries:
        entries[day_key] = []
    return entries[day_key]


def parse_time(value):
    return datetime.strptime(value, TIME_FORMAT)


def calculate_hours(start_value, end_value):
    start_time = parse_time(start_value)
    end_time = parse_time(end_value)
    if end_time <= start_time:
        raise ValueError("Ende muss nach dem Start liegen")
    return (end_time - start_time).total_seconds() / 3600


def collect_recent_values(entries, field):
    values = []
    for day in sorted(entries.keys(), reverse=True):
        for entry in reversed(entries[day]):
            value = entry.get(field, "")
            if value and value not in values:
                values.append(value)
            if len(values) >= MAX_RECENTS:
                return values
    return values


GERMAN_MONTHS = [
    "Januar",
    "Februar",
    "März",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Dezember",
]


class CalendarPicker(ctk.CTkToplevel):
    def __init__(self, master, current_date, on_select, icon_image=None):
        super().__init__(master)
        self.title("Datum wählen")
        self.on_select = on_select
        self.selected = current_date
        self.resizable(False, False)
        if icon_image is not None:
            self.after(200, lambda: self.iconphoto(False, icon_image))

        # Ensure it stays on top
        self.attributes("-topmost", True)

        self.month_var = tk.IntVar(value=current_date.month)
        self.year_var = tk.IntVar(value=current_date.year)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(padx=15, pady=15)

        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill=tk.X, pady=(0, 10))

        prev_btn = ctk.CTkButton(header, text="◀", width=40, command=self.prev_month, fg_color="transparent", border_width=1)
        prev_btn.pack(side=tk.LEFT)

        self.month_label = ctk.CTkLabel(header, text="", font=("Segoe UI", 14, "bold"))
        self.month_label.pack(side=tk.LEFT, expand=True)

        next_btn = ctk.CTkButton(header, text="▶", width=40, command=self.next_month, fg_color="transparent", border_width=1)
        next_btn.pack(side=tk.RIGHT)

        self.days_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.days_frame.pack()

        self.build_calendar()

    def prev_month(self):
        month = self.month_var.get() - 1
        year = self.year_var.get()
        if month == 0:
            month = 12
            year -= 1
        self.month_var.set(month)
        self.year_var.set(year)
        self.build_calendar()

    def next_month(self):
        month = self.month_var.get() + 1
        year = self.year_var.get()
        if month == 13:
            month = 1
            year += 1
        self.month_var.set(month)
        self.year_var.set(year)
        self.build_calendar()

    def build_calendar(self):
        for widget in self.days_frame.winfo_children():
            widget.destroy()

        month = self.month_var.get()
        year = self.year_var.get()
        month_name = GERMAN_MONTHS[month - 1]
        self.month_label.configure(text=f"{month_name} {year}")

        selected_week_row = None
        if self.selected and self.selected.month == month and self.selected.year == year:
            for row_idx, week in enumerate(calendar.monthcalendar(year, month), start=1):
                if self.selected.day in week:
                    selected_week_row = row_idx
                    break

        weekdays = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        for col, name in enumerate(weekdays):
            ctk.CTkLabel(
                self.days_frame,
                text=name,
                width=40,
                height=30,
                anchor="center",
                text_color="gray"
            ).grid(row=0, column=col, padx=2, pady=2)

        for row, week in enumerate(calendar.monthcalendar(year, month), start=1):
            for col, day in enumerate(week):
                if day == 0:
                    continue

                day_date = date(year, month, day)
                is_selected = (self.selected == day_date)

                fg_color = None
                if is_selected:
                    fg_color = ("#3a7ebf", "#1f6aa5") # Custom blueish

                btn = ctk.CTkButton(
                    self.days_frame,
                    text=str(day),
                    width=40,
                    height=30,
                    fg_color=fg_color if is_selected else "transparent",
                    border_width=1 if not is_selected else 0,
                    border_color=("#3E4551", "#3E4551"),
                    text_color=("black", "white"),
                    command=lambda d=day: self.select_day(d),
                )
                btn.grid(row=row, column=col, padx=2, pady=2)

    def select_day(self, day):
        selected_date = date(self.year_var.get(), self.month_var.get(), day)
        self.selected = selected_date
        self.on_select(selected_date)
        self.destroy()


class TimePicker(ctk.CTkToplevel):
    def __init__(self, master, on_select, icon_image=None):
        super().__init__(master)
        self.title("Zeit wählen")
        self.geometry("340x400")
        self.resizable(False, True)
        self.on_select = on_select
        self.transient(master)
        self.attributes("-topmost", True)
        if icon_image is not None:
            self.after(200, lambda: self.iconphoto(False, icon_image))

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 24 rows (hours), 4 cols (minutes)
        for hour in range(24):
            # Row label (Hour) - Optional, but cleaner if we just list times
            # Let's list times in grid:
            # 00:00 00:15 00:30 00:45
            # ...

            # Row header
            ctk.CTkLabel(self.scroll_frame, text=f"{hour:02d}:", width=30, font=("Segoe UI", 12, "bold"), text_color="gray").grid(row=hour, column=0, padx=(0, 5), pady=2)

            for i, minute in enumerate([0, 15, 30, 45]):
                time_str = f"{hour:02d}:{minute:02d}"
                btn = ctk.CTkButton(
                    self.scroll_frame,
                    text=time_str,
                    width=60,
                    height=28,
                    fg_color="transparent",
                    border_width=1,
                    border_color=("#3E4551", "#3E4551"),
                    text_color=("black", "white"),
                    command=lambda t=time_str: self.select_time(t)
                )
                btn.grid(row=hour, column=i+1, padx=2, pady=2)

    def select_time(self, time_str):
        self.on_select(time_str)
        self.destroy()


class PresetManager(ctk.CTkToplevel):
    def __init__(self, master, presets, on_save, icon_image=None):
        super().__init__(master)
        self.title("Vorlagen verwalten")
        self.geometry("600x400")
        self.resizable(False, False)
        # CTk toplevels act as independent windows by default, keep it transient
        self.transient(master)
        if icon_image is not None:
             self.after(200, lambda: self.iconphoto(False, icon_image))
        self.protocol("WM_DELETE_WINDOW", self.save_and_close)

        self.presets = [dict(preset) for preset in presets]
        self.on_save = on_save

        main_layout = ctk.CTkFrame(self, fg_color="transparent")
        main_layout.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ctk.CTkLabel(main_layout, text="Vorlagen setzen PSP und Leistungsart automatisch.", text_color="gray").pack(anchor=tk.W, pady=(0, 10))

        # Treeview Wrapper Frame
        tree_frame = ctk.CTkFrame(main_layout)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "psp", "type")
        # Standard ttk Treeview needs styling to match CTk
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)
        self.tree.heading("name", text="Name")
        self.tree.heading("psp", text="PSP")
        self.tree.heading("type", text="Leistungsart")
        self.tree.column("name", width=200)
        self.tree.column("psp", width=120)
        self.tree.column("type", width=160)

        # Scrollbar
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        form = ctk.CTkFrame(main_layout, fg_color="transparent")
        form.pack(fill=tk.X, pady=(15, 5))

        self.name_var = tk.StringVar()
        self.psp_var = tk.StringVar()
        self.type_var = tk.StringVar()

        ctk.CTkLabel(form, text="Name:").grid(row=0, column=0, sticky=tk.W)
        ctk.CTkEntry(form, textvariable=self.name_var, width=180).grid(row=1, column=0, sticky=tk.W, padx=(0, 10))

        ctk.CTkLabel(form, text="PSP:").grid(row=0, column=1, sticky=tk.W)
        ctk.CTkEntry(form, textvariable=self.psp_var, width=150).grid(row=1, column=1, sticky=tk.W, padx=(0, 10))

        ctk.CTkLabel(form, text="Leistungsart:").grid(row=0, column=2, sticky=tk.W)
        ctk.CTkEntry(form, textvariable=self.type_var, width=180).grid(row=1, column=2, sticky=tk.W)

        btn_frame = ctk.CTkFrame(main_layout, fg_color="transparent")
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        ctk.CTkButton(btn_frame, text="Hinzufügen", command=self.add_preset).pack(side=tk.LEFT)
        self.update_btn = ctk.CTkButton(btn_frame, text="Aktualisieren", command=self.update_selected)
        ctk.CTkButton(btn_frame, text="Entfernen", command=self.remove_selected, fg_color="#ef4444", hover_color="#dc2626").pack(side=tk.LEFT, padx=(10, 0))
        ctk.CTkButton(btn_frame, text="Schließen", command=self.save_and_close, fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(side=tk.RIGHT)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.refresh_list()
        self._update_update_button_visibility()

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, preset in enumerate(self.presets):
            self.tree.insert("", "end", iid=str(idx), values=(preset.get("name", ""), preset.get("psp", ""), preset.get("type", "")))

    def _selected_index(self):
        selection = self.tree.selection()
        if not selection:
            return None
        try:
            return int(selection[0])
        except ValueError:
            return None

    def on_select(self, event=None):
        idx = self._selected_index()
        if idx is None or idx >= len(self.presets):
            self._update_update_button_visibility()
            return
        preset = self.presets[idx]
        self.name_var.set(preset.get("name", ""))
        self.psp_var.set(preset.get("psp", ""))
        self.type_var.set(preset.get("type", ""))
        self._update_update_button_visibility()

    def add_preset(self):
        name = self.name_var.get().strip()
        psp = self.psp_var.get().strip()
        ltype = self.type_var.get().strip()
        if not name:
            messagebox.showerror("Vorlage", "Bitte gib einen Namen für die Vorlage an.")
            return
        if not psp and not ltype:
            messagebox.showerror("Vorlage", "Mindestens PSP oder Leistungsart müssen gesetzt sein.")
            return
        self.presets.append({"name": name, "psp": psp, "type": ltype})
        self.refresh_list()
        self.tree.selection_remove(self.tree.selection())
        self._update_update_button_visibility()

    def update_selected(self):
        name = self.name_var.get().strip()
        psp = self.psp_var.get().strip()
        ltype = self.type_var.get().strip()
        if not name:
            messagebox.showerror("Vorlage", "Bitte gib einen Namen für die Vorlage an.")
            return
        if not psp and not ltype:
            messagebox.showerror("Vorlage", "Mindestens PSP oder Leistungsart müssen gesetzt sein.")
            return
        idx = self._selected_index()
        if idx is None or idx >= len(self.presets):
            messagebox.showerror("Vorlage", "Bitte wähle eine Vorlage zum Aktualisieren aus.")
            self._update_update_button_visibility()
            return
        self.presets[idx] = {"name": name, "psp": psp, "type": ltype}
        self.refresh_list()
        self.tree.selection_set(str(idx))
        self._update_update_button_visibility()

    def _update_update_button_visibility(self):
        if self._selected_index() is None:
            if self.update_btn.winfo_manager():
                self.update_btn.pack_forget()
            return
        if not self.update_btn.winfo_manager():
            self.update_btn.pack(side=tk.LEFT, padx=(10, 0))

    def remove_selected(self):
        idx = self._selected_index()
        if idx is None or idx >= len(self.presets):
            return
        self.presets.pop(idx)
        self.refresh_list()
        self.name_var.set("")
        self.psp_var.set("")
        self.type_var.set("")
        self._update_update_button_visibility()

    def save_and_close(self):
        self.on_save(self.presets)
        self.destroy()


class TimeTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Zeiterfassung")
        self.geometry("1200x800")
        self.minsize(1000, 700)

        # Data Loading
        self.data = load_data()
        self.entries = self.data["entries"]
        self.presets = self.data["presets"]
        self.editing_index = None
        self._calendar_window = None
        self.icon_image = self._load_icon()

        # Variables
        self.date_var = tk.StringVar(value=date.today().strftime(DATE_FORMAT))
        self.preset_var = tk.StringVar()
        self.psp_var = tk.StringVar()
        self.type_var = tk.StringVar()
        self.desc_var = tk.StringVar()
        self.start_var = tk.StringVar()
        self.end_var = tk.StringVar()
        self.hours_var = tk.StringVar()
        self.time_mode = tk.StringVar(value="range")
        self.timer_start = None

        self._set_default_times()
        self._configure_treeview_style()
        self.build_ui()
        self.refresh_entry_list()

    def _configure_treeview_style(self):
        # Configure standard Treeview to match CustomTkinter Dark Theme
        style = ttk.Style()
        style.theme_use("clam")

        bg_color = "#2b2b2b" # Dark gray (approx ctk frame color)
        fg_color = "white"
        selected_bg = "#1f538d" # Standard ctk blue

        style.configure("Treeview",
                        background="#242424", # Even darker for list
                        foreground=fg_color,
                        fieldbackground="#242424",
                        borderwidth=0,
                        rowheight=30,
                        font=("Segoe UI", 11))

        style.map("Treeview",
                  background=[("selected", selected_bg)],
                  foreground=[("selected", "white")])

        style.configure("Treeview.Heading",
                        background="#333333",
                        foreground="white",
                        relief="flat",
                        font=("Segoe UI", 11, "bold"),
                        padding=(10, 8))

        style.map("Treeview.Heading",
                  background=[("active", "#404040")])

    def build_ui(self):
        # Main Layout
        self.grid_columnconfigure(0, weight=1, uniform="group1")
        self.grid_columnconfigure(1, weight=1, uniform="group1")
        self.grid_rowconfigure(0, weight=1)

        # Left Column: Form
        form_frame = ctk.CTkFrame(self)
        form_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        form_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(form_frame, text="Zeiterfassung", font=("Segoe UI", 24, "bold"), text_color=("gray10", "gray90")).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(form_frame, text="Erfasse Zeiten schnell & modern.", text_color="gray").grid(row=1, column=0, sticky="w", padx=20, pady=(0, 20))

        # Date Selection
        date_card = ctk.CTkFrame(form_frame)
        date_card.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 15))
        date_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(date_card, text="Datum:").grid(row=0, column=0, padx=15, pady=15, sticky="w")

        date_entry = ctk.CTkEntry(date_card, textvariable=self.date_var, width=140, font=("Segoe UI", 13, "bold"))
        date_entry.grid(row=0, column=1, padx=10, pady=15, sticky="ew")
        date_entry.bind("<Button-1>", self.open_calendar) # Clicking entry opens calendar

        btn_today = ctk.CTkButton(date_card, text="Heute", width=60, command=self.set_today)
        btn_today.grid(row=0, column=2, padx=(0, 10))

        btn_prev = ctk.CTkButton(date_card, text="◀", width=40, command=self.set_yesterday)
        btn_prev.grid(row=0, column=3, padx=(0, 15))

        self.day_display_var = tk.StringVar()
        ctk.CTkLabel(date_card, textvariable=self.day_display_var, font=("Segoe UI", 12, "bold"), text_color="gray").grid(row=1, column=0, columnspan=4, sticky="w", padx=15, pady=(0, 15))

        # Preset Selection
        preset_card = ctk.CTkFrame(form_frame)
        preset_card.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 15))
        preset_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(preset_card, text="Vorlage:").grid(row=0, column=0, padx=15, pady=15, sticky="w")

        self.preset_combo = ctk.CTkComboBox(preset_card, variable=self.preset_var, command=self.apply_selected_preset)
        self.preset_combo.grid(row=0, column=1, padx=10, sticky="ew")

        ctk.CTkButton(preset_card, text="Verwalten", width=80, command=self.open_preset_manager).grid(row=0, column=2, padx=(0, 15))

        # Fields (PSP, Type, Time)
        fields_card = ctk.CTkFrame(form_frame)
        fields_card.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 15))
        fields_card.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(fields_card, text="PSP (optional):").grid(row=0, column=0, padx=15, pady=(15, 0), sticky="w")
        ctk.CTkLabel(fields_card, text="Leistungsart:").grid(row=0, column=1, padx=10, pady=(15, 0), sticky="w")

        self.psp_combo = ctk.CTkComboBox(fields_card, variable=self.psp_var)
        self.psp_combo.grid(row=1, column=0, padx=15, pady=(5, 15), sticky="ew")

        self.type_combo = ctk.CTkComboBox(fields_card, variable=self.type_var)
        self.type_combo.grid(row=1, column=1, padx=10, pady=(5, 15), sticky="ew")

        # Time Section
        time_card = ctk.CTkFrame(form_frame)
        time_card.grid(row=5, column=0, sticky="ew", padx=20, pady=(0, 15))
        time_card.grid_columnconfigure(0, weight=1)

        self.range_frame = ctk.CTkFrame(time_card, fg_color="transparent")
        self.range_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(self.range_frame, text="Start:").grid(row=0, column=0, sticky="w")
        self._build_time_picker_control(self.range_frame, self.start_var, 0, 1)

        ctk.CTkLabel(self.range_frame, text="Ende:").grid(row=0, column=2, padx=(15, 0), sticky="w")
        self._build_time_picker_control(self.range_frame, self.end_var, 0, 3)

        self.duration_frame = ctk.CTkFrame(time_card, fg_color="transparent")
        # Hidden by default in range mode

        ctk.CTkLabel(self.duration_frame, text="Stunden:").grid(row=0, column=0, sticky="w")
        self.hours_entry = ctk.CTkEntry(self.duration_frame, textvariable=self.hours_var, width=100)
        self.hours_entry.grid(row=0, column=1, padx=10)

        self.mode_btn = ctk.CTkButton(time_card, text="Modus: Stunden", width=120, fg_color="transparent", border_width=1, command=self.toggle_time_mode)
        self.mode_btn.grid(row=0, column=1, padx=15, pady=15)

        # Description
        desc_card = ctk.CTkFrame(form_frame)
        desc_card.grid(row=6, column=0, sticky="ew", padx=20, pady=(0, 15))
        desc_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(desc_card, text="Beschreibung:").grid(row=0, column=0, padx=15, pady=(15, 0), sticky="w")
        self.desc_combo = ctk.CTkComboBox(desc_card, variable=self.desc_var)
        self.desc_combo.grid(row=1, column=0, padx=15, pady=(5, 15), sticky="ew")

        # Action Buttons
        btn_card = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_card.grid(row=7, column=0, sticky="ew", padx=20, pady=(0, 20))
        btn_card.grid_columnconfigure((0, 1), weight=1)

        self.add_btn = ctk.CTkButton(btn_card, text="Eintrag hinzufügen", height=40, font=("Segoe UI", 13, "bold"), command=self.add_entry)
        self.add_btn.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.update_btn = ctk.CTkButton(btn_card, text="Aktualisieren", height=40, font=("Segoe UI", 13, "bold"), command=self.update_entry)
        self.update_btn.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.update_btn.grid_remove() # Hidden initially

        ctk.CTkButton(btn_card, text="Neu", width=80, height=40, fg_color="transparent", border_width=1, command=self.reset_form).grid(row=0, column=1, sticky="e")
        ctk.CTkButton(btn_card, text="Löschen", width=80, height=40, fg_color="#ef4444", hover_color="#dc2626", command=self.delete_entry).grid(row=0, column=2, padx=(10, 0), sticky="e")

        # Timer Area
        timer_frame = ctk.CTkFrame(form_frame)
        timer_frame.grid(row=8, column=0, sticky="ew", padx=20, pady=(0, 20))
        timer_frame.grid_columnconfigure(1, weight=1)

        self.timer_btn = ctk.CTkButton(timer_frame, text="Timer starten", command=self.toggle_timer)
        self.timer_btn.grid(row=0, column=0, padx=15, pady=15)

        self.timer_label = ctk.CTkLabel(timer_frame, text="", font=("Segoe UI", 16, "bold"), text_color="#3b8ed0")
        self.timer_label.grid(row=0, column=1, padx=15)

        self.abort_btn = ctk.CTkButton(timer_frame, text="✕", width=40, fg_color="transparent", border_width=1, text_color="gray", command=self.abort_timer)
        self.abort_btn.grid(row=0, column=2, padx=15)
        self.abort_btn.grid_remove()

        # Right Column: List
        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(list_frame, text="Übersicht", font=("Segoe UI", 24, "bold"), text_color=("gray10", "gray90")).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(list_frame, text="Deine Einträge für den Tag.", text_color="gray").grid(row=1, column=0, sticky="w", padx=20, pady=(0, 15))

        # Treeview in a CTk container
        tree_container = ctk.CTkFrame(list_frame, fg_color="transparent")
        tree_container.grid(row=2, column=0, sticky="nsew", padx=20)
        tree_container.grid_columnconfigure(0, weight=1)
        tree_container.grid_rowconfigure(0, weight=1)

        columns = ("psp", "type", "desc", "hours")
        self.tree = ttk.Treeview(tree_container, columns=columns, show="tree headings", style="Treeview")
        self.tree.heading("#0", text="")
        self.tree.column("#0", width=20, stretch=False)
        self.tree.heading("psp", text="PSP")
        self.tree.heading("type", text="Leistungsart")
        self.tree.heading("desc", text="Beschreibung")
        self.tree.heading("hours", text="Stunden")

        self.tree.column("psp", width=100)
        self.tree.column("type", width=150)
        self.tree.column("desc", width=200)
        self.tree.column("hours", width=80, anchor="e")

        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Totals
        totals_frame = ctk.CTkFrame(list_frame)
        totals_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=20)
        totals_frame.grid_columnconfigure(1, weight=1)

        self.total_var = tk.StringVar(value="Summe Tag: 0.00 h")
        ctk.CTkLabel(totals_frame, textvariable=self.total_var, font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT, padx=20, pady=15)

        self.week_total_var = tk.StringVar(value="Woche: 0.00 h")
        ctk.CTkLabel(totals_frame, textvariable=self.week_total_var, font=("Segoe UI", 14, "bold"), text_color="gray").pack(side=tk.RIGHT, padx=20, pady=15)

        # Tree bindings
        self.tree.bind("<<TreeviewSelect>>", self.on_select_entry)
        self.tree.bind("<Control-c>", self.copy_selection)
        self.tree.bind("<Control-C>", self.copy_selection)

        # Styling tags
        self.tree.tag_configure("group", background="#333333", foreground="white", font=("Segoe UI", 11, "bold"))

        # Initialization
        self.update_combobox_values()
        self._apply_time_mode()

    def _build_time_picker_control(self, parent, variable, row, col):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, padx=5, sticky="ew")

        entry = ctk.CTkEntry(frame, textvariable=variable, width=80)
        entry.pack(side=tk.LEFT)

        btn = ctk.CTkButton(
            frame,
            text="⏱",
            width=30,
            fg_color="transparent",
            border_width=1,
            command=lambda: self.open_time_picker(variable)
        )
        btn.pack(side=tk.LEFT, padx=(2, 0))

    def open_time_picker(self, variable):
        if self._calendar_window is not None and self._calendar_window.winfo_exists():
            self._calendar_window.lift()
            return

        def on_select(time_str):
            variable.set(time_str)
            self._calendar_window = None

        self._calendar_window = TimePicker(self, on_select, self.icon_image)

    def _set_default_times(self):
        now_str = datetime.now().strftime(TIME_FORMAT)
        self.start_var.set(now_str)
        self.end_var.set(now_str)
        self.hours_var.set("")

    def open_calendar(self, _event=None):
        if self._calendar_window is not None and self._calendar_window.winfo_exists():
            self._calendar_window.lift()
            return
        self._calendar_window = None
        current = self.current_date_value()
        picker = CalendarPicker(self, current, self.set_selected_date, self.icon_image)
        self._calendar_window = picker
        picker.protocol("WM_DELETE_WINDOW", self._close_calendar)

    def _close_calendar(self):
        if self._calendar_window is not None and self._calendar_window.winfo_exists():
            self._calendar_window.destroy()
        self._calendar_window = None

    def set_selected_date(self, selected):
        self.date_var.set(selected.strftime(DATE_FORMAT))
        self.refresh_entry_list()

    def set_today(self):
        self.set_selected_date(date.today())

    def set_yesterday(self):
        self.set_selected_date(date.today() - timedelta(days=1))

    def current_date_value(self):
        try:
            return datetime.strptime(self.date_var.get(), DATE_FORMAT).date()
        except ValueError:
            return date.today()

    def update_combobox_values(self):
        self.psp_combo.configure(values=collect_recent_values(self.entries, "psp"))
        self.type_combo.configure(values=collect_recent_values(self.entries, "type"))
        self._update_desc_values()
        self._update_preset_values()

    def _update_desc_values(self):
        day_key = self.date_var.get().strip()
        entries = self.entries.get(day_key, [])
        desc_values = []
        for entry in entries:
            desc = entry.get("desc", "")
            if desc and desc not in desc_values:
                desc_values.append(desc)
        if not desc_values:
            desc_values = [""] # Empty list can cause issues in older ctk versions?
        self.desc_combo.configure(values=desc_values)

    def _preset_names(self):
        names = []
        for preset in self.presets:
            name = preset.get("name")
            if name:
                names.append(name)
        return names

    def _update_preset_values(self):
        names = self._preset_names()
        self.preset_combo.configure(values=names)
        current = self.preset_var.get()
        if current and current not in names:
            self.preset_var.set("")

    def apply_selected_preset(self, choice):
        # Callback for CTkComboBox gives the choice directly
        for preset in self.presets:
            if preset.get("name") == choice:
                if preset.get("psp"):
                    self.psp_var.set(preset.get("psp", ""))
                if preset.get("type"):
                    self.type_var.set(preset.get("type", ""))
                return

    def open_preset_manager(self):
        PresetManager(self, self.presets, self._save_presets, self.icon_image)

    def _save_presets(self, presets):
        self.presets[:] = presets
        self.data["presets"] = self.presets
        self._update_preset_values()
        save_data(self.data)

    def validate_fields(self):
        psp = self.psp_var.get().strip()
        ltype = self.type_var.get().strip()
        desc = self.desc_var.get().strip()
        start = self.start_var.get().strip()
        end = self.end_var.get().strip()
        hours_value = self.hours_var.get().strip()

        if self.time_mode.get() == "range":
            if not ltype or not start or not end:
                raise ValueError("Leistungsart, Start und Ende sind erforderlich")
            try:
                hours = calculate_hours(start, end)
            except Exception as exc:
                raise ValueError(str(exc)) from exc
        else:
            if not ltype or not hours_value:
                raise ValueError("Leistungsart und Stunden sind erforderlich")
            try:
                hours = float(hours_value.replace(",", "."))
            except ValueError as exc:
                raise ValueError("Stunden müssen eine Zahl sein") from exc
            if hours <= 0:
                raise ValueError("Stunden müssen größer als 0 sein")
            start = ""
            end = ""

        try:
            selected_date = datetime.strptime(self.date_var.get(), DATE_FORMAT).date()
        except ValueError as exc:
            raise ValueError("Datum muss im Format JJJJ-MM-TT vorliegen") from exc

        return selected_date.strftime(DATE_FORMAT), psp, ltype, desc, start, end, hours

    def add_entry(self):
        try:
            day_key, entry = self._prepare_entry()
        except ValueError as exc:
            messagebox.showerror("Ungültige Eingabe", str(exc))
            return

        entries = ensure_date_bucket(self.entries, day_key)
        entries.append(entry)

        save_data(self.data)
        self.update_combobox_values()
        self.refresh_entry_list()
        self.reset_form()

    def update_entry(self):
        if self.editing_index is None:
            messagebox.showinfo("Eintrag aktualisieren", "Bitte wähle zuerst einen Eintrag aus.")
            return

        try:
            day_key, entry = self._prepare_entry()
        except ValueError as exc:
            messagebox.showerror("Ungültige Eingabe", str(exc))
            return

        entries = ensure_date_bucket(self.entries, day_key)
        if self.editing_index >= len(entries):
            messagebox.showinfo("Eintrag aktualisieren", "Der ausgewählte Eintrag existiert nicht mehr.")
            self.reset_form()
            return

        entries[self.editing_index] = entry

        save_data(self.data)
        self.update_combobox_values()
        self.refresh_entry_list()
        self.reset_form()

    def _prepare_entry(self):
        day_key, psp, ltype, desc, start, end, hours = self.validate_fields()
        entry = {
            "psp": psp,
            "type": ltype,
            "desc": desc,
            "start": start,
            "end": end,
            "hours": hours,
            "mode": self.time_mode.get(),
        }
        return day_key, entry

    def reset_form(self):
        self.preset_var.set("")
        self.psp_var.set("")
        self.type_var.set("")
        self.desc_var.set("")
        self._set_default_times()
        self.time_mode.set("range")
        self._apply_time_mode()
        self.editing_index = None
        self._toggle_update_button(False)
        self.tree.selection_remove(self.tree.selection())

    def refresh_entry_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        day_key = self.date_var.get().strip()
        self._update_day_display(day_key)
        entries = self.entries.get(day_key, [])
        self._update_desc_values()
        self.item_index_map = {}
        total_hours = 0.0
        grouped_entries = self._group_entries(entries)

        for group_idx, (group_key, items) in enumerate(grouped_entries):
            group_hours = sum(item[2] for item in items)
            psp, ltype, desc = group_key
            parent_id = f"group-{group_idx}"
            self.tree.insert(
                "",
                "end",
                iid=parent_id,
                text="",
                values=(psp, ltype, desc, f"{group_hours:.2f}"),
                open=True, # Open by default in desktop view
                tags=("group",),
            )
            total_hours += group_hours
            for child_idx, (entry_idx, entry, hours) in enumerate(items):
                item_id = f"{parent_id}-{child_idx}"
                self.item_index_map[item_id] = entry_idx
                self.tree.insert(
                    parent_id,
                    "end",
                    iid=item_id,
                    text="",
                    values=(
                        entry.get("psp", ""),
                        entry.get("type", ""),
                        entry.get("desc", ""),
                        f"{hours:.2f}",
                    ),
                )

        self.total_var.set(f"Summe Tag: {total_hours:.2f} h")

        week_hours = self._calculate_week_hours(day_key)
        self.week_total_var.set(f"Woche: {week_hours:.2f} h")

    def on_select_entry(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item_id = selection[0]
        if item_id not in self.item_index_map:
            self.editing_index = None
            self._toggle_update_button(False)
            return
        idx = self.item_index_map[item_id]
        day_key = self.date_var.get().strip()
        entries = self.entries.get(day_key, [])
        if idx >= len(entries):
            return
        entry = entries[idx]
        self.psp_var.set(entry.get("psp", ""))
        self.type_var.set(entry.get("type", ""))
        self.desc_var.set(entry.get("desc", ""))
        mode = entry.get("mode", "range")
        self.time_mode.set(mode)
        if mode == "range":
            self.start_var.set(entry.get("start", ""))
            self.end_var.set(entry.get("end", ""))
            self.hours_var.set("")
        else:
            self.hours_var.set(str(entry.get("hours", "")))
            self.start_var.set("")
            self.end_var.set("")
        self._apply_time_mode()
        self.editing_index = idx
        self._toggle_update_button(True)

    def copy_selection(self, event=None):
        selection = self.tree.selection()
        if not selection:
            return "break"

        item_id = selection[0]
        values = self.tree.item(item_id, "values")
        if not values:
            return "break"

        day_key = self.date_var.get().strip()
        try:
            day_date = datetime.strptime(day_key, DATE_FORMAT).date()
        except ValueError:
            return "break"

        psp, ltype, desc, hours = values
        hours_value = str(hours).replace(",", ".")
        try:
            hours_float = float(hours_value)
        except ValueError:
            return "break"

        hours_text = f"{hours_float:.2f}".replace(".", ",")
        weekday_index = day_date.weekday()
        day_hours = ["", "", "", "", ""]  # Mo-Fr
        if 0 <= weekday_index < len(day_hours):
            day_hours[weekday_index] = hours_text

        columns = [
            ltype,
            psp,
            "",  # H (nicht benötigt, aber vorhanden)
            "",  # Bezeichnung (wird separat gesetzt)
            "",  # zweite Bezeichnung (optional)
            "",  # ME (nicht benötigt)
            "",  # Summe (wird automatisch berechnet)
            *day_hours,
        ]

        text = "\t".join(columns) + "\r\n"

        self.clipboard_clear()
        self.clipboard_append(text)
        return "break"

    def delete_entry(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Eintrag löschen", "Bitte wähle einen Eintrag zum Löschen aus.")
            return
        item_id = selection[0]
        if item_id not in self.item_index_map:
            messagebox.showinfo("Eintrag löschen", "Bitte wähle einen konkreten Untereintrag aus.")
            return
        idx = self.item_index_map[item_id]
        day_key = self.date_var.get().strip()
        entries = self.entries.get(day_key, [])
        if idx >= len(entries):
            return
        entries.pop(idx)
        save_data(self.data)
        self.editing_index = None
        self.refresh_entry_list()
        self.reset_form()

    def _update_day_display(self, day_key):
        try:
            day_date = datetime.strptime(day_key, DATE_FORMAT).date()
        except ValueError:
            self.day_display_var.set("")
            return
        weekday_names = [
            "Montag",
            "Dienstag",
            "Mittwoch",
            "Donnerstag",
            "Freitag",
            "Samstag",
            "Sonntag",
        ]
        weekday = weekday_names[day_date.weekday()]
        formatted = day_date.strftime("%d.%m.%Y")
        self.day_display_var.set(f"{weekday} {formatted}")

    def _group_entries(self, entries):
        groups = {}
        for idx, entry in enumerate(entries):
            psp = entry.get("psp", "")
            ltype = entry.get("type", "")
            desc = entry.get("desc", "")
            key = (psp, ltype, desc)
            hours = self._entry_hours(entry)
            if key not in groups:
                groups[key] = []
            groups[key].append((idx, entry, hours))

        return list(groups.items())

    def _entry_hours(self, entry):
        hours_raw = entry.get("hours")
        if hours_raw is None:
            try:
                return calculate_hours(entry.get("start", ""), entry.get("end", ""))
            except Exception:
                return 0
        try:
            return float(hours_raw)
        except Exception:
            return 0

    def _calculate_week_hours(self, day_key):
        try:
            current_day = datetime.strptime(day_key, DATE_FORMAT).date()
        except ValueError:
            return 0.0

        start_of_week = current_day - timedelta(days=current_day.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        total = 0.0
        for entry_day, entry_list in self.entries.items():
            try:
                entry_date = datetime.strptime(entry_day, DATE_FORMAT).date()
            except ValueError:
                continue
            if not (start_of_week <= entry_date <= end_of_week):
                continue
            for entry in entry_list:
                total += self._entry_hours(entry)
        return total

    def _toggle_update_button(self, show):
        if show:
            if not self.update_btn.winfo_ismapped():
                self.update_btn.grid()
        else:
            if self.update_btn.winfo_ismapped():
                self.update_btn.grid_remove()

    def toggle_time_mode(self):
        new_mode = "duration" if self.time_mode.get() == "range" else "range"
        self.time_mode.set(new_mode)
        if new_mode == "duration":
            self.range_frame.grid_remove()
            self.duration_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
            self.mode_btn.configure(text="Modus: Zeitspanne")
        else:
            self.duration_frame.grid_remove()
            self.range_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
            self.hours_var.set("")
            self.mode_btn.configure(text="Modus: Stunden")

        self._apply_time_mode()

    def _apply_time_mode(self):
        # Already handled by toggle logic, just clearing data if needed
        if self.time_mode.get() == "range":
             if not self.start_var.get():
                self._set_default_times()

    def toggle_timer(self):
        if self.timer_start is None:
            # Start timer
            self.timer_start = datetime.now()
            self.start_var.set(self.timer_start.strftime(TIME_FORMAT))
            self.timer_btn.configure(text="Timer beenden", fg_color="#ef4444", hover_color="#dc2626")
            self.time_mode.set("range")
            self._apply_time_mode()
            self.range_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
            self.duration_frame.grid_remove()
            self.mode_btn.configure(text="Modus: Stunden")
            self.abort_btn.grid(row=0, column=2, padx=15)
            self.update_timer_display()
        else:
            # Stop timer
            end_time = datetime.now()
            self.end_var.set(end_time.strftime(TIME_FORMAT))

            try:
                self._prepare_entry()
            except ValueError as exc:
                messagebox.showerror("Ungültige Eingabe", f"Eintrag konnte nicht gespeichert werden: {exc}\nBitte Felder korrigieren und erneut Timer beenden klicken.")
                return

            self.add_entry()
            self.abort_timer()

    def abort_timer(self):
        self.timer_start = None
        self.timer_btn.configure(text="Timer starten", fg_color=["#3B8ED0", "#1F6AA5"], hover_color=["#36719F", "#144870"]) # Default ctk blue
        self.abort_btn.grid_remove()
        self.timer_label.configure(text="")
        self.start_var.set("")

    def update_timer_display(self):
        if self.timer_start is None:
            return

        now = datetime.now()
        diff = now - self.timer_start
        total_seconds = int(diff.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        self.timer_label.configure(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        self.after(1000, self.update_timer_display)

    def _load_icon(self):
        try:
            self.iconbitmap(str(ICON_FILE))
            return None # iconbitmap doesn't return an image object
        except Exception:
            return None


def main():
    app = TimeTrackerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
