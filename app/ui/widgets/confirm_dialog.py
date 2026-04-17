import tkinter as tk
from tkinter import ttk


def confirm(parent, title: str = "Confirmer", message: str = "Êtes-vous sûr ?") -> bool:
    result = {"ok": False}
    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.resizable(False, False)
    dlg.grab_set()

    ttk.Label(dlg, text=message, padding=16, wraplength=300).pack()
    btn_frame = ttk.Frame(dlg, padding=8)
    btn_frame.pack()

    def _ok():
        result["ok"] = True
        dlg.destroy()

    ttk.Button(btn_frame, text="Confirmer", command=_ok).pack(side=tk.LEFT, padx=8)
    ttk.Button(btn_frame, text="Annuler", command=dlg.destroy).pack(side=tk.LEFT)
    dlg.wait_window()
    return result["ok"]
