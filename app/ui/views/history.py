import json
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

from .base_view import BaseView
from app.ui.widgets import FilterableTable, confirm
from app.services.history_service import HistoryService

_COLS = ["id", "modality", "status", "latency_ms", "cost_estimated", "rating", "created_at"]


class HistoryView(BaseView):
    def __init__(self, parent, app=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._app = app
        self._svc = HistoryService()
        self._selected_id: int | None = None

    def build(self) -> None:
        super().build()
        ttk.Label(self, text="📜 Historique", font=("", 14, "bold"), padding=8).pack(anchor="w")

        # Filters
        ff = ttk.Frame(self); ff.pack(fill=tk.X, padx=8, pady=2)
        ttk.Label(ff, text="Statut :").pack(side=tk.LEFT)
        self._status_var = tk.StringVar(value="Tous")
        ttk.Combobox(ff, textvariable=self._status_var, state="readonly", width=12,
                     values=["Tous", "success", "error", "pending", "cancelled"]
                     ).pack(side=tk.LEFT, padx=4)
        self._status_var.trace_add("write", lambda *_: self.refresh())

        ttk.Label(ff, text="Limite :").pack(side=tk.LEFT, padx=(8, 0))
        self._limit_var = tk.StringVar(value="50")
        ttk.Entry(ff, textvariable=self._limit_var, width=6).pack(side=tk.LEFT, padx=4)
        ttk.Button(ff, text="Chercher", command=self.refresh).pack(side=tk.LEFT)

        toolbar = ttk.Frame(self); toolbar.pack(fill=tk.X, padx=8)
        ttk.Button(toolbar, text="🗑️ Supprimer", command=self._delete).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="▶ Relancer", command=self._replay).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="⭐ Noter", command=self._rate).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📤 Exporter", command=self._export).pack(side=tk.LEFT, padx=2)

        pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        self._table = FilterableTable(pane, columns=_COLS, on_select=self._on_select)
        pane.add(self._table, weight=2)

        detail = ttk.LabelFrame(pane, text="Détail")
        pane.add(detail, weight=1)
        self._detail_text = scrolledtext.ScrolledText(detail, height=8, state="disabled", wrap="word")
        self._detail_text.pack(fill=tk.BOTH, expand=True)

    def refresh(self) -> None:
        super().refresh()
        status = self._status_var.get() if hasattr(self, "_status_var") else None
        limit = int(self._limit_var.get() or 50) if hasattr(self, "_limit_var") else 50
        runs = self._svc.list_runs(
            status=None if status == "Tous" else status,
            limit=limit,
        )
        rows = [{k: v for k, v in r.__dict__.items() if k in _COLS} for r in runs]
        self._table.load(rows)

    def _on_select(self, row: dict) -> None:
        self._selected_id = row.get("id")
        run = self._svc.get_run(self._selected_id)
        if run:
            detail = (f"Run #{run.id} — {run.modality} — {run.status}\n"
                      f"Latence: {run.latency_ms}ms | Coût: {run.cost_estimated}\n"
                      f"Paramètres: {json.dumps(run.params, indent=2)}\n\n"
                      f"Réponse:\n{(run.response_raw or '')[:2000]}")
            self._detail_text.configure(state="normal")
            self._detail_text.delete("1.0", "end")
            self._detail_text.insert("end", detail)
            self._detail_text.configure(state="disabled")

    def _delete(self) -> None:
        if not self._selected_id:
            messagebox.showwarning("Sélection", "Sélectionnez un run."); return
        if confirm(self, "Supprimer", f"Supprimer le run #{self._selected_id} ?"):
            self._svc.delete_run(self._selected_id)
            self._selected_id = None
            self.refresh()

    def _replay(self) -> None:
        if not self._selected_id:
            messagebox.showwarning("Sélection", "Sélectionnez un run."); return
        run = self._svc.replay_run(self._selected_id)
        messagebox.showinfo("Replay", f"Re-lancé → Run #{run.id}" if run else "Échec du replay.")
        self.refresh()

    def _rate(self) -> None:
        if not self._selected_id:
            messagebox.showwarning("Sélection", "Sélectionnez un run."); return
        from app.ui.views.testlab import _RateDialog
        _RateDialog(self, run_id=self._selected_id)

    def _export(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("JSON", "*.json"), ("CSV", "*.csv")])
        if not path:
            return
        fmt = "csv" if path.endswith(".csv") else "json"
        limit = int(self._limit_var.get() or 100)
        data = self._svc.export_runs({"limit": limit}, format=fmt)
        with open(path, "w") as f:
            f.write(data)
        messagebox.showinfo("Export", f"Exporté vers {path}")
