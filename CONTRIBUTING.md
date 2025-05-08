# Contributing to DuckDB LLM UDF

First off, thank you for considering contributing to DuckDB LLM UDF! It's people like you that make the open source community such a great place to learn, inspire, and create. Your contributions are welcome and appreciated.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Process](#development-process)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** to your local machine
   ```bash
   git clone https://github.com/your-username/duckdb_llm_udf.git
   cd duckdb_llm_udf
   ```
3. **Set up your development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```
4. **Create a new branch** for your feature/fix
   ```bash
   git checkout -b feature/your-feature-name
   ```

## How Can I Contribute?

### Reporting Bugs

- **Ensure the bug was not already reported** by searching on GitHub under [Issues](https://github.com/username/duckdb_llm_udf/issues)
- If you're unable to find an open issue addressing the problem, [open a new one](https://github.com/username/duckdb_llm_udf/issues/new)
- Include a **title and clear description**
- As much relevant information as possible
- A **code sample** or an **executable test case** demonstrating the expected behavior that is not occurring

### Suggesting Enhancements

- Open a new issue with a clear title and detailed description
- Explain why this enhancement would be useful to most users
- List some examples of how it would work in practice

### Pull Requests

- Fill in the required template
- Do not include issue numbers in the PR title
- Include screenshots and animated GIFs in your PR whenever possible
- Follow the Python style guide
- Include adequate tests
- Document new code

## Development Process

1. **Run tests** to ensure everything works before making changes
   ```bash
   pytest
   ```
2. **Make your changes** and add appropriate tests
3. **Run tests again** to ensure your changes don't break existing functionality
4. **Update the documentation** if necessary
5. **Commit your changes** following our commit message guidelines

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the version numbers following [Semantic Versioning](https://semver.org/)
3. Your PR will be merged once it has been approved by at least one maintainer

## Style Guidelines

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests after the first line

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use docstrings for all public methods and classes
- Use type hints when possible

### Documentation

- Use Markdown for documentation
- Keep language clear and concise
- Include examples where appropriate

Thank you for contributing to DuckDB LLM UDF! Your efforts make this project better for everyone.
