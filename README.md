<div align="center">

<img src="https://img.shields.io/badge/UnboundX-Downloader-4A90D9?style=for-the-badge&logo=python&logoColor=white" alt="UnboundX Downloader"/>

**Mirror any Apache / nginx directory listing to your local machine — fast, resumable, and polite.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)
[![Release](https://img.shields.io/github/v/release/Trixx4191/Uboundx-Downloader?style=flat-square&color=f59e0b)](https://github.com/Trixx4191/Uboundx-Downloader/releases)
[![Issues](https://img.shields.io/github/issues/Trixx4191/Uboundx-Downloader?style=flat-square)](https://github.com/Trixx4191/Uboundx-Downloader/issues)
[![Stars](https://img.shields.io/github/stars/Trixx4191/Uboundx-Downloader?style=flat-square&color=facc15)](https://github.com/Trixx4191/Uboundx-Downloader/stargazers)

[Features](#features) · [Quick Start](#quick-start) · [Usage](#usage) · [Configuration](#configuration-reference) · [Releases](https://github.com/Trixx4191/Uboundx-Downloader/releases)

</div>

---

## What is UnboundX Downloader?

UnboundX Downloader is a Python CLI tool that **recursively mirrors any Apache or nginx directory listing**  to your local machine — preserving the exact remote folder structure and downloading only what's new.

Perfect for archiving conference talks, security slides, PDFs, and course videos from open directory indexes.

---

## Features

| | Feature |
|---|---|
| 🔁 | **Recursive crawling** — follows nested subdirectories automatically |
| 🗂️ | **Structure mirroring** — remote folder layout reproduced exactly |
| ⏭️ | **Smart resume** — skips existing files; safe to re-run |
| 📊 | **Live progress bar** — real-time `%` and MB/s per file |
| ⚙️ | **Dual config** — set defaults in `config.py`, override with CLI flags |
| 🐢 | **Polite delay** — configurable pause between requests |
| 🧹 | **Clean partials** — failed/incomplete files are auto-removed |
| 🖥️ | **GUI mode** — optional `gui.py` for a desktop interface |

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/Trixx4191/Uboundx-Downloader.git
cd Uboundx-Downloader

# 2. Install dependencies
pip install -r requirements.txt

# 3. Edit config.py to set your target URL, then run
python downloader.py
```

> **Requires Python 3.10+**

---

## Usage

### Option A — Edit `config.py`

Open `config.py` and set your target:

```python
BASE_URL   = "https://infocon.org/cons/DEF%20CON/DEF%20CON%2031/"
OUTPUT_DIR = "./downloads"
EXTENSIONS = ["mp4", "mkv", "pdf", "pptx", "ppt"]
DELAY_SEC  = 0.5
```

Then run:

```bash
python downloader.py
```

### Option B — CLI Flags

Override any config value at runtime:

| Flag | Description | Example |
|------|-------------|---------|
| `--url` | Base URL to crawl | `--url https://infocon.org/cons/DEF%20CON/` |
| `--out` | Output directory | `--out ./defcon` |
| `--ext` | File extensions | `--ext mp4 pdf` |
| `--delay` | Seconds between requests | `--delay 1.0` |

**Examples:**

```bash
# Download all DEF CON 31 videos
python downloader.py \
  --url "https://infocon.org/cons/DEF%20CON/DEF%20CON%2031/" \
  --out ./defcon31 \
  --ext mp4 mkv

# Slides only
python downloader.py \
  --url "https://infocon.org/skills/pwn.college%20-%20Hacking/Slides/" \
  --ext pdf pptx ppt

# With a polite delay
python downloader.py \
  --url "https://example.com/lectures/" \
  --delay 2.0
```

### Option C — GUI Mode

```bash
python gui.py
```

---

## Output Structure

The tool mirrors the remote folder layout exactly. For example, crawling:

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

---

## Configuration Reference

All defaults live in `config.py`. CLI flags override at runtime.

| Setting | Default | Description |
|---------|---------|-------------|
| `BASE_URL` | *(pwn.college RE slides)* | Directory URL to crawl |
| `OUTPUT_DIR` | `./downloads` | Local root for saved files |
| `EXTENSIONS` | `mp4 mkv pdf pptx ppt` | File types to download |
| `DELAY_SEC` | `0.5` | Seconds between requests |
| `TIMEOUT_SEC` | `120` | Per-file download timeout |

---

## Requirements

| Package | Version |
|---------|---------|
| Python | ≥ 3.10 |
| `requests` | ≥ 2.28 |
| `beautifulsoup4` | ≥ 4.12 |

```bash
pip install -r requirements.txt
```

---

## Compatibility

Works with **any** site that serves a standard Apache or nginx `Index of /` directory listing — not just `infocon.org`. If the page shows a plain HTML table of file links, UnboundX can crawl it.

---

## Notes

- **Resume-safe** — re-running the script skips already-downloaded files and picks up new ones.
- **Partial cleanup** — files that fail mid-download are deleted so the next run retries cleanly.
- **Stop anytime** — press `Ctrl+C`; partial files are cleaned up automatically.

---

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

1. Fork the repo
2. Create a branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## License

[MIT](LICENSE) © 2025 Trixx4191

---

<div align="center">
  <sub>If this tool saved you time, consider giving it a ⭐</sub>
</div>
