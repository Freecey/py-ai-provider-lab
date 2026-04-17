import tkinter as tk
from tkinter import ttk, messagebox

from .base_view import BaseView
from app.ui.widgets import FilterableTable, SecretField, confirm
from app.services.credential_service import CredentialService
from app.services.provider_service import ProviderService

_COLS = ["id", "provider_id", "name", "active", "validity"]


class CredentialsView(BaseView):
    def __init__(self, parent, app=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._app = app
        self._svc = CredentialService()
        self._p_svc = ProviderService()
        self._selected_id: int | None = None

    def build(self) -> None:
        super().build()
        ttk.Label(self, text="🔑 Credentials", font=("", 14, "bold"), padding=8).pack(anchor="w")

        # Provider filter
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=8, pady=2)
        ttk.Label(filter_frame, text="Provider :").pack(side=tk.LEFT)
        self._provider_var = tk.StringVar(value="Tous")
        self._provider_cb = ttk.Combobox(filter_frame, textvariable=self._provider_var, state="readonly", width=20)
        self._provider_cb.pack(side=tk.LEFT, padx=4)
        self._provider_cb.bind("<<ComboboxSelected>>", lambda e: self._load_table())

        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=8)
        ttk.Button(toolbar, text="➕ Ajouter", command=self._add).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ Modifier", command=self._edit).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Supprimer", command=self._delete).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔍 Tester", command=self._test).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📋 Dupliquer", command=self._duplicate).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔄", command=self.refresh).pack(side=tk.RIGHT)

        self._table = FilterableTable(self, columns=_COLS,
                                      on_select=lambda r: setattr(self, "_selected_id", r.get("id")))
        self._table.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

    def refresh(self) -> None:
        super().refresh()
        providers = self._p_svc.list_providers()
        self._provider_map = {"Tous": None}
        self._provider_map.update({p.name: p.id for p in providers})
        self._provider_cb["values"] = list(self._provider_map.keys())
        self._load_table()

    def _load_table(self) -> None:
        provider_id = self._provider_map.get(self._provider_var.get())
        creds = self._svc.list_credentials(provider_id=provider_id)
        rows = [{k: v for k, v in c.__dict__.items() if k in _COLS} for c in creds]
        self._table.load(rows)

    def _add(self) -> None:
        _CredentialForm(self, title="Nouveau credential", providers=self._p_svc.list_providers(),
                        on_save=self._on_save)

    def _edit(self) -> None:
        if not self._selected_id:
            messagebox.showwarning("Sélection", "Sélectionnez un credential."); return
        c = self._svc.get_credential(self._selected_id)
        if c:
            _CredentialForm(self, title="Modifier credential", providers=self._p_svc.list_providers(),
                            credential=c, on_save=self._on_save)

    def _delete(self) -> None:
        if not self._selected_id:
            messagebox.showwarning("Sélection", "Sélectionnez un credential."); return
        if confirm(self, "Supprimer", f"Supprimer le credential #{self._selected_id} ?"):
            self._svc.delete_credential(self._selected_id)
            self._selected_id = None
            self.refresh()

    def _test(self) -> None:
        if not self._selected_id:
            messagebox.showwarning("Sélection", "Sélectionnez un credential."); return
        result = self._svc.test_connection(self._selected_id)
        status = "✅ OK" if result.success else "❌ Échec"
        messagebox.showinfo("Test", f"{status}\n{result.message}")
        self.refresh()

    def _duplicate(self) -> None:
        if not self._selected_id:
            messagebox.showwarning("Sélection", "Sélectionnez un credential."); return
        self._svc.duplicate_credential(self._selected_id)
        self.refresh()

    def _on_save(self, data: dict, cred_id: "int | None") -> None:
        if cred_id:
            self._svc.update_credential(cred_id, data)
        else:
            self._svc.create_credential(data)
        self.refresh()


