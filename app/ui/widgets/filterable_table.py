import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class FilterableTable(ttk.Frame):
    """Treeview with a filter field and sortable columns."""

    def __init__(self, parent, columns: list[str], on_select: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self._columns = columns
        self._all_rows: list[dict] = []
        self._on_select = on_select

        self._build_filter()
        self._build_tree()

    def _build_filter(self) -> None:
        frame = ttk.Frame(self)
        frame.pack(fill=tk.X, padx=4, pady=2)
        ttk.Label(frame, text="Filtrer :").pack(side=tk.LEFT)
        self._filter_var = tk.StringVar()
        self._filter_var.trace_add("write", lambda *_: self._apply_filter())
        ttk.Entry(frame, textvariable=self._filter_var, width=30).pack(side=tk.LEFT, padx=4)
        ttk.Button(frame, text="✕", width=3, command=lambda: self._filter_var.set("")).pack(side=tk.LEFT)

    def _build_tree(self) -> None:
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True)
        self._tree = ttk.Treeview(frame, columns=self._columns, show="headings", selectmode="browse")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self._tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        for col in self._columns:
            self._tree.heading(col, text=col, command=lambda c=col: self._sort_by(c))
            self._tree.column(col, width=120, anchor="w")
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        if self._on_select:
            self._tree.bind("<<TreeviewSelect>>", self._handle_select)

    def load(self, rows: list[dict]) -> None:
        self._all_rows = rows
        self._apply_filter()

    def _apply_filter(self) -> None:
        term = self._filter_var.get().lower()
        filtered = [r for r in self._all_rows if not term or
                    any(term in str(v).lower() for v in r.values())]
        self._tree.delete(*self._tree.get_children())
        for row in filtered:
            values = [row.get(c, "") for c in self._columns]
            self._tree.insert("", "end", iid=str(row.get("id", id(row))), values=values)

    def _sort_by(self, col: str) -> None:
        data = [(self._tree.set(k, col), k) for k in self._tree.get_children()]
        data.sort(key=lambda t: t[0])
        for i, (_, k) in enumerate(data):
            self._tree.move(k, "", i)

    def _handle_select(self, event=None) -> None:
        sel = self._tree.selection()
        if sel and self._on_select:
            iid = sel[0]
            row = next((r for r in self._all_rows if str(r.get("id", id(r))) == iid), None)
            if row:
                self._on_select(row)

    def get_selected_id(self) -> Optional[int]:
        sel = self._tree.selection()
        if sel:
            try:
                return int(sel[0])
            except ValueError:
                return None
        return None
