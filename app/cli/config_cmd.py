import argparse
import json

from app.services.export_service import ExportService
from .output import print_error


def add_subparser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("config", help="Import/export de configuration")
    s = p.add_subparsers(dest="config_cmd")

    ce = s.add_parser("export")
    ce.add_argument("--output", dest="output_file")
    ce.add_argument("--no-providers", action="store_false", dest="include_providers")
    ce.add_argument("--no-models", action="store_false", dest="include_models")

    ci = s.add_parser("import")
    ci.add_argument("--file", required=True, dest="input_file")


def handle(args: argparse.Namespace) -> None:
    svc = ExportService()
    cmd = args.config_cmd

    if cmd == "export":
        data = svc.export_config(
            include_providers=getattr(args, "include_providers", True),
            include_models=getattr(args, "include_models", True),
        )
        text = json.dumps(data, ensure_ascii=False, indent=2, default=str)
        if args.output_file:
            with open(args.output_file, "w") as f:
                f.write(text)
            print(f"Configuration exportée vers {args.output_file}")
        else:
            print(text)

    elif cmd == "import":
        try:
            with open(args.input_file) as f:
                data = json.load(f)
        except Exception as e:
            print_error(f"Impossible de lire {args.input_file}: {e}", 3)
        result = svc.import_config(data)
        print(f"Importé: {result['providers_added']} providers, {result['models_added']} modèles")
        if result["errors"]:
            print(f"Erreurs: {result['errors']}")

    else:
        print("Usage: app config <export|import>")
