# Examples

- **`demo_index.py`** — builds a tiny docs tree in a temp directory, indexes with Chroma + embeddings, runs a hybrid search, prints top hits.
- **`run.sh`** — `cd` to repo root and runs `demo_index.py`.

From the repository root (with the package installed):

```bash
pip install -e .
python example/demo_index.py
```

Or: `bash example/run.sh`
