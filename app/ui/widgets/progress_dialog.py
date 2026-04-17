import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class ProgressDialog(tk.Toplevel):
    def __init__(self, parent, title: str = "En cours...",
                 on_cancel: Optional[Callable] = None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.grab_set()
        self._cancelled = False
        self._on_cancel = on_cancel

        ttk.Label(self, text=title, padding=10).pack()
        self._bar = ttk.Progressbar(self, mode="indeterminate", length=300)
        self._bar.pack(padx=20, pady=10)
        self._bar.start(10)

        self._status_var = tk.StringVar(value="Initialisation...")
        ttk.Label(self, textvariable=self._status_var).pack(padx=20, pady=2)

        if on_cancel:
            ttk.Button(self, text="Annuler", command=self._cancel).pack(pady=8)

        self.protocol("WM_DELETE_WINDOW", self._cancel if on_cancel else lambda: None)

    def set_status(self, text: str) -> None:
        self._status_var.set(text)

    def _cancel(self) -> None:
        self._cancelled = True
        if self._on_cancel:
            self._on_cancel()
        self.close()

    def close(self) -> None:
        self._bar.stop()
        self.grab_release()
        self.destroy()

    @property
    def cancelled(self) -> bool:
        return self._cancelled
