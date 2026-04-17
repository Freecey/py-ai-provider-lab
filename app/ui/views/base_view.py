import tkinter as tk
from tkinter import ttk


class BaseView(ttk.Frame):
    """Base class for all section views."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._built = False

    def build(self) -> None:
        """Called once when the view is first shown."""
        self._built = True

    def refresh(self) -> None:
        """Called each time the view is navigated to."""
        if not self._built:
            self.build()
