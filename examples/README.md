# Examples

This directory contains runnable examples demonstrating the AWS MCP Server.

| Example | Description |
|---------|-------------|
| [`quickstart.py`](quickstart.py) | Start the server programmatically and hit the API |
| [`use_services.py`](use_services.py) | Call AWS services directly via the registry |
| [`mock_demo.py`](mock_demo.py) | End-to-end demo using `moto` (no real AWS account needed) |
| [`config.example.yaml`](config.example.yaml) | Sample YAML configuration |
| [`.env.example`](.env.example) | Sample environment variables |

## Running the mock demo (no AWS account)

```bash
pip install -r ../requirements.txt
python mock_demo.py
```

This spins up mocked S3 and EC2 using `moto`, creates a bucket and an instance,
then lists them through the service registry — proving the full path works
without touching real AWS.

## Running against real AWS

1. Configure credentials (`aws configure` or environment variables).
2. Use **read-only** IAM permissions to start safely.

```bash
python use_services.py
```
