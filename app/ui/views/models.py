import tkinter as tk
from tkinter import ttk, messagebox

from .base_view import BaseView
from app.ui.widgets import FilterableTable, confirm
from app.services.model_service import ModelService
from app.services.provider_service import ProviderService

_COLS = ["id", "provider_id", "technical_name", "display_name", "type", "active", "favorite", "rating"]
_CAPABILITIES = [
    "chat", "reasoning", "vision", "image_gen", "video_gen", "video_understanding",
    "transcription", "speech", "embeddings", "tool_calling", "json_output", "streaming",
]


class ModelsView(BaseView):
    def __init__(self, parent, app=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._app = app
        self._svc = ModelService()
        self._p_svc = ProviderService()
        self._selected_id: int | None = None

    def build(self) -> None:
        super().build()
        ttk.Label(self, text="🤖 Modèles", font=("", 14, "bold"), padding=8).pack(anchor="w")

        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=8, pady=2)
        ttk.Label(filter_frame, text="Provider :").pack(side=tk.LEFT)
        self._provider_var = tk.StringVar(value="Tous")
        self._provider_cb = ttk.Combobox(filter_frame, textvariable=self._provider_var,
                                          state="readonly", width=20)
        self._provider_cb.pack(side=tk.LEFT, padx=4)
        self._provider_cb.bind("<<ComboboxSelected>>", lambda e: self._load_table())

        ttk.Label(filter_frame, text="Type :").pack(side=tk.LEFT, padx=(8, 0))
        self._type_var = tk.StringVar(value="Tous")
        ttk.Combobox(filter_frame, textvariable=self._type_var, state="readonly", width=12,
                     values=["Tous", "text", "image", "audio", "video", "multimodal", "embedding", "other"]
                     ).pack(side=tk.LEFT, padx=4)
        self._type_var.trace_add("write", lambda *_: self._load_table())

        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=8)
        ttk.Button(toolbar, text="➕ Ajouter", command=self._add).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ Modifier", command=self._edit).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Supprimer", command=self._delete).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔄 Sync API", command=self._sync).pack(side=tk.LEFT, padx=2)
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
        model_type = self._type_var.get()
        models = self._svc.list_models(
            provider_id=provider_id,
            type=None if model_type == "Tous" else model_type,
            active_only=False,
        )
        rows = [{k: v for k, v in m.__dict__.items() if k in _COLS} for m in models]
        self._table.load(rows)

    def _add(self) -> None:
        _ModelForm(self, title="Nouveau modèle", providers=self._p_svc.list_providers(),
                   on_save=self._on_save)

    def _edit(self) -> None:
        if not self._selected_id:
            messagebox.showwarning("Sélection", "Sélectionnez un modèle."); return
        m = self._svc.get_model(self._selected_id)
        if m:
            _ModelForm(self, title="Modifier modèle", providers=self._p_svc.list_providers(),
                       model=m, on_save=self._on_save)

    def _delete(self) -> None:
        if not self._selected_id:
            messagebox.showwarning("Sélection", "Sélectionnez un modèle."); return
        if confirm(self, "Supprimer", f"Supprimer le modèle #{self._selected_id} ?"):
            self._svc.delete_model(self._selected_id)
            self._selected_id = None
            self.refresh()

    def _sync(self) -> None:
        if not self._selected_id:
            messagebox.showwarning("Sélection", "Sélectionnez un modèle d'abord pour identifier le provider."); return
        m = self._svc.get_model(self._selected_id)
        if not m: return
        from app.storage.repositories.credential_repo import CredentialRepository
        from app.storage.db import get_conn
        creds = CredentialRepository(get_conn()).list(provider_id=m.provider_id)
        if not creds:
            messagebox.showwarning("Sync", "Aucun credential configuré."); return
        result = self._svc.sync_models(m.provider_id, creds[0].id)
        messagebox.showinfo("Sync", f"Ajoutés: {result.added}, Mis à jour: {result.updated}, Erreurs: {result.errors}")
        self.refresh()

    def _on_save(self, data: dict, model_id: "int | None") -> None:
        if model_id:
            self._svc.update_model(model_id, data)
        else:
            self._svc.create_model(data)
        self.refresh()


class _ModelForm(tk.Toplevel):
    def __init__(self, parent, title: str, providers: list, on_save, model=None):
        super().__init__(parent)
        self.title(title)
        self.grab_set()
        self._providers = providers
        self._model = model
        self._on_save = on_save
        self._build()

    def _build(self) -> None:
        form = ttk.Frame(self, padding=12)
        form.pack(fill=tk.BOTH, expand=True)
        self._vars: dict[str, tk.StringVar] = {}

        row = ttk.Frame(form); row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Provider", width=18, anchor="w").pack(side=tk.LEFT)
        self._provider_var = tk.StringVar()
        if self._model:
            p = next((p for p in self._providers if p.id == self._model.provider_id), None)
            if p: self._provider_var.set(p.name)
        ttk.Combobox(row, textvariable=self._provider_var, values=[p.name for p in self._providers],
                     state="readonly", width=28).pack(side=tk.LEFT)

        for label, key in [("Nom technique", "technical_name"), ("Nom affiché", "display_name"),
                            ("Contexte max", "context_max"), ("Notes", "notes")]:
            r = ttk.Frame(form); r.pack(fill=tk.X, pady=2)
            ttk.Label(r, text=label, width=18, anchor="w").pack(side=tk.LEFT)
            var = tk.StringVar(value=str(getattr(self._model, key, "") or "") if self._model else "")
            self._vars[key] = var
            ttk.Entry(r, textvariable=var, width=30).pack(side=tk.LEFT)

        r = ttk.Frame(form); r.pack(fill=tk.X, pady=2)
        ttk.Label(r, text="Type", width=18, anchor="w").pack(side=tk.LEFT)
        self._type_var = tk.StringVar(value=getattr(self._model, "type", "text") if self._model else "text")
        ttk.Combobox(r, textvariable=self._type_var, state="readonly", width=14,
                     values=["text", "image", "audio", "video", "multimodal", "embedding", "other"]
                     ).pack(side=tk.LEFT)

        # Capabilities
        ttk.Label(form, text="Capacités :", padding=(0, 4)).pack(anchor="w")
        caps_frame = ttk.Frame(form)
        caps_frame.pack(fill=tk.X)
        existing_caps = set()
        if self._model:
            existing_caps = {c.capability if hasattr(c, "capability") else c for c in self._model.capabilities}
        self._cap_vars: dict[str, tk.BooleanVar] = {}
        for i, cap in enumerate(_CAPABILITIES):
            var = tk.BooleanVar(value=cap in existing_caps)
            self._cap_vars[cap] = var
            ttk.Checkbutton(caps_frame, text=cap, variable=var).grid(row=i // 4, column=i % 4, sticky="w", padx=2)

        btn_frame = ttk.Frame(form)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="Sauvegarder", command=self._save).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Annuler", command=self.destroy).pack(side=tk.LEFT)

    def _save(self) -> None:
        provider_name = self._provider_var.get()
        provider = next((p for p in self._providers if p.name == provider_name), None)
        data = {k: v.get() for k, v in self._vars.items()}
        data["provider_id"] = provider.id if provider else None
        data["type"] = self._type_var.get()
        data["capabilities"] = [cap for cap, var in self._cap_vars.items() if var.get()]
        try:
            data["context_max"] = int(data["context_max"]) if data["context_max"] else None
        except ValueError:
            data["context_max"] = None
        self._on_save(data, self._model.id if self._model else None)
        self.destroy()
