import json
from datetime import datetime, date, timedelta
from pathlib import Path
import calendar
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont

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


class CalendarPicker(tk.Toplevel):
    def __init__(self, master, current_date, on_select, icon_image=None):
        super().__init__(master)
        self.title("Datum wählen")
        self.on_select = on_select
        self.selected = current_date
        self.configure(padx=10, pady=10, bg="#1e1e1e")
        self.resizable(False, False)
        if icon_image is not None:
            self.iconphoto(False, icon_image)

        self._style = ttk.Style(self)
        self._style.configure(
            "CalendarDay.TButton",
            padding=4,
        )
        self._style.configure(
            "CalendarHeader.TLabel",
            background="#1e1e1e",
            foreground="#d4d4d4",
        )
        self._style.configure(
            "SelectedWeek.TButton",
            background="#2a3f55",
            foreground="#d4d4d4",
        )
        self._style.configure(
            "SelectedWeek.TLabel",
            background="#2a3f55",
            foreground="#d4d4d4",
        )
        self._style.configure(
            "SelectedDay.TButton",
            background="#569cd6",
            foreground="#ffffff",
        )
        self._style.map(
            "SelectedDay.TButton",
            background=[("active", "#6cb8ff")],
            foreground=[("active", "#ffffff")],
        )

        self.month_var = tk.IntVar(value=current_date.month)
        self.year_var = tk.IntVar(value=current_date.year)

        header = ttk.Frame(self)
        header.pack(fill=tk.X, pady=(0, 8))

        prev_btn = ttk.Button(header, text="◀", width=3, command=self.prev_month)
        prev_btn.pack(side=tk.LEFT)

        self.month_label = ttk.Label(header, text="")
        self.month_label.pack(side=tk.LEFT, expand=True)

        next_btn = ttk.Button(header, text="▶", width=3, command=self.next_month)
        next_btn.pack(side=tk.RIGHT)

        self.days_frame = ttk.Frame(self)
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
        self.month_label.config(text=f"{month_name} {year}")

        selected_week_row = None
        if self.selected and self.selected.month == month and self.selected.year == year:
            for row_idx, week in enumerate(calendar.monthcalendar(year, month), start=1):
                if self.selected.day in week:
                    selected_week_row = row_idx
                    break

        weekdays = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        for col, name in enumerate(weekdays):
            ttk.Label(
                self.days_frame,
                text=name,
                width=3,
                anchor="center",
                style="CalendarHeader.TLabel",
            ).grid(row=0, column=col)

        for row, week in enumerate(calendar.monthcalendar(year, month), start=1):
            for col, day in enumerate(week):
                if day == 0:
                    label_style = "SelectedWeek.TLabel" if selected_week_row == row else "CalendarHeader.TLabel"
                    ttk.Label(self.days_frame, text="", width=3, style=label_style).grid(row=row, column=col)
                    continue
                style = "CalendarDay.TButton"
                day_date = date(year, month, day)
                if self.selected == day_date:
                    style = "SelectedDay.TButton"
                elif selected_week_row == row:
                    style = "SelectedWeek.TButton"
                btn = ttk.Button(
                    self.days_frame,
                    text=str(day),
                    width=3,
                    style=style,
                    command=lambda d=day: self.select_day(d),
                )
                btn.grid(row=row, column=col, padx=1, pady=1)

    def select_day(self, day):
        selected_date = date(self.year_var.get(), self.month_var.get(), day)
        self.selected = selected_date
        self.on_select(selected_date)
        self.destroy()


