import json
from datetime import datetime, date, timedelta
from pathlib import Path
import calendar
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont

DATA_FILE = Path("time_entries.json")
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"
MAX_RECENTS = 10


def load_data():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return {}


def save_data(data):
    DATA_FILE.write_text(json.dumps(data, indent=2))


def ensure_date_bucket(data, day_key):
    if day_key not in data:
        data[day_key] = []
    return data[day_key]


def parse_time(value):
    return datetime.strptime(value, TIME_FORMAT)


def calculate_hours(start_value, end_value):
    start_time = parse_time(start_value)
    end_time = parse_time(end_value)
    if end_time <= start_time:
        raise ValueError("End time must be after start time")
    return (end_time - start_time).total_seconds() / 3600


def collect_recent_values(data, field):
    values = []
    for day in sorted(data.keys(), reverse=True):
        for entry in reversed(data[day]):
            value = entry.get(field, "")
            if value and value not in values:
                values.append(value)
            if len(values) >= MAX_RECENTS:
                return values
    return values


class CalendarPicker(tk.Toplevel):
    def __init__(self, master, current_date, on_select):
        super().__init__(master)
        self.title("Select Date")
        self.on_select = on_select
        self.selected = current_date
        self.configure(padx=10, pady=10, bg="#1e1e1e")
        self.resizable(False, False)

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
        month_name = calendar.month_name[month]
        self.month_label.config(text=f"{month_name} {year}")

        weekdays = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for col, name in enumerate(weekdays):
            ttk.Label(self.days_frame, text=name, width=3, anchor="center").grid(row=0, column=col)

        for row, week in enumerate(calendar.monthcalendar(year, month), start=1):
            for col, day in enumerate(week):
                if day == 0:
                    ttk.Label(self.days_frame, text="", width=3).grid(row=row, column=col)
                    continue
                btn = ttk.Button(
                    self.days_frame,
                    text=str(day),
                    width=3,
                    command=lambda d=day: self.select_day(d),
                )
                btn.grid(row=row, column=col, padx=1, pady=1)

    def select_day(self, day):
        selected_date = date(self.year_var.get(), self.month_var.get(), day)
        self.on_select(selected_date)
        self.destroy()


class TimeTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Time Tracker")
        self.geometry("860x560")
        self.configure(bg="#1e1e1e")
        self.resizable(True, True)

        self.data = load_data()
        self.editing_index = None

        self.date_var = tk.StringVar(value=date.today().strftime(DATE_FORMAT))
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
        accent = "#569cd6"
        accent_active = "#6cb8ff"
        fg = "#d4d4d4"
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
        style.configure(
            "TCombobox",
            fieldbackground=field_bg,
            background=field_bg,
            foreground=fg,
            arrowcolor="#f3f3f3",
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", field_bg)],
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

        ttk.Label(date_frame, text="Date:").pack(side=tk.LEFT)
        date_entry = ttk.Entry(date_frame, width=12, textvariable=self.date_var)
        date_entry.pack(side=tk.LEFT, padx=(6, 6))

        ttk.Button(date_frame, text="Pick Date", command=self.open_calendar).pack(side=tk.LEFT)
        ttk.Button(date_frame, text="Today", command=self.set_today).pack(side=tk.LEFT, padx=(6, 0))

        self.day_display_var = tk.StringVar()
        ttk.Label(date_frame, textvariable=self.day_display_var, font=("Arial", 12, "bold")).pack(side=tk.RIGHT)

        # Input fields
        fields_frame = ttk.Frame(main_frame)
        fields_frame.pack(fill=tk.X, pady=(0, 12))

        self.psp_combo = self._build_combobox(fields_frame, "PSP (optional):", self.psp_var)
        self.type_combo = self._build_combobox(fields_frame, "Leistungsart:", self.type_var)
        self.time_frame = ttk.Frame(fields_frame)
        self.time_frame.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(self.time_frame, text="Start:").grid(row=0, column=0, sticky=tk.W)
        self.start_combo = self._build_time_entry(self.time_frame, self.start_var, row=1, column=0)

        ttk.Label(self.time_frame, text="End:").grid(row=0, column=1, sticky=tk.W, padx=(8, 0))
        self.end_combo = self._build_time_entry(self.time_frame, self.end_var, row=1, column=1, pad_x=8)

        ttk.Label(self.time_frame, text="Stunden:").grid(row=0, column=2, sticky=tk.W, padx=(8, 0))
        self.hours_entry = ttk.Entry(self.time_frame, width=10, textvariable=self.hours_var, state="disabled")
        self.hours_entry.grid(row=1, column=2, padx=(8, 0))

        self.mode_btn = ttk.Button(self.time_frame, text="Zu Stunden wechseln", command=self.toggle_time_mode)
        self.mode_btn.grid(row=1, column=3, padx=(10, 0))

        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(desc_frame, text="Kurzbeschreibung:").pack(anchor=tk.W)
        ttk.Entry(desc_frame, textvariable=self.desc_var).pack(fill=tk.X)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 12))

        self.add_btn = ttk.Button(btn_frame, text="Add Entry", command=self.add_entry)
        self.add_btn.pack(side=tk.LEFT)

        self.update_btn = ttk.Button(btn_frame, text="Update Entry", command=self.update_entry)
        self.update_btn.pack(side=tk.LEFT, padx=(6, 0))
        self.update_btn.pack_forget()

        ttk.Button(btn_frame, text="Clear", command=self.reset_form).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(btn_frame, text="Delete", command=self.delete_entry).pack(side=tk.LEFT, padx=(6, 0))

        # Entries list
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("psp", "type", "desc", "start", "end", "hours")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=12,
        )
        headings = {
            "psp": "PSP",
            "type": "Leistungsart",
            "desc": "Beschreibung",
            "start": "Start",
            "end": "End",
            "hours": "Hours",
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

        # Total hours
        self.total_var = tk.StringVar(value="Total: 0.00 h")
        ttk.Label(main_frame, textvariable=self.total_var, font=("Arial", 12, "bold")).pack(anchor=tk.E, pady=(8, 0))

        self.update_combobox_values()

    def _build_combobox(self, parent, label, variable):
        frame = ttk.Frame(parent)
        frame.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(frame, text=label).pack(anchor=tk.W)
        combo = ttk.Combobox(frame, textvariable=variable, width=18)
        combo.pack()
        return combo

    def _build_time_entry(self, parent, variable, row=0, column=0, pad_x=0):
        combo = ttk.Combobox(parent, width=12, textvariable=variable, values=self._time_options())
        combo.grid(row=row, column=column, padx=(pad_x, 0))
        return combo

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
        CalendarPicker(self, current, self.set_selected_date)

    def set_selected_date(self, selected):
        self.date_var.set(selected.strftime(DATE_FORMAT))
        self.refresh_entry_list()

    def set_today(self):
        self.set_selected_date(date.today())

    def current_date_value(self):
        try:
            return datetime.strptime(self.date_var.get(), DATE_FORMAT).date()
        except ValueError:
            return date.today()

    def update_combobox_values(self):
        self.psp_combo["values"] = collect_recent_values(self.data, "psp")
        self.type_combo["values"] = collect_recent_values(self.data, "type")

    def validate_fields(self):
        psp = self.psp_var.get().strip()
        ltype = self.type_var.get().strip()
        desc = self.desc_var.get().strip()
        start = self.start_var.get().strip()
        end = self.end_var.get().strip()
        hours_value = self.hours_var.get().strip()

        if self.time_mode.get() == "range":
            if not ltype or not start or not end:
                raise ValueError("Leistungsart, Start, and End are required")
            try:
                hours = calculate_hours(start, end)
            except Exception as exc:
                raise ValueError(str(exc)) from exc
        else:
            if not ltype or not hours_value:
                raise ValueError("Leistungsart and Stunden are required")
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
            raise ValueError("Date must be in YYYY-MM-DD format") from exc

        return selected_date.strftime(DATE_FORMAT), psp, ltype, desc, start, end, hours

    def add_entry(self):
        try:
            day_key, entry = self._prepare_entry()
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        entries = ensure_date_bucket(self.data, day_key)
        entries.append(entry)

        save_data(self.data)
        self.update_combobox_values()
        self.refresh_entry_list()
        self.reset_form()

    def update_entry(self):
        if self.editing_index is None:
            messagebox.showinfo("Update entry", "Bitte wähle zuerst einen Eintrag aus.")
            return

        try:
            day_key, entry = self._prepare_entry()
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        entries = ensure_date_bucket(self.data, day_key)
        if self.editing_index >= len(entries):
            messagebox.showinfo("Update entry", "Der ausgewählte Eintrag existiert nicht mehr.")
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
        entries = self.data.get(day_key, [])
        total_hours = 0.0
        for idx, entry in enumerate(entries):
            hours = entry.get("hours")
            if hours is None:
                try:
                    hours = calculate_hours(entry.get("start", ""), entry.get("end", ""))
                except Exception:
                    hours = 0
            else:
                try:
                    hours = float(hours)
                except Exception:
                    hours = 0
            total_hours += hours
            self.tree.insert("", "end", iid=str(idx), values=(
                entry.get("psp", ""),
                entry.get("type", ""),
                entry.get("desc", ""),
                entry.get("start", ""),
                entry.get("end", ""),
                f"{hours:.2f}",
            ))
        self._auto_size_columns()
        self.total_var.set(f"Total: {total_hours:.2f} h")

    def on_select_entry(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        idx = int(selection[0])
        day_key = self.date_var.get().strip()
        entries = self.data.get(day_key, [])
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

    def delete_entry(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Delete entry", "Please select an entry to delete.")
            return
        idx = int(selection[0])
        day_key = self.date_var.get().strip()
        entries = self.data.get(day_key, [])
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
            for item in self.tree.get_children(""):
                cell_text = self.tree.set(item, col)
                max_width = max(max_width, font.measure(cell_text))
            self.tree.column(col, width=max(80, min(max_width + padding, 400)))

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
            self.start_combo.configure(state="disabled")
            self.end_combo.configure(state="disabled")
            self.hours_entry.configure(state="normal")
            self.mode_btn.configure(text="Zu Start/Ende wechseln")
        else:
            self.start_combo.configure(state="normal")
            self.end_combo.configure(state="normal")
            self.hours_entry.configure(state="disabled")
            self.hours_var.set("")
            self.mode_btn.configure(text="Zu Stunden wechseln")


def main():
    app = TimeTrackerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
