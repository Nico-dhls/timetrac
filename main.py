import json
from datetime import datetime, date, timedelta
from pathlib import Path
import calendar
import tkinter as tk
from tkinter import ttk, messagebox

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
        self.configure(padx=10, pady=10, bg="#121212")
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
        self.configure(bg="#121212")
        self.resizable(True, True)

        self.data = load_data()
        self.editing_index = None

        self.date_var = tk.StringVar(value=date.today().strftime(DATE_FORMAT))
        self.psp_var = tk.StringVar()
        self.type_var = tk.StringVar()
        self.desc_var = tk.StringVar()
        self.start_var = tk.StringVar()
        self.end_var = tk.StringVar()

        self._setup_styles()
        self.build_ui()
        self.refresh_entry_list()

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        base_bg = "#121212"
        field_bg = "#1f1f1f"
        accent = "#3f51b5"
        fg = "#e0e0e0"
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
            background=field_bg,
            foreground=fg,
            padding=6,
        )
        style.map("TButton", background=[("active", accent)])
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
            background=field_bg,
            foreground=fg,
            relief="flat",
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

        # Input fields
        fields_frame = ttk.Frame(main_frame)
        fields_frame.pack(fill=tk.X, pady=(0, 12))

        self.psp_combo = self._build_combobox(fields_frame, "PSP (optional):", self.psp_var)
        self.type_combo = self._build_combobox(fields_frame, "Leistungsart:", self.type_var)
        self._build_time_entry(fields_frame, "Start:", self.start_var)
        self._build_time_entry(fields_frame, "End:", self.end_var)

        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(desc_frame, text="Kurzbeschreibung:").pack(anchor=tk.W)
        ttk.Entry(desc_frame, textvariable=self.desc_var).pack(fill=tk.X)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 12))

        self.save_btn = ttk.Button(btn_frame, text="Add Entry", command=self.save_entry)
        self.save_btn.pack(side=tk.LEFT)

        ttk.Button(btn_frame, text="Clear", command=self.reset_form).pack(side=tk.LEFT, padx=(6, 0))

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

    def _build_time_entry(self, parent, label, variable):
        frame = ttk.Frame(parent)
        frame.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(frame, text=label).pack(anchor=tk.W)
        ttk.Combobox(frame, width=12, textvariable=variable, values=self._time_options()).pack()

    @staticmethod
    def _time_options():
        times = []
        current = datetime.strptime("00:00", TIME_FORMAT)
        end_time = datetime.strptime("23:59", TIME_FORMAT)
        while current <= end_time:
            times.append(current.strftime(TIME_FORMAT))
            current += timedelta(minutes=15)
        return times

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

        if not ltype or not start or not end:
            raise ValueError("Leistungsart, Start, and End are required")

        try:
            calculate_hours(start, end)
        except Exception as exc:
            raise ValueError(str(exc)) from exc

        try:
            selected_date = datetime.strptime(self.date_var.get(), DATE_FORMAT).date()
        except ValueError as exc:
            raise ValueError("Date must be in YYYY-MM-DD format") from exc

        return selected_date.strftime(DATE_FORMAT), psp, ltype, desc, start, end

    def save_entry(self):
        try:
            day_key, psp, ltype, desc, start, end = self.validate_fields()
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        entries = ensure_date_bucket(self.data, day_key)
        entry = {"psp": psp, "type": ltype, "desc": desc, "start": start, "end": end}

        if self.editing_index is None:
            entries.append(entry)
        else:
            entries[self.editing_index] = entry

        save_data(self.data)
        self.update_combobox_values()
        self.refresh_entry_list()
        self.reset_form()

    def reset_form(self):
        self.psp_var.set("")
        self.type_var.set("")
        self.desc_var.set("")
        self.start_var.set("")
        self.end_var.set("")
        self.editing_index = None
        self.save_btn.config(text="Add Entry")
        self.tree.selection_remove(self.tree.selection())

    def refresh_entry_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        day_key = self.date_var.get().strip()
        entries = self.data.get(day_key, [])
        total_hours = 0.0
        for idx, entry in enumerate(entries):
            try:
                hours = calculate_hours(entry["start"], entry["end"])
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
        self.start_var.set(entry.get("start", ""))
        self.end_var.set(entry.get("end", ""))
        self.editing_index = idx
        self.save_btn.config(text="Update Entry")


def main():
    app = TimeTrackerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
