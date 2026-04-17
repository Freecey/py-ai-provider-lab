import argparse
import sys

from app.services.test_service import TestService
from .output import print_output, print_error


def add_subparser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("run", help="Lancer un test")
    s = p.add_subparsers(dest="run_cmd")

    # text
    rt = s.add_parser("text")
    rt.add_argument("--credential", type=int, required=True, dest="credential_id")
    rt.add_argument("--model", type=int, required=True, dest="model_id")
    rt.add_argument("--prompt", required=True)
    rt.add_argument("--system")
    rt.add_argument("--temperature", type=float)
    rt.add_argument("--max-tokens", type=int, dest="max_tokens")
    rt.add_argument("--stream", action="store_true")
    rt.add_argument("--output", choices=["table", "json", "plain"], default="plain")

    # image
    ri = s.add_parser("image")
    ri.add_argument("--credential", type=int, required=True, dest="credential_id")
    ri.add_argument("--model", type=int, required=True, dest="model_id")
    ri.add_argument("--prompt", required=True)
    ri.add_argument("--size", default="1024x1024")
    ri.add_argument("--output", choices=["table", "json", "plain"], default="plain")

    # audio
    ra = s.add_parser("audio")
    ra.add_argument("--credential", type=int, required=True, dest="credential_id")
    ra.add_argument("--model", type=int, required=True, dest="model_id")
    ra.add_argument("--file", dest="file_path")
    ra.add_argument("--op", default="transcription", dest="operation",
                    choices=["transcription", "speech", "translation"])
    ra.add_argument("--output", choices=["table", "json", "plain"], default="plain")


def handle(args: argparse.Namespace) -> None:
    svc = TestService()
    cmd = args.run_cmd
    fmt = getattr(args, "output", "plain")

    if cmd == "text":
        params = {"user_prompt": args.prompt}
        if args.system: params["system_prompt"] = args.system
        if args.temperature is not None: params["temperature"] = args.temperature
        if args.max_tokens: params["max_tokens"] = args.max_tokens
        on_chunk = None
        if args.stream:
            def on_chunk(delta): print(delta, end="", flush=True)
        run = svc.run_text(args.credential_id, args.model_id, params, on_chunk=on_chunk)
        if args.stream: print()
        if fmt == "json":
            print_output(run, "json")
        else:
            print(f"\n[{run.status}] latence={run.latency_ms}ms")

    elif cmd == "image":
        params = {"prompt": args.prompt, "size": args.size}
        run = svc.run_image(args.credential_id, args.model_id, params)
        if fmt == "json":
            print_output(run, "json")
        else:
            print(f"[{run.status}] {(run.response_raw or '')[:200]}")

    elif cmd == "audio":
        params = {"operation": args.operation}
        run = svc.run_audio(args.credential_id, args.model_id, params, file_path=args.file_path)
        if fmt == "json":
            print_output(run, "json")
        else:
            print(f"[{run.status}] {(run.response_raw or '')[:500]}")

    else:
        print("Usage: app run <text|image|audio>")
