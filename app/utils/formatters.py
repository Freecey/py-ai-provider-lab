import json
from typing import Any


def format_table(rows: list[dict], columns: "list[str] | None" = None) -> str:
    if not rows:
        return "(aucun résultat)"
    cols = columns or list(rows[0].keys())
    widths = {c: max(len(str(c)), max(len(str(r.get(c, ""))) for r in rows)) for c in cols}
    sep = "  "
    header = sep.join(str(c).ljust(widths[c]) for c in cols)
    divider = sep.join("-" * widths[c] for c in cols)
    lines = [header, divider]
    for row in rows:
        lines.append(sep.join(str(row.get(c, "")).ljust(widths[c]) for c in cols))
    return "\n".join(lines)


def format_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def format_plain(rows: list[dict], key: str = "id") -> str:
    return "\n".join(str(r.get(key, r)) for r in rows)
