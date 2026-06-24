#!/usr/bin/env python
"""Setup script for AWS MCP Server."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="aws-mcp-server",
    version="0.2.0",
    author="jonesiiiedwin0-ops",
    description="A powerful MCP server for AWS services integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jonesiiiedwin0-ops/aws",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "aws-mcp-server=aws_mcp_server.__main__:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
