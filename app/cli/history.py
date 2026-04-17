import argparse

from app.services.history_service import HistoryService
from .output import print_output, print_error

_COLS = ["id", "modality", "status", "latency_ms", "cost_estimated", "rating", "created_at"]


def add_subparser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("history", help="Historique des tests")
    s = p.add_subparsers(dest="history_cmd")

    hl = s.add_parser("list")
    hl.add_argument("--provider", type=int, dest="provider_id")
    hl.add_argument("--model", type=int, dest="model_id")
    hl.add_argument("--status")
    hl.add_argument("--limit", type=int, default=20)
    hl.add_argument("--output", choices=["table", "json", "plain"], default="table")

    hs = s.add_parser("show"); hs.add_argument("id", type=int)
    hs.add_argument("--output", choices=["table", "json", "plain"], default="table")

    he = s.add_parser("export")
    he.add_argument("--format", choices=["json", "csv"], default="json")
    he.add_argument("--output", dest="output_file")
    he.add_argument("--limit", type=int, default=100)


def handle(args: argparse.Namespace) -> None:
    svc = HistoryService()
    cmd = args.history_cmd
    fmt = getattr(args, "output", "table")

    if cmd == "list":
        items = svc.list_runs(
            provider_id=getattr(args, "provider_id", None),
            model_id=getattr(args, "model_id", None),
            status=getattr(args, "status", None),
            limit=args.limit,
        )
        print_output(items, fmt, columns=_COLS)

    elif cmd == "show":
        r = svc.get_run(args.id)
        if not r:
            print_error(f"Run {args.id} introuvable", 1)
        print_output(r, fmt)

    elif cmd == "export":
        data = svc.export_runs({"limit": args.limit}, format=args.format)
        if args.output_file:
            with open(args.output_file, "w") as f:
                f.write(data)
            print(f"Exporté vers {args.output_file}")
        else:
            print(data)

    else:
        print("Usage: app history <list|show|export>")
