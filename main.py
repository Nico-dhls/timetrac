import json
from datetime import datetime, date, timedelta
from pathlib import Path
import calendar
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont


class Tooltip:
    def __init__(self, widget, text, bg="#0f1629", fg="#e6e8ef"):
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
            font=("Segoe UI", 9),
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
        shared_bg = "#101a2e"
        self._style.configure("Calendar.TFrame", background=shared_bg)
        self._style.configure(
            "CalendarDay.TButton",
            padding=4,
            background="#1b2b44",
            foreground="#e6e8ef",
            bordercolor="#1b2b44",
        )
        self._style.map(
            "CalendarDay.TButton",
            background=[("active", "#233756")],
            foreground=[("active", "#ffffff")],
        )
        self._style.configure(
            "CalendarHeader.TLabel",
            background=shared_bg,
            foreground="#d4d4d4",
        )
        self._style.configure(
            "CalendarMonth.TLabel",
            background=shared_bg,
            foreground="#e6e8ef",
            font=("Segoe UI", 10, "bold"),
        )
        self._style.configure(
            "SelectedWeek.TButton",
            background="#2a3f55",
            foreground="#d4d4d4",
            bordercolor="#2a3f55",
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
            bordercolor="#569cd6",
        )
        self._style.map(
            "SelectedDay.TButton",
            background=[("active", "#6cb8ff")],
            foreground=[("active", "#ffffff")],
        )

        self.month_var = tk.IntVar(value=current_date.month)
        self.year_var = tk.IntVar(value=current_date.year)

        header = ttk.Frame(self, style="Calendar.TFrame")
        header.pack(fill=tk.X, pady=(0, 8))

        prev_btn = ttk.Button(header, text="◀", width=3, command=self.prev_month)
        prev_btn.pack(side=tk.LEFT)

        self.month_label = ttk.Label(header, text="", style="CalendarMonth.TLabel")
        self.month_label.pack(side=tk.LEFT, expand=True)

        next_btn = ttk.Button(header, text="▶", width=3, command=self.next_month)
        next_btn.pack(side=tk.RIGHT)

        self.days_frame = ttk.Frame(self, style="Calendar.TFrame")
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

        ttk.Button(btn_frame, text="Hinzufügen", command=self.add_preset).pack(side=tk.LEFT)
        self.update_btn = ttk.Button(btn_frame, text="Aktualisieren", command=self.update_selected)
        ttk.Button(btn_frame, text="Entfernen", command=self.remove_selected).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(btn_frame, text="Schließen", command=self.save_and_close).pack(side=tk.RIGHT)

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
            self.update_btn.pack(side=tk.LEFT, padx=(6, 0))

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


class TimeTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Zeiterfassung")
        self.geometry("1480x760")
        self.minsize(1340, 700)
        self.configure(bg="#070d1c")
        self.resizable(True, True)

        self.icon_image = self._load_icon()

        self.data = load_data()
        self.entries = self.data["entries"]
        self.presets = self.data["presets"]
        self.editing_index = None
        self._calendar_window = None

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

        self._setup_styles()
        self.build_ui()
        self.refresh_entry_list()

    def _rounded_rect_image(self, fill, bg, radius=10):
        size = radius * 2 + 6
        img = tk.PhotoImage(width=size, height=size)
        img.put(bg, to=(0, 0, size, size))
        for x in range(size):
            for y in range(size):
                dx = min(x, size - x - 1)
                dy = min(y, size - y - 1)
                # inside straight edges
                if dx >= radius or dy >= radius:
                    img.put(fill, (x, y))
                    continue
                # inside rounded corners
                cx = radius - dx - 0.5
                cy = radius - dy - 0.5
                if cx * cx + cy * cy <= radius * radius:
                    img.put(fill, (x, y))
        return img

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        base_bg = "#070d1c"
        card_bg = "#0e162b"
        field_bg = "#111c33"
        focus_bg = "#1a2d4c"
        accent = "#8d7bff"
        accent_active = "#4ee0ff"
        fg = "#eef2ff"
        muted = "#9fb6de"
        border = "#1a2742"
        card_alt = "#122041"
        accent_soft = "#355ca3"
        self._colors = {
            "field_bg": field_bg,
            "focus_bg": focus_bg,
            "base": base_bg,
            "card": card_bg,
            "accent": accent,
            "accent_active": accent_active,
            "muted": muted,
            "border": border,
            "card_alt": card_alt,
            "accent_soft": accent_soft,
        }
        self._img_refs = []
        self.option_add("*Font", ("Segoe UI", 11))
        self.option_add("*TCombobox*Listbox.font", ("Segoe UI", 11))
        self.option_add("*TCombobox*Listbox.background", field_bg)
        self.option_add("*TCombobox*Listbox.foreground", fg)
        style.configure(
            "TFrame",
            background=base_bg,
        )
        style.configure(
            "Card.TFrame",
            background=card_bg,
        )
        style.configure(
            "TLabel",
            background=base_bg,
            foreground=fg,
        )
        style.configure(
            "Card.TLabel",
            background=card_bg,
            foreground=fg,
        )
        style.configure(
            "Title.TLabel",
            background=card_bg,
            foreground="#ffffff",
            font=("Segoe UI", 16, "bold"),
        )
        style.configure(
            "Subtle.TLabel",
            background=card_bg,
            foreground=muted,
            font=("Segoe UI", 10),
        )
        style.configure(
            "TButton",
            background=card_alt,
            foreground=fg,
            padding=6,
            borderwidth=0,
        )
        style.map(
            "TButton",
            background=[("active", focus_bg)],
            foreground=[("active", "#ffffff")],
        )
        style.configure(
            "Ghost.TButton",
            background=card_bg,
            foreground=fg,
            padding=5,
            borderwidth=0,
        )
        style.map(
            "Ghost.TButton",
            background=[("active", focus_bg)],
            foreground=[("active", "#ffffff")],
        )
        style.configure(
            "Accent.TButton",
            background=accent,
            foreground="#ffffff",
            padding=6,
            borderwidth=0,
        )
        style.map(
            "Accent.TButton",
            background=[("active", accent_active)],
            foreground=[("active", "#ffffff")],
        )
        toolbar_normal = self._rounded_rect_image("#4b6fb0", card_bg, radius=9)
        toolbar_hover = self._rounded_rect_image("#5e86d1", card_bg, radius=9)
        accent_img = self._rounded_rect_image(accent, card_bg, radius=7)
        accent_hover = self._rounded_rect_image(accent_active, card_bg, radius=7)
        danger_img = self._rounded_rect_image("#d14b64", card_bg, radius=7)
        danger_hover = self._rounded_rect_image("#e5677c", card_bg, radius=7)
        self._img_refs.extend(
            [toolbar_normal, toolbar_hover, accent_img, accent_hover, danger_img, danger_hover]
        )
        style.element_create(
            "ToolbarRounded.border",
            "image",
            toolbar_normal,
            ("active", toolbar_hover),
            ("pressed", toolbar_hover),
            border=10,
            sticky="nswe",
        )
        style.layout(
            "ToolbarRounded.TButton",
            [
                (
                    "ToolbarRounded.border",
                    {
                        "children": [
                            (
                                "Button.padding",
                                {
                                    "children": [
                                        (
                                            "Button.label",
                                            {"sticky": "nswe"},
                                        )
                                    ],
                                    "sticky": "nswe",
                                },
                            )
                        ],
                        "sticky": "nswe",
                    },
                )
            ],
        )
        style.configure(
            "ToolbarRounded.TButton",
            foreground="#f4f6fb",
            padding=6,
            background="#4b6fb0",
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
        )
        style.element_create(
            "AccentRounded.border",
            "image",
            accent_img,
            ("active", accent_hover),
            ("pressed", accent_hover),
            border=10,
            sticky="nswe",
        )
        style.layout(
            "AccentRounded.TButton",
            [
                (
                    "AccentRounded.border",
                    {
                        "children": [
                            (
                                "Button.padding",
                                {
                                    "children": [
                                        (
                                            "Button.label",
                                            {"sticky": "nswe"},
                                        )
                                    ],
                                    "sticky": "nswe",
                                },
                            )
                        ],
                        "sticky": "nswe",
                    },
                )
            ],
        )
        style.configure(
            "AccentRounded.TButton",
            foreground="#ffffff",
            padding=6,
            background=accent,
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
        )
        style.element_create(
            "DangerRounded.border",
            "image",
            danger_img,
            ("active", danger_hover),
            ("pressed", danger_hover),
            border=10,
            sticky="nswe",
        )
        style.layout(
            "DangerRounded.TButton",
            [
                (
                    "DangerRounded.border",
                    {
                        "children": [
                            (
                                "Button.padding",
                                {
                                    "children": [
                                        (
                                            "Button.label",
                                            {"sticky": "nswe"},
                                        )
                                    ],
                                    "sticky": "nswe",
                                },
                            )
                        ],
                        "sticky": "nswe",
                    },
                )
            ],
        )
        style.configure(
            "DangerRounded.TButton",
            foreground="#ffffff",
            padding=6,
            background="#d14b64",
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
        )
        style.configure(
            "TEntry",
            fieldbackground=field_bg,
            foreground=fg,
            insertcolor=fg,
            bordercolor=border,
            lightcolor=accent,
            darkcolor=border,
            padding=6,
        )
        style.map(
            "TEntry",
            fieldbackground=[("focus", focus_bg)],
            bordercolor=[("focus", accent)],
            foreground=[("focus", fg)],
        )
        style.configure(
            "Date.TEntry",
            fieldbackground="#20365d",
            foreground=fg,
            insertcolor=fg,
            bordercolor="#5f8bdc",
            lightcolor="#5f8bdc",
            darkcolor=border,
            padding=8,
        )
        style.map(
            "Date.TEntry",
            fieldbackground=[("focus", "#294a7c")],
            bordercolor=[("focus", accent_active)],
        )
        style.configure(
            "TCombobox",
            fieldbackground=field_bg,
            background=field_bg,
            foreground=fg,
            arrowcolor="#f3f3f3",
            bordercolor=border,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", field_bg), ("focus", focus_bg)],
            background=[("focus", focus_bg)],
            foreground=[("readonly", fg)],
        )
        style.configure(
            "Modern.Treeview",
            background=card_bg,
            fieldbackground=card_bg,
            foreground=fg,
            rowheight=30,
            borderwidth=0,
            highlightthickness=0,
        )
        style.map(
            "Modern.Treeview",
            background=[("selected", "#1f3d69")],
            foreground=[("selected", "#ffffff")],
        )
        style.configure(
            "Modern.Treeview.Heading",
            background=card_alt,
            foreground=fg,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padding=8,
        )
        style.map(
            "Modern.Treeview.Heading",
            background=[("active", focus_bg)],
            foreground=[("active", "#ffffff")],
        )

    def _card(self, parent):
        frame = tk.Frame(
            parent,
            bg=self._colors["card"],
            bd=0,
            highlightthickness=1,
            highlightbackground=self._colors["accent_soft"],
            highlightcolor=self._colors["accent_soft"],
            padx=16,
            pady=16,
        )
        return frame

    def build_ui(self):
        main_frame = tk.Frame(self, bg=self._colors["base"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=18)
        main_frame.grid_columnconfigure(0, weight=11, uniform="cards")
        main_frame.grid_columnconfigure(1, weight=17, uniform="cards")

        form_card = self._card(main_frame)
        form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        form_card.grid_columnconfigure(0, weight=1)

        ttk.Label(form_card, text="Zeiterfassung", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            form_card,
            text="Erfasse Zeiten schneller mit modernen Eingabeelementen.",
            style="Subtle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 12))

        date_frame = ttk.Frame(form_card, style="Card.TFrame")
        date_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        date_frame.grid_columnconfigure(1, weight=1)

        date_label = ttk.Label(date_frame, text="Datum:", style="Card.TLabel")
        date_label.grid(row=0, column=0, sticky="w")

        date_shell = tk.Frame(
            date_frame,
            bg="#1b2f52",
            highlightthickness=1,
            highlightbackground=self._colors["accent_soft"],
            bd=0,
        )
        date_shell.grid(row=0, column=1, padx=(10, 12), sticky="ew")
        date_shell.grid_columnconfigure(1, weight=1)

        date_icon = tk.Label(
            date_shell,
            text="📅",
            bg="#1b2f52",
            fg=self._colors["muted"],
            font=("Segoe UI", 12),
        )
        date_icon.grid(row=0, column=0, padx=(10, 6), pady=6)

        date_entry = ttk.Entry(
            date_shell,
            width=18,
            textvariable=self.date_var,
            style="Date.TEntry",
            font=("Segoe UI", 12, "bold"),
        )
        date_entry.grid(row=0, column=1, padx=(0, 12), pady=6, sticky="ew")
        date_entry.bind("<Button-1>", self.open_calendar)
        date_icon.bind("<Button-1>", self.open_calendar)

        ttk.Button(date_frame, text="Heute", style="ToolbarRounded.TButton", command=self.set_today).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(date_frame, text="Gestern", style="ToolbarRounded.TButton", command=self.set_yesterday).grid(row=0, column=3, padx=(0, 4))

        self.day_display_var = tk.StringVar()
        ttk.Label(date_frame, textvariable=self.day_display_var, style="Card.TLabel", font=("Segoe UI", 12, "bold")).grid(row=1, column=0, columnspan=3, sticky="w", pady=(8, 0))
        date_info = ttk.Label(date_frame, text="ⓘ", style="Card.TLabel", cursor="question_arrow")
        date_info.grid(row=1, column=3, padx=(8, 0), sticky="e")
        Tooltip(
            date_info,
            "Feld anklicken öffnet den Kalender – oder per Heute/Gestern springen.",
            bg=self._colors["card"],
            fg=self._colors["muted"],
        )

        preset_bar = ttk.Frame(form_card, style="Card.TFrame")
        preset_bar.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        preset_bar.grid_columnconfigure(1, weight=1)
        preset_label = ttk.Label(preset_bar, text="Vorlage:", style="Card.TLabel")
        preset_label.grid(row=0, column=0, sticky="w")
        self.preset_combo = ttk.Combobox(preset_bar, textvariable=self.preset_var, width=22, state="readonly")
        self.preset_combo.grid(row=0, column=1, padx=(8, 8), sticky="ew")
        self.preset_combo.bind("<<ComboboxSelected>>", lambda _evt: self.apply_selected_preset())
        ttk.Button(preset_bar, text="Vorlagen verwalten", style="ToolbarRounded.TButton", command=self.open_preset_manager).grid(row=0, column=2, padx=(8, 0), sticky="e")
        preset_info = ttk.Label(preset_bar, text="ⓘ", style="Card.TLabel", cursor="question_arrow")
        preset_info.grid(row=0, column=3, padx=(8, 0))
        Tooltip(
            preset_info,
            "Vorlagen füllen PSP und Leistungsart automatisch aus.",
            bg=self._colors["card"],
            fg=self._colors["muted"],
        )

        fields_frame = ttk.Frame(form_card, style="Card.TFrame")
        fields_frame.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        fields_frame.grid_columnconfigure(0, weight=1)
        fields_frame.grid_columnconfigure(1, weight=1)

        self.psp_combo = self._build_combobox(
            fields_frame,
            "PSP (optional):",
            self.psp_var,
            column=0,
            tooltip_text="Optionaler PSP-Code, um deine Buchung schneller zuzuordnen.",
        )
        self.type_combo = self._build_combobox(
            fields_frame,
            "Leistungsart:",
            self.type_var,
            column=1,
            tooltip_text="Pflichtfeld für den abrechnungsrelevanten Leistungs-Typ.",
        )

        self.time_frame = ttk.Frame(form_card, style="Card.TFrame")
        self.time_frame.grid(row=5, column=0, sticky="ew")
        self.time_frame.grid_columnconfigure(0, weight=1)

        self.range_frame = ttk.Frame(self.time_frame, style="Card.TFrame")
        self.range_frame.grid(row=0, column=0, sticky="w")
        start_label = ttk.Label(self.range_frame, text="Start:", style="Card.TLabel")
        start_label.grid(row=0, column=0, sticky=tk.W)
        self.start_combo = self._build_time_entry(self.range_frame, self.start_var, row=1, column=0)

        end_label = ttk.Label(self.range_frame, text="Ende:", style="Card.TLabel")
        end_label.grid(row=0, column=1, sticky=tk.W, padx=(8, 0))
        self.end_combo = self._build_time_entry(self.range_frame, self.end_var, row=1, column=1, pad_x=8)
        range_info = ttk.Label(self.range_frame, text="ⓘ", style="Card.TLabel", cursor="question_arrow")
        range_info.grid(row=0, column=2, sticky="w", padx=(8, 0))
        Tooltip(
            range_info,
            "Nutze Start/Ende für klassische Zeitspannen. Prüft automatisch, dass Ende nach Start liegt.",
            bg=self._colors["card"],
            fg=self._colors["muted"],
        )

        self.duration_frame = ttk.Frame(self.time_frame, style="Card.TFrame")
        hours_label = ttk.Label(self.duration_frame, text="Stunden:", style="Card.TLabel")
        hours_label.grid(row=0, column=0, sticky=tk.W)
        self.hours_entry = ttk.Entry(self.duration_frame, width=12, textvariable=self.hours_var)
        self.hours_entry.grid(row=1, column=0, padx=(0, 12))
        hours_info = ttk.Label(self.duration_frame, text="ⓘ", style="Card.TLabel", cursor="question_arrow")
        hours_info.grid(row=0, column=1, sticky="w", padx=(6, 0))
        Tooltip(
            hours_info,
            "Trage hier direkt Stunden ein, wenn du keine Start/Ende Zeiten verwenden willst.",
            bg=self._colors["card"],
            fg=self._colors["muted"],
        )

        self.mode_btn = ttk.Button(self.time_frame, text="Zu Stunden wechseln", style="ToolbarRounded.TButton", command=self.toggle_time_mode)
        self.mode_btn.grid(row=0, column=1, rowspan=2, padx=(10, 0), sticky="e")

        desc_frame = ttk.Frame(form_card, style="Card.TFrame")
        desc_frame.grid(row=6, column=0, sticky="ew", pady=(12, 4))
        desc_label = ttk.Label(desc_frame, text="Kurzbeschreibung:", style="Card.TLabel")
        desc_label.grid(row=0, column=0, sticky="w")
        desc_info = ttk.Label(desc_frame, text="ⓘ", style="Card.TLabel", cursor="question_arrow")
        desc_info.grid(row=0, column=1, sticky="w", padx=(6, 0))
        Tooltip(
            desc_info,
            "Kurzer Text für die gebuchte Tätigkeit. Häufige Einträge tauchen als Vorschlag auf.",
            bg=self._colors["card"],
            fg=self._colors["muted"],
        )
        self.desc_combo = ttk.Combobox(desc_frame, textvariable=self.desc_var)
        self.desc_combo.grid(row=1, column=0, sticky="ew")

        btn_frame = ttk.Frame(form_card, style="Card.TFrame")
        btn_frame.grid(row=7, column=0, sticky="ew", pady=(12, 0))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=1)
        btn_frame.grid_columnconfigure(3, weight=1)

        self.add_btn = ttk.Button(btn_frame, text="Eintrag hinzufügen", style="AccentRounded.TButton", command=self.add_entry)
        self.add_btn.grid(row=0, column=0, sticky="ew")

        self.update_btn = ttk.Button(btn_frame, text="Eintrag aktualisieren", style="AccentRounded.TButton", command=self.update_entry)
        self.update_btn.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self.update_btn.grid_remove()

        ttk.Button(btn_frame, text="Felder leeren", style="ToolbarRounded.TButton", command=self.reset_form).grid(row=0, column=2, sticky="ew", padx=(8, 0))
        ttk.Button(btn_frame, text="Löschen", style="DangerRounded.TButton", command=self.delete_entry).grid(row=0, column=3, sticky="ew", padx=(8, 0))

        self.timer_btn = ttk.Button(btn_frame, text="Timer starten", style="AccentRounded.TButton", command=self.toggle_timer)
        self.timer_btn.grid(row=0, column=4, sticky="ew", padx=(8, 0))

        list_card = self._card(main_frame)
        list_card.grid(row=0, column=1, sticky="nsew")
        list_card.grid_columnconfigure(0, weight=1)
        list_card.grid_rowconfigure(2, weight=1)

        ttk.Label(list_card, text="Übersicht", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(list_card, text="Gruppierte Einträge und Summen.", style="Subtle.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 10))

        tree_frame = ttk.Frame(list_card, style="Card.TFrame")
        tree_frame.grid(row=2, column=0, sticky="nsew")
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        columns = ("psp", "type", "desc", "hours")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="tree headings",
            height=17,
            style="Modern.Treeview",
        )
        self.tree.heading("#0", text="")
        self.tree.column("#0", width=24, anchor=tk.W, minwidth=24, stretch=False)

        headings = {
            "psp": "PSP",
            "type": "Leistungsart",
            "desc": "Beschreibung",
            "hours": "Stunden",
        }
        for col, title in headings.items():
            self.tree.heading(col, text=title)
            width = 200
            minwidth = 150
            if col == "hours":
                width = 210
                minwidth = 190
            elif col == "desc":
                width = 360
                minwidth = 260
            self.tree.column(col, width=width, anchor=tk.CENTER, minwidth=minwidth, stretch=True)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        totals_frame = ttk.Frame(list_card, style="Card.TFrame")
        totals_frame.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        totals_frame.grid_columnconfigure(0, weight=1)
        totals_frame.grid_columnconfigure(1, weight=1)

        self.total_var = tk.StringVar(value="Summe Tag: 0.00 h")
        ttk.Label(totals_frame, textvariable=self.total_var, style="Card.TLabel", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")

        self.week_total_var = tk.StringVar(value="Woche: 0.00 h")
        ttk.Label(totals_frame, textvariable=self.week_total_var, style="Card.TLabel", font=("Segoe UI", 12, "bold")).grid(row=0, column=1, sticky="e")

        self.tree.tag_configure("group", background=self._colors["card_alt"], foreground="#ffffff", font=("Segoe UI", 10, "bold"))

        self.tree.bind("<<TreeviewSelect>>", self.on_select_entry)
        self.tree.bind("<Control-c>", self.copy_selection)
        self.tree.bind("<Control-C>", self.copy_selection)

        self.update_combobox_values()
        self.desc_combo["values"] = []
        self._apply_time_mode()

    def _build_combobox(self, parent, label, variable, column=None, tooltip_text=None):
        frame = ttk.Frame(parent, style="Card.TFrame")
        if column is None:
            frame.pack(side=tk.LEFT, padx=(0, 8))
        else:
            frame.grid(row=0, column=column, sticky="ew", padx=(0, 10))
            frame.grid_columnconfigure(0, weight=1)
        ttk.Label(frame, text=label, style="Card.TLabel").grid(row=0, column=0, sticky="w")
        if tooltip_text:
            info = ttk.Label(frame, text="ⓘ", style="Card.TLabel", cursor="question_arrow")
            info.grid(row=0, column=1, sticky="w", padx=(6, 0))
            Tooltip(info, tooltip_text, bg=self._colors["card"], fg=self._colors["muted"])
        combo = ttk.Combobox(frame, textvariable=variable, width=20)
        combo.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        return combo

    def _build_time_entry(self, parent, variable, row=0, column=0, pad_x=0):
        combo = ttk.Combobox(
            parent,
            width=12,
            textvariable=variable,
            values=self._time_options(),
        )
        combo.configure(postcommand=lambda c=combo: self._scroll_time_to_current(c))
        combo.bind("<Button-1>", self.on_time_click)
        combo.grid(row=row, column=column, padx=(pad_x, 0))
        return combo

    def on_time_click(self, event):
        try:
            element = event.widget.identify(event.x, event.y)
            # Only auto-fill if clicking the text entry part, not the arrow button
            if element == "textarea" or (element and "textarea" in str(element)):
                now = datetime.now()
                # Round to nearest 15 minutes
                minutes = now.minute
                remainder = minutes % 15
                if remainder < 8:
                    rounded_min = minutes - remainder
                else:
                    rounded_min = minutes + (15 - remainder)

                if rounded_min == 60:
                    now = now.replace(minute=0) + timedelta(hours=1)
                else:
                    now = now.replace(minute=rounded_min)

                time_str = now.strftime(TIME_FORMAT)
                # Use after_idle to avoid conflict with default focus/click behavior
                self.after_idle(lambda: event.widget.set(time_str))
        except Exception:
            pass

    def _scroll_time_to_current(self, combo):
        values = combo["values"]
        if not values:
            return
        target_value = combo.get().strip()

        # If current text is in values, we are good - select it
        if target_value in values:
            try:
                combo.current(values.index(target_value))
            except ValueError:
                pass
            return

        # If text is empty or not in list, find closest to NOW
        now = datetime.now()
        # Convert now to minutes for comparison
        now_mins = now.hour * 60 + now.minute

        closest_index = -1
        min_diff = float('inf')

        for idx, val in enumerate(values):
            try:
                dt = datetime.strptime(val, TIME_FORMAT)
                val_mins = dt.hour * 60 + dt.minute
                diff = abs(val_mins - now_mins)
                if diff < min_diff:
                    min_diff = diff
                    closest_index = idx
            except ValueError:
                continue

        if closest_index != -1:
            try:
                combo.current(closest_index)
            except ValueError:
                pass

    @staticmethod
    def _time_options():
        times = []
        current = datetime.strptime("00:00", TIME_FORMAT)
        end_time = datetime.strptime("23:45", TIME_FORMAT)
        while current <= end_time:
            times.append(current.strftime(TIME_FORMAT))
            current += timedelta(minutes=15)
        return times

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
        picker.bind("<Destroy>", self._clear_calendar_ref)

    def _close_calendar(self):
        if self._calendar_window is not None and self._calendar_window.winfo_exists():
            self._calendar_window.destroy()
        self._calendar_window = None

    def _clear_calendar_ref(self, _event=None):
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
                values=(psp, ltype, desc, f"{group_hours:.2f}"),
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
                        f"{hours:.2f}",
                    ),
                )
        self._auto_size_columns()
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

        # Add a trailing newline so SAP treats the clipboard content as a full row
        # and advances through all columns instead of stopping after the first field.
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

    def toggle_timer(self):
        if self.timer_start is None:
            # Start timer
            self.timer_start = datetime.now()
            self.start_var.set(self.timer_start.strftime(TIME_FORMAT))
            self.timer_btn.configure(text="Timer beenden", style="DangerRounded.TButton")
            self.time_mode.set("range")
            self._apply_time_mode()
        else:
            # Stop timer
            end_time = datetime.now()
            self.end_var.set(end_time.strftime(TIME_FORMAT))

            # Try to prepare entry (validates fields)
            try:
                self._prepare_entry()
            except ValueError as exc:
                messagebox.showerror("Ungültige Eingabe", f"Eintrag konnte nicht gespeichert werden: {exc}\nBitte Felder korrigieren und erneut Timer beenden klicken.")
                return

            # If valid, add entry and reset
            self.add_entry()
            self.timer_start = None
            self.timer_btn.configure(text="Timer starten", style="AccentRounded.TButton")

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
    