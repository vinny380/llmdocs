---
title: "Contributing"
description: "How to report issues, propose features, and submit pull requests to llmdocs."
category: "Contributing"
order: 40
tags: [contributing, pr, community]
---

# Contributing

Thank you for helping improve **llmdocs**. This project is **MIT-licensed**; contributions are welcome under the same license.

## Issues

- **Bugs:** Include Python version, `llmdocs --version`, minimal `llmdocs.yaml`, and steps to reproduce.
- **Features:** Describe the user story (CLI user, Docker operator, MCP client) and any constraints.

## Pull requests

1. **Fork** and create a **branch** from `main`.
2. For **behavior changes**, prefer **tests first** (see [Development](./development.md)).
3. Keep diffs **focused**; avoid unrelated refactors.
4. Run **`pytest`** locally before pushing.
5. Match existing **style** (typing, Pydantic v2, Click patterns).

## Scope

- The **CLI** is the supported user interface — avoid expanding `llmdocs` as a public Python SDK without discussion.
- **Dependencies:** update `pyproject.toml` and **locked** `requirements.txt` / `requirements-dev.txt` together.

## Code of conduct

Be respectful and constructive. See [Code of conduct](../community/code-of-conduct.md).
