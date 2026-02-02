import argparse

from src.logger import setup_logging


def main() -> None:
    """Parse arguments and run the appropriate mode."""
    parser = argparse.ArgumentParser(
        description="Voice Assistant - Local AI-powered voice assistant"
    )
    parser.add_argument(
        "--mode",
        choices=["cli", "web"],
        default="web",
        help="Run mode: 'cli' for terminal, 'web' for Gradio UI (default: cli)",
    )
    args = parser.parse_args()

    setup_logging()

    if args.mode == "web":
        from src.interface.ui.app import run as run_web
        run_web()
    else:
        from src.interface.cli.app import run as run_cli
        run_cli()


if __name__ == "__main__":
    main()
