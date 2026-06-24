"""Command-line entry point for the AWS MCP Server."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .config import Config
from .server import build_server, configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aws-mcp-server",
        description="A Model Context Protocol server for safe, read-first access to AWS.",
    )
    parser.add_argument("--version", action="version", version=f"aws-mcp-server {__version__}")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate configuration and exit without starting the server.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    config = Config.from_env()
    configure_logging(config.log_level)
    server = build_server(config)

    if args.check:
        print(
            "Configuration OK | region={region} read_only={ro} services={svc}".format(
                region=config.region,
                ro=config.read_only,
                svc=",".join(config.enabled_services),
            )
        )
        return 0

    try:
        server.run()
    except NotImplementedError as exc:
        print(f"aws-mcp-server: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
