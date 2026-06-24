<div align="center">

# AWS MCP Server

**A Model Context Protocol (MCP) server for safe, read-first access to AWS services.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)
[![CI](https://github.com/jonesiiiedwin0-ops/AWS/actions/workflows/ci.yml/badge.svg)](https://github.com/jonesiiiedwin0-ops/AWS/actions/workflows/ci.yml)
[![Stars](https://img.shields.io/github/stars/jonesiiiedwin0-ops/AWS.svg)](https://github.com/jonesiiiedwin0-ops/AWS/stargazers)

[Quick Start](#-quick-start) •
[Configuration](#-configuration) •
[Roadmap](#-roadmap) •
[Contributing](#-contributing) •
[Strategy](STRATEGY.md)

</div>

---

> **Project status: early foundation.** This repository currently ships a
> minimal, installable server skeleton plus the project scaffolding (CI, tests,
> docs, contributor guides). The service implementations are being built out in
> the open — see the [Roadmap](#-roadmap) and [STRATEGY.md](STRATEGY.md). We
> document what exists today, not what we wish existed.

## 🌟 Overview

The **AWS MCP Server** lets any [Model Context Protocol](https://modelcontextprotocol.io)
client (such as Claude Desktop or IDE extensions) talk to AWS through a single,
standardized interface — **read-only by default**, with mutating actions gated
behind an explicit opt-in.

### Why MCP?

Model Context Protocol is an open standard for connecting AI applications to
external tools and data. Implementing it once means this server works with every
MCP-compatible client, no custom glue required.

### Design principles

- 🔒 **Safe by default** — read-only unless you explicitly enable writes.
- ⚡ **Fast to start** — install and connect in minutes, no code to write.
- 🧩 **Modular** — enable only the services you need.
- 🧪 **Tested** — CI runs lint, type-check, and tests on every change (against
  mocked AWS, so no account is needed to contribute).

## 🛠️ Planned service coverage

The MVP targets the services people most often ask an AI about:

| Service | Capability (MVP) | Status |
|---------|------------------|--------|
| S3      | List buckets/objects, sizes | 🚧 In progress |
| EC2     | Describe instances, state    | 🚧 In progress |
| Lambda  | List/describe functions      | 📋 Planned |
| CloudWatch | Read metrics & logs       | 📋 Planned |
| Cost Explorer | Cost & usage summaries | 📋 Planned |

Additional services are tracked on the [Roadmap](#-roadmap).

## 📋 Prerequisites

- **Python 3.10+**
- **AWS credentials** configured via the standard chain (env vars, shared
  credentials file, or an instance/role profile).
- An MCP-compatible client.

## 🚀 Quick Start

> Packaging to PyPI is planned. For now, install from source.

```bash
# Clone
git clone https://github.com/jonesiiiedwin0-ops/AWS.git
cd AWS

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install (editable)
pip install -e ".[dev]"

# Verify the install
aws-mcp-server --version
aws-mcp-server --help
```

Run the server:

```bash
aws-mcp-server          # read-only by default
```

To connect it to an MCP client, add a server entry pointing at the
`aws-mcp-server` command. A worked example for Claude Desktop:

```json
{
  "mcpServers": {
    "aws": {
      "command": "aws-mcp-server",
      "env": { "AWS_REGION": "us-east-1" }
    }
  }
}
```

## ⚙️ Configuration

Configuration comes from environment variables (see [`.env.example`](.env.example)):

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_REGION` | `us-east-1` | Default AWS region |
| `AWS_MCP_READ_ONLY` | `true` | Block all mutating actions when `true` |
| `AWS_MCP_ENABLED_SERVICES` | `s3,ec2` | Comma-separated services to enable |
| `AWS_MCP_LOG_LEVEL` | `INFO` | Logging verbosity |

Standard AWS credential variables (`AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY`, `AWS_PROFILE`, …) are honored via boto3's default
chain. **Never commit credentials** — `.env` is git-ignored.

## 🔒 Security

- **Read-only by default.** Set `AWS_MCP_READ_ONLY=false` only when you
  intend to allow writes, and prefer per-action confirmation.
- Use a **least-privilege IAM policy**. A generator is on the roadmap.
- Report vulnerabilities privately — see [SECURITY.md](SECURITY.md).

## 🗺️ Roadmap

The full, phased plan lives in **[STRATEGY.md](STRATEGY.md)**. In brief:

- **Phase 0 — Foundation** *(current)*: installable skeleton, CI, tests, docs.
- **Phase 1 — MVP**: five read-only services, sub-5-minute setup.
- **Phase 2 — Trust**: safety rails, audit logging, IAM policy generator.
- **Phase 3 — Reach**: docs site, registry listings, client configs.
- **Phase 4+ — Depth & platform**: more services, plugin API, 1.0.

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) and
our [Code of Conduct](CODE_OF_CONDUCT.md). Good first issues are labeled
`good first issue`.

```bash
pip install -e ".[dev]"
ruff check .         # lint
pytest               # tests
```

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE).
