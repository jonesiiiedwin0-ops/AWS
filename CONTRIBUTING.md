# Contributing to AWS MCP Server

Thank you for considering contributing to AWS MCP Server!

## How Can I Contribute?

### Reporting Bugs

Create an issue with:
- Clear and descriptive title
- Step-by-step reproduction steps
- Expected vs actual behavior
- Environment details (OS, Python version)

### Suggesting Features

Submit an issue describing:
- Use case and motivation
- Example implementation
- Potential drawbacks

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests: `pytest`
5. Run linting: `black src/ && ruff check src/`
6. Commit with clear message
7. Push and create a Pull Request

## Development Setup

```bash
git clone https://github.com/jonesiiiedwin0-ops/aws.git
cd aws
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running Tests

```bash
pytest
pytest --cov=src
pytest -v
```

## Code Style

- Follow PEP 8
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Write docstrings for all public functions

Thank you for contributing!
