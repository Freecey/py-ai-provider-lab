import argparse
import sys

from app.services.provider_service import ProviderService
from .output import print_output, print_error

_COLS = ["id", "name", "slug", "active", "base_url", "auth_type"]


def add_subparser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("providers", help="Gérer les providers")
    s = p.add_subparsers(dest="providers_cmd")

    # list
    pl = s.add_parser("list", help="Lister les providers")
    pl.add_argument("--output", choices=["table", "json", "plain"], default="table")
    pl.add_argument("--active-only", action="store_true")

    # show
    ps = s.add_parser("show", help="Afficher un provider")
    ps.add_argument("id", type=int)
    ps.add_argument("--output", choices=["table", "json", "plain"], default="table")

    # add
    pa = s.add_parser("add", help="Ajouter un provider")
    pa.add_argument("--name", required=True)
    pa.add_argument("--url", required=True, dest="base_url")
    pa.add_argument("--auth", default="api_key", dest="auth_type",
                    choices=["api_key", "bearer", "oauth2", "custom"])
    pa.add_argument("--output", choices=["table", "json", "plain"], default="table")

    # edit
    pe = s.add_parser("edit", help="Modifier un provider")
    pe.add_argument("id", type=int)
    pe.add_argument("--name"); pe.add_argument("--url", dest="base_url")
    pe.add_argument("--active", choices=["true", "false"])
    pe.add_argument("--output", choices=["table", "json", "plain"], default="table")

    # delete
    pd = s.add_parser("delete", help="Supprimer un provider")
    pd.add_argument("id", type=int)


def handle(args: argparse.Namespace) -> None:
    svc = ProviderService()
    cmd = args.providers_cmd
    fmt = getattr(args, "output", "table")

    if cmd == "list":
        items = svc.list_providers(active_only=args.active_only)
        print_output(items, fmt, columns=_COLS)

    elif cmd == "show":
        p = svc.get_provider(args.id)
        if not p:
            print_error(f"Provider {args.id} introuvable", 1)
        print_output(p, fmt)

    elif cmd == "add":
        data = {"name": args.name, "base_url": args.base_url, "auth_type": args.auth_type}
        p = svc.create_provider(data)
        print_output(p, fmt)

    elif cmd == "edit":
        data = {}
        if args.name: data["name"] = args.name
        if args.base_url: data["base_url"] = args.base_url
        if args.active: data["active"] = args.active == "true"
        p = svc.update_provider(args.id, data)
        if not p:
            print_error(f"Provider {args.id} introuvable", 1)
        print_output(p, fmt)

    elif cmd == "delete":
        ok = svc.delete_provider(args.id)
        if not ok:
            print_error(f"Provider {args.id} introuvable", 1)
        else:
            print(f"Provider {args.id} supprimé.")

    else:
        print("Usage: app providers <list|show|add|edit|delete>")
