# llmdocs

Agent-first documentation platform: MCP-oriented search, raw markdown URLs, and `llms.txt` generation — self-hosted.

## For users (CLI only)

Install from PyPI (when published) or from a checkout:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install .
llmdocs --help
llmdocs version
```

The `llmdocs` command is the supported interface. This package is **not** intended as a Python SDK; internal modules may change without notice.

## Development

Git history for this project lives **in this directory** (`git` is initialized here). If your editor opened a parent folder that is also a Git repo, run commands from `Projects/llmdocs` so commits apply only to llmdocs.

Use a virtualenv and locked dev requirements:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
pytest
```

## Docker

The production image installs dependencies from `requirements.txt`, then installs the package. (Dockerfile will be added in a later task.)

## License

MIT
