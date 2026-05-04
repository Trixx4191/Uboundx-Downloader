# unboundx

A simple Python tool called **UnboundX Downloader** that mirrors any **Apache / nginx directory listing** — like those on infocon.org — and downloads all videos, slides, and PDFs while preserving the exact folder structure from the site.

---

## Features

- Recursively crawls nested subdirectories
- Mirrors the remote folder structure locally
- Skips files that already exist (safe to re-run / resume)
- Live progress bar showing `%` and MB per file
- Configurable via `config.py` or CLI flags
- Polite request delay to avoid hammering the server

---

## Quick start

```bash
# 1. Clone / download the files
git clone https://github.com/you/unboundx
cd unboundx

# 2. Install dependencies
pip install -r requirements.txt

# 3. Edit config.py to set your URL, then run
python downloader.py
```

---

## Usage

### Option A — edit `config.py`

Open `config.py` and set `BASE_URL` to the directory you want to mirror:

```python
BASE_URL   = "https://infocon.org/skills/pwn.college%20-%20Hacking/Slides/04%20Reverse%20Engineering/"
OUTPUT_DIR = "./downloads"
EXTENSIONS = ["mp4", "mkv", "pdf", "pptx", "ppt"]
```

Then just run:

```bash
python downloader.py
```

### Option B — CLI flags (override config.py)

| Flag | Description | Example |
|------|-------------|---------|
| `--url` | Base URL to crawl | `--url https://infocon.org/cons/DEF%20CON/` |
| `--out` | Output directory | `--out ./defcon` |
| `--ext` | File extensions | `--ext mp4 pdf` |
| `--delay` | Seconds between requests | `--delay 1.0` |

```bash
# Download only videos from a specific con
python downloader.py \
  --url "https://infocon.org/cons/DEF%20CON/DEF%20CON%2031/" \
  --out ./defcon31 \
  --ext mp4 mkv

# Download slides only
python downloader.py \
  --url "https://infocon.org/skills/pwn.college%20-%20Hacking/Slides/" \
  --ext pdf pptx ppt
```

---

## Output structure

The tool mirrors the site's folder structure exactly. For example, crawling:

```
https://infocon.org/skills/pwn.college - Hacking/Slides/04 Reverse Engineering/
```

Produces:

```
downloads/
└── 04 Reverse Engineering/
    ├── 01 - intro.mp4
    ├── 01 - intro.pdf
    ├── 02 - tools.mp4
    └── 02 - tools.pptx
```

If you crawl a parent directory with multiple subdirectories, they all appear under `downloads/` mirroring the remote layout.

---

## Configuration reference

All settings live in `config.py`. CLI flags override them at runtime.

| Setting | Default | Description |
|---------|---------|-------------|
| `BASE_URL` | (pwn.college RE slides) | Directory URL to crawl |
| `OUTPUT_DIR` | `./downloads` | Local root for saved files |
| `EXTENSIONS` | `mp4 mkv pdf pptx ppt` | File types to download |
| `DELAY_SEC` | `0.5` | Seconds between requests |
| `TIMEOUT_SEC` | `120` | Per-file download timeout |

---

## Requirements

- Python 3.10+
- `requests` ≥ 2.28
- `beautifulsoup4` ≥ 4.12

Install with:

```bash
pip install -r requirements.txt
```

---

## Works with any directory listing

This tool is not specific to infocon.org. It works with any site that serves a standard Apache or nginx **"Index of /"** directory listing — the plain HTML page with a table of links you get when there's no `index.html`.

---

## Notes

- Files that already exist locally are skipped, so you can safely re-run the script to resume an interrupted download or pick up new files added to the site.
- Partial files from failed downloads are automatically deleted so the next run retries them cleanly.
- Press `Ctrl+C` at any time to stop.