class PresetManager(tk.Toplevel):
    def __init__(self, master, presets, on_save, icon_image=None):
        super().__init__(master)
        self.title("Vorlagen verwalten")
        self.configure(bg="#1e1e1e", padx=10, pady=10)
        self.resizable(False, False)
        self.transient(master)
        if icon_image is not None:
            self.iconphoto(False, icon_image)
        self.protocol("WM_DELETE_WINDOW", self.save_and_close)

        self.presets = [dict(preset) for preset in presets]
        self.on_save = on_save

        ttk.Label(self, text="Vorlagen setzen PSP und Leistungsart automatisch.").pack(anchor=tk.W, pady=(0, 8))

        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "psp", "type")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        self.tree.heading("name", text="Name")
        self.tree.heading("psp", text="PSP")
        self.tree.heading("type", text="Leistungsart")
        self.tree.column("name", width=160)
        self.tree.column("psp", width=120)
        self.tree.column("type", width=160)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        form = ttk.Frame(self)
        form.pack(fill=tk.X, pady=(10, 4))

        self.name_var = tk.StringVar()
        self.psp_var = tk.StringVar()
        self.type_var = tk.StringVar()

        ttk.Label(form, text="Name:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(form, textvariable=self.name_var, width=18).grid(row=1, column=0, sticky=tk.W, padx=(0, 8))

        ttk.Label(form, text="PSP:").grid(row=0, column=1, sticky=tk.W)
        ttk.Entry(form, textvariable=self.psp_var, width=18).grid(row=1, column=1, sticky=tk.W, padx=(0, 8))

        ttk.Label(form, text="Leistungsart:").grid(row=0, column=2, sticky=tk.W)
        ttk.Entry(form, textvariable=self.type_var, width=18).grid(row=1, column=2, sticky=tk.W)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=(8, 0))

        ttk.Button(btn_frame, text="Hinzufügen/Aktualisieren", command=self.add_or_update).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Entfernen", command=self.remove_selected).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(btn_frame, text="Schließen", command=self.save_and_close).pack(side=tk.RIGHT)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.refresh_list()

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
            return
        preset = self.presets[idx]
        self.name_var.set(preset.get("name", ""))
        self.psp_var.set(preset.get("psp", ""))
        self.type_var.set(preset.get("type", ""))

    def add_or_update(self):
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
        new_preset = {"name": name, "psp": psp, "type": ltype}
        if idx is None or idx >= len(self.presets):
            self.presets.append(new_preset)
        else:
            self.presets[idx] = new_preset
        self.refresh_list()
        if idx is not None and idx < len(self.presets):
            self.tree.selection_set(str(idx))

    def remove_selected(self):
        idx = self._selected_index()
        if idx is None or idx >= len(self.presets):
            return
        self.presets.pop(idx)
        self.refresh_list()
        self.name_var.set("")
        self.psp_var.set("")
        self.type_var.set("")

    def save_and_close(self):
        self.on_save(self.presets)
        self.destroy()


class TimeTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Zeiterfassung")
        self.geometry("860x560")
        self.configure(bg="#1e1e1e")
        self.resizable(True, True)

        self.icon_image = self._load_icon()

        self.data = load_data()
        self.entries = self.data["entries"]
        self.presets = self.data["presets"]
        self.editing_index = None

        self.date_var = tk.StringVar(value=date.today().strftime(DATE_FORMAT))
        self.preset_var = tk.StringVar()
        self.psp_var = tk.StringVar()
        self.type_var = tk.StringVar()
        self.desc_var = tk.StringVar()
        self.start_var = tk.StringVar()
        self.end_var = tk.StringVar()
        self.hours_var = tk.StringVar()
        self.time_mode = tk.StringVar(value="range")

        self._set_default_times()

        self._setup_styles()
        self.build_ui()
        self.refresh_entry_list()

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        base_bg = "#1e1e1e"
        panel_bg = "#252526"
        field_bg = "#2d2d2d"
        focus_bg = "#1f3c53"
        accent = "#569cd6"
        accent_active = "#6cb8ff"
        fg = "#d4d4d4"
        self._colors = {
            "field_bg": field_bg,
            "focus_bg": focus_bg,
        }
        style.configure(
            "TFrame",
            background=base_bg,
        )
        style.configure(
            "TLabel",
            background=base_bg,
            foreground=fg,
        )
        style.configure(
            "TButton",
            background=panel_bg,
            foreground=fg,
            padding=6,
        )
        style.map(
            "TButton",
            background=[("active", accent)],
            foreground=[("active", "#ffffff")],
        )
        style.configure(
            "TEntry",
            fieldbackground=field_bg,
            foreground=fg,
            insertcolor=fg,
        )
        style.map(
            "TEntry",
            fieldbackground=[("focus", focus_bg)],
            bordercolor=[("focus", accent)],
            foreground=[("focus", fg)],
        )
        style.configure(
            "TCombobox",
            fieldbackground=field_bg,
            background=field_bg,
            foreground=fg,
            arrowcolor="#f3f3f3",
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", field_bg), ("focus", focus_bg)],
            background=[("focus", focus_bg)],
            foreground=[("readonly", fg)],
        )
        style.configure(
            "Treeview",
            background=field_bg,
            fieldbackground=field_bg,
            foreground=fg,
            rowheight=26,
            borderwidth=0,
        )
        style.map(
            "Treeview",
            background=[("selected", accent)],
            foreground=[("selected", "#ffffff")],
        )
        style.configure(
            "Treeview.Heading",
            background=panel_bg,
            foreground=fg,
            relief="flat",
        )
        style.map(
            "Treeview.Heading",
            background=[("active", accent_active)],
            foreground=[("active", "#ffffff")],
        )

    def build_ui(self):
        main_frame = ttk.Frame(self, padding=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Date selection
        date_frame = ttk.Frame(main_frame)
        date_frame.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(date_frame, text="Datum:").pack(side=tk.LEFT)
        date_entry = ttk.Entry(date_frame, width=12, textvariable=self.date_var)
        date_entry.pack(side=tk.LEFT, padx=(6, 6))

        ttk.Button(date_frame, text="Datum auswählen", command=self.open_calendar).pack(side=tk.LEFT)
        ttk.Button(date_frame, text="Heute", command=self.set_today).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(date_frame, text="Gestern", command=self.set_yesterday).pack(side=tk.LEFT, padx=(6, 0))

        self.day_display_var = tk.StringVar()
        ttk.Label(date_frame, textvariable=self.day_display_var, font=("Arial", 12, "bold")).pack(side=tk.RIGHT)

        preset_bar = ttk.Frame(main_frame)
        preset_bar.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(preset_bar, text="Vorlage:").pack(side=tk.LEFT)
        self.preset_combo = ttk.Combobox(preset_bar, textvariable=self.preset_var, width=20, state="readonly")
        self.preset_combo.pack(side=tk.LEFT, padx=(6, 6))
        self.preset_combo.bind("<<ComboboxSelected>>", lambda _evt: self.apply_selected_preset())
        ttk.Button(preset_bar, text="Anwenden", command=self.apply_selected_preset).pack(side=tk.LEFT)
        ttk.Button(preset_bar, text="Vorlagen verwalten", command=self.open_preset_manager).pack(side=tk.LEFT, padx=(6, 0))

        # Input fields
        fields_frame = ttk.Frame(main_frame)
        fields_frame.pack(fill=tk.X, pady=(0, 12))

        self.psp_combo = self._build_combobox(fields_frame, "PSP (optional):", self.psp_var)
        self.type_combo = self._build_combobox(fields_frame, "Leistungsart:", self.type_var)

        self.time_frame = ttk.Frame(fields_frame)
        self.time_frame.pack(side=tk.LEFT, padx=(0, 8), fill=tk.X, expand=True)
        self.time_frame.grid_columnconfigure(0, weight=1)

        self.range_frame = ttk.Frame(self.time_frame)
        self.range_frame.grid(row=0, column=0, sticky="w")
        ttk.Label(self.range_frame, text="Start:").grid(row=0, column=0, sticky=tk.W)
        self.start_combo = self._build_time_entry(self.range_frame, self.start_var, row=1, column=0)

        ttk.Label(self.range_frame, text="Ende:").grid(row=0, column=1, sticky=tk.W, padx=(8, 0))
        self.end_combo = self._build_time_entry(self.range_frame, self.end_var, row=1, column=1, pad_x=8)

        self.duration_frame = ttk.Frame(self.time_frame)
        ttk.Label(self.duration_frame, text="Stunden:").grid(row=0, column=0, sticky=tk.W)
        self.hours_entry = ttk.Entry(self.duration_frame, width=10, textvariable=self.hours_var)
        self.hours_entry.grid(row=1, column=0, padx=(0, 8))

        self.mode_btn = ttk.Button(self.time_frame, text="Zu Stunden wechseln", command=self.toggle_time_mode)
        self.mode_btn.grid(row=0, column=1, rowspan=2, padx=(10, 0), sticky="e")

        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(desc_frame, text="Kurzbeschreibung:").pack(anchor=tk.W)
        self.desc_combo = ttk.Combobox(desc_frame, textvariable=self.desc_var)
        self.desc_combo.pack(fill=tk.X)

        # Buttons and total hours
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 12))

        self.add_btn = ttk.Button(btn_frame, text="Eintrag hinzufügen", command=self.add_entry)
        self.add_btn.pack(side=tk.LEFT)

        self.update_btn = ttk.Button(btn_frame, text="Eintrag aktualisieren", command=self.update_entry)
        self.update_btn.pack(side=tk.LEFT, padx=(6, 0))
        self.update_btn.pack_forget()

        ttk.Button(btn_frame, text="Felder leeren", command=self.reset_form).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(btn_frame, text="Löschen", command=self.delete_entry).pack(side=tk.LEFT, padx=(6, 0))

        self.total_var = tk.StringVar(value="Summe: 0.00 h")
        ttk.Label(btn_frame, textvariable=self.total_var, font=("Arial", 12, "bold")).pack(side=tk.RIGHT)

        # Entries list
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("psp", "type", "desc", "start", "end", "hours")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="tree headings",
            height=12,
        )
        self.tree.heading("#0", text="")
        self.tree.column("#0", width=26, anchor=tk.W, minwidth=26, stretch=False)

        headings = {
            "psp": "PSP",
            "type": "Leistungsart",
            "desc": "Beschreibung",
            "start": "Start",
            "end": "Ende",
            "hours": "Stunden",
        }
        for col, title in headings.items():
            self.tree.heading(col, text=title)
            width = 140
            if col == "hours":
                width = 110
            elif col == "desc":
                width = 200
            self.tree.column(col, width=width, anchor=tk.CENTER, minwidth=80)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self.on_select_entry)
        self.tree.bind("<Control-c>", self.copy_selection)
        self.tree.bind("<Control-C>", self.copy_selection)

        self.update_combobox_values()
        self.desc_combo["values"] = []
        self._apply_time_mode()

    def _build_combobox(self, parent, label, variable):
        frame = ttk.Frame(parent)
        frame.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(frame, text=label).pack(anchor=tk.W)
        combo = ttk.Combobox(frame, textvariable=variable, width=18)
        combo.pack()
        return combo

    def _build_time_entry(self, parent, variable, row=0, column=0, pad_x=0):
        combo = ttk.Combobox(
            parent,
            width=12,
            textvariable=variable,
            values=self._time_options(),
        )
        combo.configure(postcommand=lambda c=combo: self._scroll_time_to_current(c))
        combo.grid(row=row, column=column, padx=(pad_x, 0))
        return combo

    def _scroll_time_to_current(self, combo):
        values = combo["values"]
        if not values:
            return
        target_value = combo.get().strip()
        now_value = datetime.now().strftime(TIME_FORMAT)
        if target_value not in values:
            target_value = now_value if now_value in values else ""
        if target_value:
            try:
                combo.current(values.index(target_value))
            except ValueError:
                pass

    @staticmethod
    def _time_options():
        times = []
        current = datetime.strptime("00:00", TIME_FORMAT)
        end_time = datetime.strptime("23:00", TIME_FORMAT)
        while current <= end_time:
            times.append(current.strftime(TIME_FORMAT))
            current += timedelta(hours=1)
        return times

    def _set_default_times(self):
        now_str = datetime.now().strftime(TIME_FORMAT)
        self.start_var.set(now_str)
        self.end_var.set(now_str)
        self.hours_var.set("")

    def open_calendar(self):
        current = self.current_date_value()
        CalendarPicker(self, current, self.set_selected_date, self.icon_image)

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
        self.psp_combo["values"] = collect_recent_values(self.entries, "psp")
        self.type_combo["values"] = collect_recent_values(self.entries, "type")
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
        self.desc_combo["values"] = desc_values

    def _preset_names(self):
        names = []
        for preset in self.presets:
            name = preset.get("name")
            if name:
                names.append(name)
        return names

    def _update_preset_values(self):
        names = self._preset_names()
        self.preset_combo["values"] = names
        current = self.preset_var.get()
        if current and current not in names:
            self.preset_var.set("")

    def apply_selected_preset(self):
        selected_name = self.preset_var.get()
        for preset in self.presets:
            if preset.get("name") == selected_name:
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
                values=(psp, ltype, desc, "—", "—", f"{group_hours:.2f}"),
                open=False,
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
                        entry.get("start", ""),
                        entry.get("end", ""),
                        f"{hours:.2f}",
                    ),
                )
        self._auto_size_columns()
        self.total_var.set(f"Summe: {total_hours:.2f} h")

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

        psp, ltype, desc, _, _, hours = values
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
            "",  # Z
            "",  # S.
            ltype,
            psp,
            "",  # Bezeichnung (wird separat gesetzt)
            "",  # zweite Bezeichnung (optional)
            "",  # ME (nicht benötigt)
            "",  # Summe (wird automatisch berechnet)
            *day_hours,
        ]

        text = "\t".join(columns)

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
        formatted = day_date.strftime("%d.%m")
        self.day_display_var.set(f"{weekday} {formatted}")

    def _auto_size_columns(self):
        font = tkfont.nametofont("TkDefaultFont")
        padding = 30
        for col in self.tree["columns"]:
            heading_text = self.tree.heading(col).get("text", "")
            max_width = font.measure(heading_text)
            stack = list(self.tree.get_children(""))
            while stack:
                item = stack.pop()
                cell_text = self.tree.set(item, col)
                max_width = max(max_width, font.measure(cell_text))
                stack.extend(self.tree.get_children(item))
            self.tree.column(col, width=max(80, min(max_width + padding, 400)))

    def _group_entries(self, entries):
        groups = {}
        for idx, entry in enumerate(entries):
            psp = entry.get("psp", "")
            ltype = entry.get("type", "")
            desc = entry.get("desc", "")
            key = (psp, ltype, desc)
            hours_raw = entry.get("hours")
            if hours_raw is None:
                try:
                    hours = calculate_hours(entry.get("start", ""), entry.get("end", ""))
                except Exception:
                    hours = 0
            else:
                try:
                    hours = float(hours_raw)
                except Exception:
                    hours = 0
            if key not in groups:
                groups[key] = []
            groups[key].append((idx, entry, hours))

        return list(groups.items())

    def _toggle_update_button(self, show):
        if show:
            if not self.update_btn.winfo_ismapped():
                self.update_btn.pack(side=tk.LEFT, padx=(6, 0))
        else:
            if self.update_btn.winfo_ismapped():
                self.update_btn.pack_forget()

    def toggle_time_mode(self):
        new_mode = "duration" if self.time_mode.get() == "range" else "range"
        self.time_mode.set(new_mode)
        if new_mode == "duration":
            self.hours_var.set(self.hours_var.get() or "1.0")
        else:
            if not self.start_var.get():
                self._set_default_times()
        self._apply_time_mode()

    def _apply_time_mode(self):
        if self.time_mode.get() == "duration":
            self.range_frame.grid_remove()
            self.duration_frame.grid(row=0, column=0, sticky="w")
            self.hours_entry.configure(state="normal")
            self.mode_btn.configure(text="Zu Start/Ende wechseln")
        else:
            self.duration_frame.grid_remove()
            self.range_frame.grid(row=0, column=0, sticky="w")
            self.hours_var.set("")
            self.hours_entry.configure(state="disabled")
            self.mode_btn.configure(text="Zu Stunden wechseln")

    def _load_icon(self):
        try:
            self.iconbitmap(str(ICON_FILE))
        except Exception:
            return None


def main():
    app = TimeTrackerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
    