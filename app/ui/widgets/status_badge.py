import tkinter as tk
from tkinter import ttk

_STATUS_COLORS = {
    "ok": "#22c55e",
    "success": "#22c55e",
    "active": "#22c55e",
    "auth_invalid": "#ef4444",
    "invalid": "#ef4444",
    "error": "#ef4444",
    "endpoint_ko": "#f97316",
    "timeout": "#f97316",
    "pending": "#eab308",
    "running": "#3b82f6",
    "untested": "#94a3b8",
    "cancelled": "#94a3b8",
}


class StatusBadge(ttk.Label):
    def __init__(self, parent, status: str = "untested", **kwargs):
        super().__init__(parent, **kwargs)
        self.set_status(status)

    def set_status(self, status: str) -> None:
        color = _STATUS_COLORS.get(status.lower(), "#94a3b8")
        self.configure(text=f" {status.upper()} ", background=color,
                       foreground="white", relief="flat", padding=2)
