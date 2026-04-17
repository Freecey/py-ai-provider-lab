import json
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
from typing import Optional

from .base_view import BaseView
from app.services.test_service import TestService
from app.services.provider_service import ProviderService
from app.services.model_service import ModelService
from app.services.credential_service import CredentialService
from app.storage.repositories.preset_repo import PresetRepository
from app.storage.db import get_conn
from app.models.preset import Preset


class TestLabView(BaseView):
    def __init__(self, parent, app=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._app = app
        self._svc = TestService()
        self._p_svc = ProviderService()
        self._m_svc = ModelService()
        self._c_svc = CredentialService()
        self._current_run_id: Optional[int] = None
        self._presets_data: list = []

    def build(self) -> None:
        super().build()
        ttk.Label(self, text="🧪 Test Lab", font=("", 14, "bold"), padding=8).pack(anchor="w")
        pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Left: presets sidebar
        self._preset_frame = ttk.LabelFrame(pane, text="Presets", width=160)
        pane.add(self._preset_frame, weight=1)
        self._build_presets_panel()

        # Center: config + params
        center = ttk.Frame(pane)
        pane.add(center, weight=3)
        self._build_config_panel(center)

        # Right: results
        right = ttk.Frame(pane)
        pane.add(right, weight=3)
        self._build_results_panel(right)

    def _build_presets_panel(self) -> None:
        self._presets_lb = tk.Listbox(self._preset_frame, width=18)
        self._presets_lb.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self._presets_lb.bind("<Double-Button-1>", self._load_preset)
        btns = ttk.Frame(self._preset_frame)
        btns.pack(fill=tk.X)
        ttk.Button(btns, text="💾 Sauvegarder", command=self._save_preset).pack(fill=tk.X, padx=2, pady=1)

    def _build_config_panel(self, parent) -> None:
        sel = ttk.LabelFrame(parent, text="Sélection", padding=8)
        sel.pack(fill=tk.X, padx=4, pady=4)

        rows = [
            ("Provider", "_prov_var"), ("Credential", "_cred_var"),
            ("Modèle", "_model_var"), ("Modalité", "_modality_var"),
        ]
        self._prov_var = tk.StringVar()
        self._cred_var = tk.StringVar()
        self._model_var = tk.StringVar()
        self._modality_var = tk.StringVar(value="text")

        for label, var_name in rows:
            r = ttk.Frame(sel); r.pack(fill=tk.X, pady=2)
            ttk.Label(r, text=label, width=12, anchor="w").pack(side=tk.LEFT)
            var = getattr(self, var_name)
            cb = ttk.Combobox(r, textvariable=var, state="readonly", width=26)
            cb.pack(side=tk.LEFT)
            setattr(self, f"_{var_name[1:]}_cb", cb)

        self._prov_var.trace_add("write", lambda *_: self._on_provider_change())
        self._modality_var.trace_add("write", lambda *_: self._build_params())

        # Params panel
        self._params_outer = ttk.LabelFrame(parent, text="Paramètres", padding=8)
        self._params_outer.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self._params_frame: Optional[ttk.Frame] = None
        self._param_vars: dict[str, tk.StringVar] = {}

    def _build_results_panel(self, parent) -> None:
        ctrl = ttk.Frame(parent)
        ctrl.pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(ctrl, text="▶ Lancer", command=self._run).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl, text="🔄 Relancer", command=self._replay).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl, text="⭐ Noter", command=self._rate).pack(side=tk.LEFT, padx=2)

        nb = ttk.Notebook(parent)
        nb.pack(fill=tk.BOTH, expand=True, padx=4)

        req_frame = ttk.Frame(nb)
        nb.add(req_frame, text="Requête")
        self._req_text = scrolledtext.ScrolledText(req_frame, height=12, state="disabled", wrap="word")
        self._req_text.pack(fill=tk.BOTH, expand=True)

        resp_frame = ttk.Frame(nb)
        nb.add(resp_frame, text="Réponse")
        self._resp_text = scrolledtext.ScrolledText(resp_frame, height=12, state="disabled", wrap="word")
        self._resp_text.pack(fill=tk.BOTH, expand=True)

        self._metrics_var = tk.StringVar(value="")
        ttk.Label(parent, textvariable=self._metrics_var, padding=4).pack(anchor="w", padx=4)

    def _build_params(self) -> None:
        if self._params_frame:
            self._params_frame.destroy()
        self._params_frame = ttk.Frame(self._params_outer)
        self._params_frame.pack(fill=tk.BOTH, expand=True)
        self._param_vars.clear()
        modality = self._modality_var.get()

        if modality == "text":
            fields = [("Prompt", "user_prompt", ""), ("System", "system_prompt", ""),
                      ("Temperature", "temperature", "0.7"), ("Max tokens", "max_tokens", "1024")]
        elif modality == "image":
            fields = [("Prompt", "prompt", ""), ("Size", "size", "1024x1024"),
                      ("Quality", "quality", "standard"), ("N images", "n", "1")]
        elif modality == "audio":
            fields = [("Opération", "operation", "transcription"), ("Fichier", "file_path", "")]
        else:
            fields = [("Prompt", "prompt", "")]

        for label, key, default in fields:
            r = ttk.Frame(self._params_frame); r.pack(fill=tk.X, pady=2)
            ttk.Label(r, text=label, width=14, anchor="w").pack(side=tk.LEFT)
            var = tk.StringVar(value=default)
            self._param_vars[key] = var
            ttk.Entry(r, textvariable=var, width=30).pack(side=tk.LEFT, fill=tk.X, expand=True)

        if modality == "text":
            self._stream_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(self._params_frame, text="Streaming",
                            variable=self._stream_var).pack(anchor="w")

    def _on_provider_change(self) -> None:
        prov_name = self._prov_var.get()
        prov = next((p for p in self._p_svc.list_providers() if p.name == prov_name), None)
        if not prov:
            return
        creds = self._c_svc.list_credentials(provider_id=prov.id)
        self._creds_map = {c.name: c for c in creds}
        cred_cb = getattr(self, "_cred_var_cb", None)
        if cred_cb:
            cred_cb["values"] = [c.name for c in creds]
        models = self._m_svc.list_models(provider_id=prov.id, active_only=True)
        self._models_map = {(m.display_name or m.technical_name): m for m in models}
        model_cb = getattr(self, "_model_var_cb", None)
        if model_cb:
            model_cb["values"] = list(self._models_map.keys())

    def _run(self) -> None:
        params = {k: v.get() for k, v in self._param_vars.items()}
        modality = self._modality_var.get()
        cred_name = self._cred_var.get()
        model_name = self._model_var.get()
        cred = getattr(self, "_creds_map", {}).get(cred_name)
        model = getattr(self, "_models_map", {}).get(model_name)
        if not cred or not model:
            messagebox.showwarning("Test", "Sélectionnez un credential et un modèle."); return

        self._set_req_text(json.dumps(params, indent=2))
        self._set_resp_text("En cours...")
        self._metrics_var.set("")

        def on_chunk(delta):
            self._resp_text.configure(state="normal")
            self._resp_text.insert("end", delta)
            self._resp_text.see("end")
            self._resp_text.configure(state="disabled")

        def callback(run, result):
            if self._app:
                self._app.schedule(lambda: self._on_result(run, result))

        stream = getattr(self, "_stream_var", tk.BooleanVar()).get() if modality == "text" else False

        if modality == "text":
            self._svc.run_text(cred.id, model.id, params,
                               on_chunk=on_chunk if stream else None, callback=callback)
        elif modality == "image":
            self._svc.run_image(cred.id, model.id, params, callback=callback)
        elif modality == "audio":
            self._svc.run_audio(cred.id, model.id, params,
                                file_path=params.get("file_path"), callback=callback)
        else:
            self._svc.run_video(cred.id, model.id, params, callback=callback)

    def _on_result(self, run, result) -> None:
        self._current_run_id = run.id
        status = "✅" if run.status == "success" else "❌"
        self._set_resp_text(run.response_raw or (result.error if result else "Erreur inconnue"))
        self._metrics_var.set(
            f"{status} Statut: {run.status} | Latence: {run.latency_ms}ms | "
            f"Coût: {run.cost_estimated or '—'}"
        )

    def _replay(self) -> None:
        if not self._current_run_id:
            messagebox.showwarning("Replay", "Aucun test précédent à relancer."); return
        from app.services.history_service import HistoryService
        run = HistoryService().replay_run(self._current_run_id)
        if run:
            self._metrics_var.set(f"Re-lancé : run #{run.id}")

    def _rate(self) -> None:
        if not self._current_run_id:
            messagebox.showwarning("Note", "Aucun test à noter."); return
        _RateDialog(self, run_id=self._current_run_id)

    def _save_preset(self) -> None:
        name = simpledialog.askstring("Preset", "Nom du preset :", parent=self)
        if not name:
            return
        params = {k: v.get() for k, v in self._param_vars.items()}
        modality = self._modality_var.get()
        preset = Preset(name=name, modality=modality, params=params)
        PresetRepository(get_conn()).create(preset)
        self._load_presets()

    def _load_presets(self) -> None:
        modality = self._modality_var.get()
        self._presets_data = PresetRepository(get_conn()).list(modality=modality)
        self._presets_lb.delete(0, "end")
        for p in self._presets_data:
            self._presets_lb.insert("end", p.name)

    def _load_preset(self, event=None) -> None:
        sel = self._presets_lb.curselection()
        if not sel: return
        preset = self._presets_data[sel[0]]
        for k, v in preset.params.items():
            if k in self._param_vars:
                self._param_vars[k].set(str(v))

    def _set_req_text(self, text: str) -> None:
        self._req_text.configure(state="normal")
        self._req_text.delete("1.0", "end")
        self._req_text.insert("end", text)
        self._req_text.configure(state="disabled")

    def _set_resp_text(self, text: str) -> None:
        self._resp_text.configure(state="normal")
        self._resp_text.delete("1.0", "end")
        self._resp_text.insert("end", text)
        self._resp_text.configure(state="disabled")

    def refresh(self) -> None:
        super().refresh()
        providers = self._p_svc.list_providers()
        for cb_name, items in [("_prov_var_cb", [p.name for p in providers]),
                                ("_modality_var_cb", ["text", "image", "audio", "video"])]:
            cb = getattr(self, cb_name, None)
            if cb:
                cb["values"] = items
        self._build_params()
        self._load_presets()


class _RateDialog(tk.Toplevel):
    def __init__(self, parent, run_id: int):
        super().__init__(parent)
        self.title("Notation")
        self.grab_set()
        self._run_id = run_id
        ttk.Label(self, text="Note (1-5) :", padding=8).pack()
        self._rating_var = tk.IntVar(value=3)
        ttk.Scale(self, from_=1, to=5, variable=self._rating_var, orient="horizontal").pack(padx=16)
        ttk.Label(self, text="Commentaire :").pack()
        self._notes = tk.Text(self, height=3, width=40)
        self._notes.pack(padx=8, pady=4)
        ttk.Button(self, text="Enregistrer", command=self._save).pack(pady=8)

    def _save(self) -> None:
        from app.services.history_service import HistoryService
        HistoryService().rate_run(self._run_id, self._rating_var.get(), self._notes.get("1.0", "end").strip())
        self.destroy()
