"""JSON-only CLI for the environment variable agent.

Reads newline-delimited JSON commands from stdin, writes one JSON response
per line to stdout. This is the canonical "JSON only" interface: there is no
keyword argument parser for individual variables and no non-JSON output.

Example:
    echo '{"action":"set","args":{"key":"FOO","value":"bar"}}' | python -m env_agent
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from env_agent.agent import EnvAgent
from env_agent.models import EnvCommand
from env_agent.store import JsonStore


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="env_agent",
        description="Environment variable agent (JSON-only interface).",
    )
    parser.add_argument(
        "--store",
        default=None,
        help="Path to a JSON file used for persistence.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    store = JsonStore(path=args.store) if args.store else None
    agent = EnvAgent(store=store)
    if store is not None and store.exists():
        try:
            agent.handle(EnvCommand(action="load", args={}))
        except Exception:
            pass

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        print(agent.handle_json(line), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
