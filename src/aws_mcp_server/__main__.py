"""Entry point for AWS MCP Server."""

import asyncio
import sys
import logging
from .server import MCPServer
from .config import Config


def setup_logging(config: Config) -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=config.log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def main() -> None:
    """Main entry point."""
    config = Config()
    setup_logging(config)

    server = MCPServer(config)
    await server.start(host=config.server_host, port=config.server_port)


def run() -> None:
    """Run the server."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer shutdown gracefully")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
