import tkinter as tk
from tkinter import ttk, messagebox

from .base_view import BaseView
from app.ui.widgets import FilterableTable, confirm
from app.services.provider_service import ProviderService

_COLS = ["id", "name", "slug", "active", "base_url", "auth_type"]


class ProvidersView(BaseView):
    def __init__(self, parent, app=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._app = app
        self._svc = ProviderService()
        self._selected_id: int | None = None

    def build(self) -> None:
        super().build()
        ttk.Label(self, text="🔌 Providers", font=("", 14, "bold"), padding=8).pack(anchor="w")

        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=8)
        ttk.Button(toolbar, text="➕ Ajouter", command=self._add).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ Modifier", command=self._edit).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Supprimer", command=self._delete).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔍 Tester", command=self._test).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔄 Rafraîchir", command=self.refresh).pack(side=tk.RIGHT, padx=2)

        self._table = FilterableTable(self, columns=_COLS,
                                      on_select=lambda r: setattr(self, "_selected_id", r.get("id")))
        self._table.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

    def refresh(self) -> None:
        super().refresh()
        providers = self._svc.list_providers()
        rows = [{k: v for k, v in p.__dict__.items() if k in _COLS} for p in providers]
        self._table.load(rows)

    def _add(self) -> None:
        _ProviderForm(self, title="Nouveau provider", on_save=self._on_save)

    def _edit(self) -> None:
        if not self._selected_id:
            messagebox.showwarning("Sélection", "Sélectionnez un provider.")
            return
        p = self._svc.get_provider(self._selected_id)
        if p:
            _ProviderForm(self, title="Modifier le provider", provider=p, on_save=self._on_save)

    def _delete(self) -> None:
        if not self._selected_id:
            messagebox.showwarning("Sélection", "Sélectionnez un provider.")
            return
        if confirm(self, "Supprimer", f"Supprimer le provider #{self._selected_id} ?"):
            self._svc.delete_provider(self._selected_id)
            self._selected_id = None
            self.refresh()

    def _test(self) -> None:
        if not self._selected_id:
            messagebox.showwarning("Sélection", "Sélectionnez un provider.")
            return
        from app.storage.repositories.credential_repo import CredentialRepository
        from app.storage.db import get_conn
        creds = CredentialRepository(get_conn()).list(provider_id=self._selected_id)
        if not creds:
            messagebox.showwarning("Test", "Aucun credential configuré pour ce provider.")
            return
        result = self._svc.health_check(self._selected_id, creds[0].id)
        messagebox.showinfo("Santé", f"Statut: {result.status}\n{result.message}")

    def _on_save(self, data: dict, provider_id: int | None) -> None:
        if provider_id:
            self._svc.update_provider(provider_id, data)
        else:
            self._svc.create_provider(data)
        self.refresh()


class _ProviderForm(tk.Toplevel):
    def __init__(self, parent, title: str, on_save, provider=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.grab_set()
        self._provider = provider
        self._on_save = on_save
        self._build()

    def _build(self) -> None:
        form = ttk.Frame(self, padding=12)
        form.pack()
        self._vars: dict[str, tk.StringVar] = {}
        fields = [
            ("Nom", "name"), ("Slug", "slug"), ("URL de base", "base_url"),
            ("Type d'auth", "auth_type"), ("Notes", "notes"),
        ]
        for label, key in fields:
            row = ttk.Frame(form)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=label, width=16, anchor="w").pack(side=tk.LEFT)
            var = tk.StringVar(value=getattr(self._provider, key, "") if self._provider else "")
            self._vars[key] = var
            ttk.Entry(row, textvariable=var, width=32).pack(side=tk.LEFT)

        self._active_var = tk.BooleanVar(value=getattr(self._provider, "active", True))
        ttk.Checkbutton(form, text="Actif", variable=self._active_var).pack(anchor="w", pady=4)

        btn_frame = ttk.Frame(form)
        btn_frame.pack(fill=tk.X, pady=8)
        ttk.Button(btn_frame, text="Sauvegarder", command=self._save).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Annuler", command=self.destroy).pack(side=tk.LEFT)

    def _save(self) -> None:
        data = {k: v.get() for k, v in self._vars.items()}
        data["active"] = self._active_var.get()
        self._on_save(data, self._provider.id if self._provider else None)
        self.destroy()
