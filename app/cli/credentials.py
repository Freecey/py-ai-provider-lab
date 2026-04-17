import argparse

from app.services.credential_service import CredentialService
from .output import print_output, print_error

_COLS = ["id", "provider_id", "name", "active", "validity", "org_id"]


def add_subparser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("credentials", help="Gérer les credentials")
    s = p.add_subparsers(dest="credentials_cmd")

    cl = s.add_parser("list"); cl.add_argument("--provider", type=int, dest="provider_id")
    cl.add_argument("--output", choices=["table", "json", "plain"], default="table")

    cs = s.add_parser("show"); cs.add_argument("id", type=int)
    cs.add_argument("--output", choices=["table", "json", "plain"], default="table")

    ca = s.add_parser("add")
    ca.add_argument("--provider", type=int, required=True, dest="provider_id")
    ca.add_argument("--name", required=True)
    ca.add_argument("--api-key", dest="api_key", default="")
    ca.add_argument("--output", choices=["table", "json", "plain"], default="table")

    ce = s.add_parser("edit"); ce.add_argument("id", type=int)
    ce.add_argument("--name"); ce.add_argument("--api-key", dest="api_key")
    ce.add_argument("--active", choices=["true", "false"])
    ce.add_argument("--output", choices=["table", "json", "plain"], default="table")

    cd = s.add_parser("delete"); cd.add_argument("id", type=int)
    ct = s.add_parser("test"); ct.add_argument("id", type=int)
    ct.add_argument("--output", choices=["table", "json", "plain"], default="table")


def handle(args: argparse.Namespace) -> None:
    svc = CredentialService()
    cmd = args.credentials_cmd
    fmt = getattr(args, "output", "table")

    if cmd == "list":
        items = svc.list_credentials(provider_id=getattr(args, "provider_id", None))
        print_output(items, fmt, columns=_COLS)

    elif cmd == "show":
        c = svc.get_credential(args.id)
        if not c:
            print_error(f"Credential {args.id} introuvable", 1)
        print_output(c, fmt)

    elif cmd == "add":
        data = {"provider_id": args.provider_id, "name": args.name, "api_key": args.api_key}
        c = svc.create_credential(data)
        print_output(c, fmt)

    elif cmd == "edit":
        data = {}
        if args.name: data["name"] = args.name
        if args.api_key: data["api_key"] = args.api_key
        if args.active: data["active"] = args.active == "true"
        c = svc.update_credential(args.id, data)
        if not c:
            print_error(f"Credential {args.id} introuvable", 1)
        print_output(c, fmt)

    elif cmd == "delete":
        ok = svc.delete_credential(args.id)
        if not ok:
            print_error(f"Credential {args.id} introuvable", 1)
        else:
            print(f"Credential {args.id} supprimé.")

    elif cmd == "test":
        result = svc.test_connection(args.id)
        print_output(result.__dict__, fmt)

    else:
        print("Usage: app credentials <list|show|add|edit|delete|test>")
