# CLI

Entry point: `python main.py <COMMAND> --resume <path-to-pdf>`

## Commands

### `discover`

Weekly **exploration** run. Defaults:

| Setting | Value |
|---------|--------|
| Filter | lenient (unknown stipend/duration allowed) |
| Rich reports | off |
| limit / top_k | 30 / 10 |

```bash
python main.py discover --resume uploads/resume.pdf --no-llm --no-embeddings
```

Use when you want the broadest set of listings (e.g. after cache replay or `--jobs-csv`).

### `shortlist`

**Apply-ready** run. Defaults:

| Setting | Value |
|---------|--------|
| Filter | strict (known stipend/duration required) |
| Rich reports | on (LLM coaching path; see issue #005) |
| limit / top_k | 30 / 5 |

```bash
python main.py shortlist --resume uploads/resume.pdf
```

Use when you want fewer, higher-confidence matches.

## Overrides

Profile defaults are starting points. Explicit flags win:

- `--lenient` / `--no-lenient` — filter mode
- `--rich-reports` / `--no-rich-reports` — coaching depth
- `--limit`, `--top-k`, `--min-stipend`, `--min-duration`, `--role`
- `--jobs-csv`, `--internship-url`, `--live`, `--allow-sample-fallback`
- `--no-llm`, `--no-embeddings`
- `--ollama-fast-model` (default `qwen2.5:3b`) — JD parsing
- `--ollama-large-model` (default `qwen2.5:7b`) — company research
- `--ollama-url` — Ollama base URL

Example: strict exploration with a smaller report set:

```bash
python main.py discover --resume uploads/resume.pdf --no-lenient --top-k 5
```
