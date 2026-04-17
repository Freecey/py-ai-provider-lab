import json
import sys
from typing import Any

from app.utils.formatters import format_table, format_json, format_plain


def print_output(data: Any, output_format: str = "table",
                 columns: "list | None" = None, key: str = "id") -> None:
    if isinstance(data, list):
        rows = [_to_dict(item) for item in data]
    elif isinstance(data, dict):
        rows = [data]
    else:
        print(str(data))
        return

    if output_format == "json":
        print(format_json(rows if len(rows) != 1 else rows[0]))
    elif output_format == "plain":
        print(format_plain(rows, key=key))
    else:
        print(format_table(rows, columns=columns))


def print_error(message: str, exit_code: int = 1) -> None:
    print(f"Erreur: {message}", file=sys.stderr)
    sys.exit(exit_code)


def _to_dict(obj: Any) -> dict:
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "__dict__"):
        d = {}
        for k, v in obj.__dict__.items():
            if not k.startswith("_"):
                d[k] = str(v) if hasattr(v, "isoformat") else v
        return d
    return {"value": str(obj)}
