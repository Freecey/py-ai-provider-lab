import argparse

from app.services.model_service import ModelService
from .output import print_output, print_error

_COLS = ["id", "provider_id", "technical_name", "display_name", "type", "active", "favorite", "rating"]


def add_subparser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("models", help="Gérer les modèles")
    s = p.add_subparsers(dest="models_cmd")

    ml = s.add_parser("list")
    ml.add_argument("--provider", type=int, dest="provider_id")
    ml.add_argument("--type", dest="model_type")
    ml.add_argument("--all", action="store_true", dest="include_inactive")
    ml.add_argument("--output", choices=["table", "json", "plain"], default="table")

    ms = s.add_parser("show"); ms.add_argument("id", type=int)
    ms.add_argument("--output", choices=["table", "json", "plain"], default="table")

    ma = s.add_parser("add")
    ma.add_argument("--provider", type=int, required=True, dest="provider_id")
    ma.add_argument("--name", required=True, dest="technical_name")
    ma.add_argument("--display-name", dest="display_name", default="")
    ma.add_argument("--type", default="text", dest="model_type")
    ma.add_argument("--output", choices=["table", "json", "plain"], default="table")

    msy = s.add_parser("sync")
    msy.add_argument("--provider", type=int, required=True, dest="provider_id")
    msy.add_argument("--credential", type=int, required=True, dest="credential_id")
    msy.add_argument("--output", choices=["table", "json", "plain"], default="table")


def handle(args: argparse.Namespace) -> None:
    svc = ModelService()
    cmd = args.models_cmd
    fmt = getattr(args, "output", "table")

    if cmd == "list":
        items = svc.list_models(
            provider_id=getattr(args, "provider_id", None),
            type=getattr(args, "model_type", None),
            active_only=not getattr(args, "include_inactive", False),
        )
        print_output(items, fmt, columns=_COLS)

    elif cmd == "show":
        m = svc.get_model(args.id)
        if not m:
            print_error(f"Modèle {args.id} introuvable", 1)
        print_output(m, fmt)

    elif cmd == "add":
        data = {"provider_id": args.provider_id, "technical_name": args.technical_name,
                "display_name": args.display_name or args.technical_name, "type": args.model_type}
        m = svc.create_model(data)
        print_output(m, fmt)

    elif cmd == "sync":
        result = svc.sync_models(args.provider_id, args.credential_id)
        print_output(result.__dict__, fmt)

    else:
        print("Usage: app models <list|show|add|sync>")
