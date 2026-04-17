import queue
import tkinter as tk
from tkinter import ttk
from typing import Optional

from app.config.constants import APP_NAME, APP_VERSION
from app.utils.logger import get_logger

logger = get_logger("ui.app_window")

_NAV_SECTIONS = [
    ("🏠 Dashboard", "dashboard"),
    ("🔌 Providers", "providers"),
    ("🔑 Credentials", "credentials"),
    ("🤖 Models", "models"),
    ("🧪 Test Lab", "testlab"),
    ("📜 History", "history"),
    ("⚖️ Compare", "compare"),
    ("⚙️ Settings", "settings"),
]


class AppWindow:
    def __init__(self):
        self._root = tk.Tk()
        self._root.title(f"{APP_NAME} v{APP_VERSION}")
        self._root.geometry("1200x750")
        self._root.minsize(800, 500)
        self._views: dict = {}
        self._current: Optional[str] = None
        self._cb_queue: queue.Queue = queue.Queue()

        self._build()
        self._navigate("dashboard")
        self._root.after(100, self._process_callbacks)

    def _build(self) -> None:
        self._root.columnconfigure(1, weight=1)
        self._root.rowconfigure(0, weight=1)

        # Sidebar
        self._sidebar = ttk.Frame(self._root, width=160, relief="sunken")
        self._sidebar.grid(row=0, column=0, sticky="nsw", padx=0, pady=0)
        self._sidebar.grid_propagate(False)
        self._build_sidebar()

        # Main frame
        self._main_frame = ttk.Frame(self._root)
        self._main_frame.grid(row=0, column=1, sticky="nsew")
        self._main_frame.grid_rowconfigure(0, weight=1)
        self._main_frame.grid_columnconfigure(0, weight=1)

        # Log panel (collapsible)
        self._log_visible = tk.BooleanVar(value=False)
        self._log_frame = ttk.LabelFrame(self._root, text="Logs")
        self._log_text: Optional[tk.Text] = None

        # Status bar
        self._status_var = tk.StringVar(value="Prêt")
        ttk.Label(self._root, textvariable=self._status_var, relief="sunken",
                  anchor="w", padding=2).grid(row=1, column=0, columnspan=2, sticky="ew")

    def _build_sidebar(self) -> None:
        ttk.Label(self._sidebar, text=APP_NAME, font=("", 10, "bold"),
                  wraplength=140, justify="center", padding=8).pack(fill=tk.X)
        ttk.Separator(self._sidebar).pack(fill=tk.X)
        self._nav_buttons: dict[str, ttk.Button] = {}
        for label, key in _NAV_SECTIONS:
            btn = ttk.Button(self._sidebar, text=label, width=18,
                             command=lambda k=key: self._navigate(k))
            btn.pack(fill=tk.X, padx=4, pady=2)
            self._nav_buttons[key] = btn

        ttk.Separator(self._sidebar).pack(fill=tk.X, pady=8)
        ttk.Button(self._sidebar, text="📋 Logs", width=18,
                   command=self._toggle_logs).pack(fill=tk.X, padx=4)

    def _navigate(self, section: str) -> None:
        # Hide current view
        if self._current and self._current in self._views:
            self._views[self._current].grid_remove()

        # Update button style
        for k, btn in self._nav_buttons.items():
            btn.state(["!pressed"])
        if section in self._nav_buttons:
            self._nav_buttons[section].state(["pressed"])

        # Lazy-load view
        if section not in self._views:
            self._views[section] = self._create_view(section)

        view = self._views[section]
        view.grid(row=0, column=0, sticky="nsew")
        view.refresh()
        self._current = section
        self.set_status(f"Section : {section}")

    def _create_view(self, section: str):
        from app.ui.views import (
            dashboard, providers, credentials, models,
            testlab, history, compare, settings,
        )
        factories = {
            "dashboard": dashboard.DashboardView,
            "providers": providers.ProvidersView,
            "credentials": credentials.CredentialsView,
            "models": models.ModelsView,
            "testlab": testlab.TestLabView,
            "history": history.HistoryView,
            "compare": compare.CompareView,
            "settings": settings.SettingsView,
        }
        cls = factories.get(section)
        if cls:
            return cls(self._main_frame, app=self)
        # Fallback stub
        frame = ttk.Frame(self._main_frame)
        ttk.Label(frame, text=f"Vue '{section}' — à implémenter", font=("", 14)).pack(expand=True)
        return frame

    def _toggle_logs(self) -> None:
        if self._log_visible.get():
            self._log_frame.grid_remove()
            self._log_visible.set(False)
        else:
            if self._log_text is None:
                self._build_log_panel()
            self._log_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
            self._log_visible.set(True)

    def _build_log_panel(self) -> None:
        self._log_text = tk.Text(self._log_frame, height=8, wrap="word",
                                 state="disabled", background="#1e1e1e", foreground="#d4d4d4")
        sb = ttk.Scrollbar(self._log_frame, command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=sb.set)
        self._log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._log_frame.grid(row=2, column=0, columnspan=2, sticky="ew")

    def log(self, message: str) -> None:
        if self._log_text:
            self._log_text.configure(state="normal")
            self._log_text.insert("end", message + "\n")
            self._log_text.see("end")
            self._log_text.configure(state="disabled")

    def set_status(self, message: str) -> None:
        self._status_var.set(message)

    def schedule(self, callback) -> None:
        """Schedule a callback to run in the main thread (from background threads)."""
        self._cb_queue.put(callback)

    def _process_callbacks(self) -> None:
        try:
            while True:
                cb = self._cb_queue.get_nowait()
                cb()
        except queue.Empty:
            pass
        self._root.after(50, self._process_callbacks)

    def run(self) -> None:
        self._root.mainloop()
