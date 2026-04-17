import tkinter as tk
from tkinter import ttk

from .base_view import BaseView


class DashboardView(BaseView):
    def __init__(self, parent, app=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._app = app

    def build(self) -> None:
        super().build()
        ttk.Label(self, text="🏠 Dashboard", font=("", 14, "bold"), padding=8).pack(anchor="w")

        # Metric cards row
        self._metrics_frame = ttk.Frame(self)
        self._metrics_frame.pack(fill=tk.X, padx=8, pady=4)
        self._metric_vars: dict = {}
        for label in ("Providers", "Credentials", "Modèles", "Tests"):
            card = ttk.LabelFrame(self._metrics_frame, text=label, padding=8)
            card.pack(side=tk.LEFT, padx=4, expand=True, fill=tk.BOTH)
            var = tk.StringVar(value="—")
            self._metric_vars[label] = var
            ttk.Label(card, textvariable=var, font=("", 20, "bold")).pack()

        # Recent runs table
        ttk.Label(self, text="Derniers tests", font=("", 11, "bold"), padding=(8, 4)).pack(anchor="w")
        from app.ui.widgets.filterable_table import FilterableTable
        self._runs_table = FilterableTable(self, columns=["id", "modality", "status", "latency_ms", "created_at"])
        self._runs_table.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Recent errors
        ttk.Label(self, text="Derniers échecs", font=("", 11, "bold"), padding=(8, 4)).pack(anchor="w")
        self._errors_table = FilterableTable(self, columns=["id", "modality", "error_message", "created_at"])
        self._errors_table.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

    def refresh(self) -> None:
        super().refresh()
        try:
            from app.storage.db import get_conn
            from app.storage.repositories.provider_repo import ProviderRepository
            from app.storage.repositories.credential_repo import CredentialRepository
            from app.storage.repositories.model_repo import ModelRepository
            from app.storage.repositories.test_run_repo import TestRunRepository
            conn = get_conn()
            self._metric_vars["Providers"].set(str(len(ProviderRepository(conn).list())))
            self._metric_vars["Credentials"].set(str(len(CredentialRepository(conn).list())))
            self._metric_vars["Modèles"].set(str(len(ModelRepository(conn).list(active_only=False))))
            runs = TestRunRepository(conn).list(limit=20)
            self._metric_vars["Tests"].set(str(len(runs)))
            self._runs_table.load([r.__dict__ for r in runs[:10]])
            errors = [r for r in runs if r.status == "error"][:10]
            self._errors_table.load([r.__dict__ for r in errors])
        except Exception as e:
            pass
