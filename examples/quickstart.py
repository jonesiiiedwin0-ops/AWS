"""Quickstart: run the server in-process and call its HTTP API.

Run with:
    python examples/quickstart.py
"""

from fastapi.testclient import TestClient

from aws_mcp_server import Config, MCPServer


def main() -> None:
    # Enable only the services we want to demo.
    config = Config(
        aws_region="us-east-1",
        enabled_services=["s3", "ec2", "lambda"],
    )
    server = MCPServer(config)

    # TestClient lets us exercise the API without binding a socket.
    client = TestClient(server.app)

    print("Health:", client.get("/health").json())
    print("Services:", client.get("/services").json())

    tools = client.get("/tools").json()
    print(f"\n{tools['count']} tools available. First five:")
    for tool in tools["tools"][:5]:
        print(f"  - {tool['name']}: {tool['description']}")

    print("\nOpenAPI docs are served at /docs when running live.")


if __name__ == "__main__":
    main()
