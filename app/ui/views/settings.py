import tkinter as tk
from tkinter import ttk, messagebox

from .base_view import BaseView
from app.config.settings import get_settings


class SettingsView(BaseView):
    def __init__(self, parent, app=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._app = app

    def build(self) -> None:
        super().build()
        ttk.Label(self, text="⚙️ Paramètres", font=("", 14, "bold"), padding=8).pack(anchor="w")

        form = ttk.LabelFrame(self, text="Configuration", padding=12)
        form.pack(fill=tk.X, padx=16, pady=8)

        settings = get_settings()
        self._fields: dict[str, tk.StringVar] = {}

        for label, key, val in [
            ("Dossier de données", "data_dir", settings.data_dir),
            ("Niveau de log", "log_level", settings.log_level),
            ("Thème", "theme", settings.theme),
            ("Langue", "lang", settings.lang),
            ("Timeout réseau (s)", "network_timeout", str(settings.network_timeout)),
        ]:
            row = ttk.Frame(form)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=label, width=22, anchor="w").pack(side=tk.LEFT)
            var = tk.StringVar(value=val)
            self._fields[key] = var
            ttk.Entry(row, textvariable=var, width=30).pack(side=tk.LEFT)

        # Sandbox mode
        self._sandbox_var = tk.BooleanVar(value=settings.sandbox_mode)
        ttk.Checkbutton(form, text="Mode sandbox (pas d'appels API réels)",
                        variable=self._sandbox_var).pack(anchor="w", pady=4)

        # Crypto passphrase
        crypt_frame = ttk.LabelFrame(self, text="Chiffrement", padding=12)
        crypt_frame.pack(fill=tk.X, padx=16, pady=8)
        ttk.Label(crypt_frame, text="Passphrase de chiffrement :").pack(anchor="w")
        from app.ui.widgets.secret_field import SecretField
        self._passphrase_field = SecretField(crypt_frame)
        self._passphrase_field.pack(anchor="w", pady=4)
        ttk.Button(crypt_frame, text="Appliquer la passphrase",
                   command=self._apply_passphrase).pack(anchor="w")

        ttk.Button(self, text="Sauvegarder", command=self._save).pack(pady=12)

    def _save(self) -> None:
        # In-memory update only (config.ini write would require file manipulation)
        from app.config import settings as smod
        s = get_settings()
        s.data_dir = self._fields["data_dir"].get()
        s.log_level = self._fields["log_level"].get().upper()
        s.theme = self._fields["theme"].get()
        s.lang = self._fields["lang"].get()
        try:
            s.network_timeout = int(self._fields["network_timeout"].get())
        except ValueError:
            pass
        s.sandbox_mode = self._sandbox_var.get()
        messagebox.showinfo("Paramètres", "Paramètres mis à jour (session en cours).")

    def _apply_passphrase(self) -> None:
        from app.utils.crypto import set_passphrase
        passphrase = self._passphrase_field.get()
        if passphrase:
            set_passphrase(passphrase)
            messagebox.showinfo("Chiffrement", "Passphrase appliquée.")

    def refresh(self) -> None:
        super().refresh()
