import tkinter as tk
from tkinter import ttk


class SecretField(ttk.Frame):
    """Entry that hides content by default, with a reveal toggle."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._var = tk.StringVar()
        self._shown = False
        self._entry = ttk.Entry(self, textvariable=self._var, show="•", width=30)
        self._btn = ttk.Button(self, text="👁", width=3, command=self._toggle)
        self._entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._btn.pack(side=tk.LEFT)

    def _toggle(self) -> None:
        self._shown = not self._shown
        self._entry.configure(show="" if self._shown else "•")
        self._btn.configure(text="🙈" if self._shown else "👁")

    def get(self) -> str:
        return self._var.get()

    def set(self, value: str) -> None:
        self._var.set(value)
