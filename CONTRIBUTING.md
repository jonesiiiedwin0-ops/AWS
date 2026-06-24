# Contributing to AWS MCP Server

First off, thank you for considering contributing to AWS MCP Server! It's people like you that make AWS MCP Server such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* **Use a clear and descriptive title**
* **Describe the exact steps which reproduce the problem**
* **Provide specific examples to demonstrate the steps**
* **Describe the behavior you observed after following the steps**
* **Explain which behavior you expected to see instead and why**
* **Include screenshots and animated GIFs if possible**
* **Include your environment details** (OS, Python version, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* **Use a clear and descriptive title**
* **Provide a step-by-step description of the suggested enhancement**
* **Provide specific examples to demonstrate the steps**
* **Describe the current behavior and the expected behavior**
* **Explain why this enhancement would be useful**

### Pull Requests

* Follow the Python style guide (PEP 8)
* Include appropriate test cases
* Update documentation as needed
* End all files with a newline

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git
- Virtual environment (recommended)

### Setup Steps

```bash
# Clone the repository
git clone https://github.com/jonesiiiedwin0-ops/aws.git
cd aws

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

## Development Workflow

### Creating a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_specific.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/

# Run all checks
black src/ tests/ && ruff check src/ tests/ && mypy src/
```

### Commit Messages

Write clear and descriptive commit messages:

```
Add feature X

Describe what your change does and why it's needed.
Reference issues if applicable: #123
```

### Submitting Changes

1. Push your branch to your fork
2. Create a pull request from your feature branch
3. Describe your changes in the PR description
4. Respond to any feedback or requests

## Styleguides

### Python Code Style

We follow PEP 8 with some customizations:

* Use 4 spaces for indentation
* Maximum line length is 100 characters
* Use type hints for function parameters and returns
* Write docstrings for all public modules, functions, classes, and methods

### Docstring Format

```python
"""Brief description of function.

Longer description if needed.

Args:
    param1: Description of param1
    param2: Description of param2

Returns:
    Description of return value

Raises:
    ValueError: When something is invalid
"""
```

### Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

## Testing

### Writing Tests

Tests should be placed in the `tests/` directory and follow this pattern:

```python
import pytest
from aws_mcp_server import MCPServer

def test_server_initialization():
    """Test server initialization."""
    server = MCPServer()
    assert server is not None

@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    server = MCPServer()
    # Test implementation
```

### Test Coverage

Aim for at least 80% code coverage. Check coverage with:

```bash
pytest --cov=src --cov-report=html
```

## Documentation

### Updating Documentation

* Update `README.md` for general information
* Update docs in `docs/` folder for detailed guides
* Add docstrings to code
* Update `CHANGELOG.md` with significant changes

### Building Documentation Locally

```bash
# Install documentation dependencies
pip install sphinx sphinx-rtd-theme

# Build documentation
cd docs
make html
```

## Questions?

Feel free to open an issue with the `question` label or start a discussion in our GitHub Discussions page.

---

Thank you for contributing! 🎉
