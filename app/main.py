"""Application entry point — GUI or CLI depending on arguments."""
import sys


def main() -> int:
    if "--cli" in sys.argv:
        idx = sys.argv.index("--cli")
        cli_args = sys.argv[idx + 1:]
        from app.cli import main as cli_main
        return cli_main(cli_args)
    else:
        from app.storage.db import get_db
        from app.storage.seed import seed
        get_db()
        seed(force="--reseed" in sys.argv)
        from app.ui.app_window import AppWindow
        app = AppWindow()
        app.run()
        return 0


if __name__ == "__main__":
    sys.exit(main())
