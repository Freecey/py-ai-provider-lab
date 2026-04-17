import argparse

from app.services.provider_service import ProviderService
from .output import print_output


def add_subparser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("health", help="Vérifier la santé des providers")
    p.add_argument("--provider", type=int, dest="provider_id")
    p.add_argument("--output", choices=["table", "json", "plain"], default="table")


def handle(args: argparse.Namespace) -> None:
    svc = ProviderService()
    fmt = getattr(args, "output", "table")
    provider_id = getattr(args, "provider_id", None)

    if provider_id:
        from app.storage.repositories.credential_repo import CredentialRepository
        from app.storage.db import get_conn
        creds = CredentialRepository(get_conn()).list(provider_id=provider_id)
        if not creds:
            print(f"Aucun credential pour le provider {provider_id}")
            return
        result = svc.health_check(provider_id, creds[0].id)
        print_output([result.__dict__], fmt)
    else:
        results = svc.health_check_all()
        rows = [v.__dict__ for v in results.values()]
        print_output(rows, fmt)
