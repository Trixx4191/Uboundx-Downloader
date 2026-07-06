# UnboundX Downloader v1.0.0 🎉

**Initial public release**

---

## What's included

UnboundX Downloader is a Python CLI tool that recursively mirrors any Apache or nginx open directory listing to your local machine — preserving folder structure, skipping already-downloaded files, and cleaning up failed partials automatically.

---

## Features in this release

- **Recursive crawl** — follows nested subdirectories on any `Index of /` page
- **Structure mirroring** — remote folder layout reproduced locally, exactly
- **Smart resume** — skips existing files; safe to re-run after interruption
- **Live progress bar** — real-time percentage and MB display per file
- **CLI flags** — override `config.py` defaults on the fly (`--url`, `--out`, `--ext`, `--delay`)
- **GUI mode** — optional desktop interface via `gui.py`
- **Polite scraping** — configurable delay between requests (`DELAY_SEC`)
- **Auto-cleanup** — partial downloads from failed requests are deleted before next run

---

## Installation

```bash
git clone https://github.com/Trixx4191/Uboundx-Downloader.git
cd Uboundx-Downloader
pip install -r requirements.txt
python downloader.py
```

**Requirements:** Python 3.10+, `requests >= 2.28`, `beautifulsoup4 >= 4.12`

---

## Quick example

```bash
# Download all DEF CON 31 videos
python downloader.py \
  --url "https://infocon.org/cons/DEF%20CON/DEF%20CON%2031/" \
  --out ./defcon31 \
  --ext mp4 mkv
```

---

## Compatibility

Works with any site serving a standard Apache or nginx directory listing — not just `infocon.org`.

---

## What's next (planned for v1.1.0)

- [ ] Multi-threaded downloads
- [ ] `--dry-run` flag to preview without downloading
- [ ] `.uboundx` config file support
- [ ] Better error reporting with retry counts

---

**Full changelog:** https://github.com/Trixx4191/Uboundx-Downloader/commits/main