class _CredentialForm(tk.Toplevel):
    def __init__(self, parent, title: str, providers: list, on_save, credential=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(True, False)
        self.grab_set()
        self._providers = providers
        self._credential = credential
        self._on_save = on_save
        self._build()

    def _build(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Basic tab
        basic = ttk.Frame(notebook, padding=12)
        notebook.add(basic, text="Général")
        self._vars: dict[str, tk.StringVar] = {}

        provider_names = [p.name for p in self._providers]
        row = ttk.Frame(basic); row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Provider", width=20, anchor="w").pack(side=tk.LEFT)
        self._provider_var = tk.StringVar(value="")
        if self._credential:
            p = next((p for p in self._providers if p.id == self._credential.provider_id), None)
            if p: self._provider_var.set(p.name)
        self._provider_cb = ttk.Combobox(row, textvariable=self._provider_var,
                                          values=provider_names, state="readonly", width=28)
        self._provider_cb.pack(side=tk.LEFT)

        for label, key in [("Nom", "name"), ("Org ID", "org_id"), ("Project ID", "project_id"), ("Notes", "notes")]:
            r = ttk.Frame(basic); r.pack(fill=tk.X, pady=2)
            ttk.Label(r, text=label, width=20, anchor="w").pack(side=tk.LEFT)
            var = tk.StringVar(value=getattr(self._credential, key, "") if self._credential else "")
            self._vars[key] = var
            ttk.Entry(r, textvariable=var, width=30).pack(side=tk.LEFT)

        # Secrets
        r = ttk.Frame(basic); r.pack(fill=tk.X, pady=2)
        ttk.Label(r, text="API Key", width=20, anchor="w").pack(side=tk.LEFT)
        self._api_key_field = SecretField(r)
        self._api_key_field.set(getattr(self._credential, "api_key", "") if self._credential else "")
        self._api_key_field.pack(side=tk.LEFT)

        r = ttk.Frame(basic); r.pack(fill=tk.X, pady=2)
        ttk.Label(r, text="Bearer Token", width=20, anchor="w").pack(side=tk.LEFT)
        self._bearer_field = SecretField(r)
        self._bearer_field.set(getattr(self._credential, "bearer_token", "") if self._credential else "")
        self._bearer_field.pack(side=tk.LEFT)

        self._active_var = tk.BooleanVar(value=getattr(self._credential, "active", True))
        ttk.Checkbutton(basic, text="Actif", variable=self._active_var).pack(anchor="w", pady=4)

        # OAuth2 tab
        oauth = ttk.Frame(notebook, padding=12)
        notebook.add(oauth, text="OAuth2")
        self._oauth_vars: dict[str, tk.StringVar] = {}
        for label, key in [("Client ID", "oauth_client_id"), ("Auth URL", "oauth_auth_url"),
                            ("Token Endpoint", "oauth_token_endpoint"), ("Scopes", "oauth_scopes")]:
            r = ttk.Frame(oauth); r.pack(fill=tk.X, pady=2)
            ttk.Label(r, text=label, width=18, anchor="w").pack(side=tk.LEFT)
            var = tk.StringVar(value=getattr(self._credential, key, "") if self._credential else "")
            self._oauth_vars[key] = var
            ttk.Entry(r, textvariable=var, width=32).pack(side=tk.LEFT)

        r = ttk.Frame(oauth); r.pack(fill=tk.X, pady=2)
        ttk.Label(r, text="Client Secret", width=18, anchor="w").pack(side=tk.LEFT)
        self._oauth_secret_field = SecretField(r)
        self._oauth_secret_field.pack(side=tk.LEFT)

        btn_frame = ttk.Frame(self, padding=8)
        btn_frame.pack()
        ttk.Button(btn_frame, text="Sauvegarder", command=self._save).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Annuler", command=self.destroy).pack(side=tk.LEFT)

    def _save(self) -> None:
        provider_name = self._provider_var.get()
        provider = next((p for p in self._providers if p.name == provider_name), None)
        data = {k: v.get() for k, v in self._vars.items()}
        data.update({k: v.get() for k, v in self._oauth_vars.items()})
        data["provider_id"] = provider.id if provider else None
        data["api_key"] = self._api_key_field.get()
        data["bearer_token"] = self._bearer_field.get()
        data["oauth_client_secret"] = self._oauth_secret_field.get()
        data["active"] = self._active_var.get()
        self._on_save(data, self._credential.id if self._credential else None)
        self.destroy()
