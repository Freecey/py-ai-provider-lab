import tkinter as tk
from tkinter import ttk

from .base_view import BaseView


class CompareView(BaseView):
    def __init__(self, parent, app=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._app = app

    def build(self) -> None:
        super().build()
        ttk.Label(self, text="⚖️ Comparaison", font=("", 14, "bold"), padding=8).pack(anchor="w")
        ttk.Label(self, text="Sélectionnez des entrées d'historique pour les comparer côte à côte.",
                  padding=4).pack(anchor="w")
        # Placeholder — full implementation in Phase 8
        ttk.Label(self, text="(Vue Compare — disponible en Phase 8)", foreground="gray").pack(expand=True)

    def refresh(self) -> None:
        super().refresh()
