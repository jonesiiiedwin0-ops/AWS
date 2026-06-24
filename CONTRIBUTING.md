# Contributing to AWS MCP Server

Thanks for your interest in contributing! This project aims to be welcoming and
easy to contribute to — that is a core part of the [strategy](STRATEGY.md).

## Ground rules

- Be respectful — see the [Code of Conduct](CODE_OF_CONDUCT.md).
- Keep PRs focused and small where possible.
- Every behavior change needs a test.
- CI must be green (lint + tests) before review.

## Development setup

```bash
git clone https://github.com/jonesiiiedwin0-ops/AWS.git
cd AWS
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

You do **not** need an AWS account to develop or run the test suite — tests run
against mocked AWS.

## Before you push

```bash
ruff check .      # lint (use `ruff check . --fix` to autofix)
pytest            # run the test suite
```

## Pull requests

1. Fork and create a feature branch.
2. Make your change with tests and docs.
3. Ensure `ruff check .` and `pytest` pass.
4. Open a PR with a clear description of the *why*, not just the *what*.

## Good first issues

Look for issues labeled `good first issue`. If you'd like to pick one up,
comment on it so we can avoid duplicate work.

## Reporting bugs / requesting features

Open an issue using the appropriate template. For security issues, please
follow [SECURITY.md](SECURITY.md) instead of filing a public issue.
