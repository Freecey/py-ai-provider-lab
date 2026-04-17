"""CLI entry point — invoked via: python main.py --cli <subcommand> [args]"""
import argparse
import sys

from app.cli import providers, credentials, models, run, history, health
from app.cli import config_cmd


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app",
        description="py-ai-provider-lab CLI",
    )
    parser.add_argument("--debug", action="store_true", help="Activer les logs HTTP détaillés")
    sub = parser.add_subparsers(dest="command")

    providers.add_subparser(sub)
    credentials.add_subparser(sub)
    models.add_subparser(sub)
    run.add_subparser(sub)
    history.add_subparser(sub)
    health.add_subparser(sub)
    config_cmd.add_subparser(sub)

    return parser


def main(argv: "list[str] | None" = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.debug:
        import logging
        logging.getLogger("http_client").setLevel(logging.DEBUG)
        logging.getLogger("app").setLevel(logging.DEBUG)

    # Init DB + seed on first run
    from app.storage.db import get_db
    from app.storage.seed import seed
    get_db()
    seed()

    if args.command == "providers":
        providers.handle(args)
    elif args.command == "credentials":
        credentials.handle(args)
    elif args.command == "models":
        models.handle(args)
    elif args.command == "run":
        run.handle(args)
    elif args.command == "history":
        history.handle(args)
    elif args.command == "health":
        health.handle(args)
    elif args.command == "config":
        config_cmd.handle(args)
    else:
        parser.print_help()
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
