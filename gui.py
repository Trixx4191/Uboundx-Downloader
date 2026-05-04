#!/usr/bin/env python3
"""
UnboundX Downloader — GUI (Debug Fixed)
Run: python gui.py
"""

import os
import sys
import time
import queue
import threading
import urllib.parse
import tkinter as tk
from tkinter import filedialog
from datetime import datetime

from bs4 import BeautifulSoup

try:
    import config as cfg
except ImportError:
    cfg = None

try:
    from curl_cffi import requests as curl_requests
    _SESSION = curl_requests.Session(impersonate="chrome120")
    _BACKEND = "curl_cffi chrome120"
except ImportError:
    import requests as _fallback
    _SESSION = _fallback.Session()
    _BACKEND = "requests (install curl_cffi for TLS bypass)"

_SESSION.headers.update(getattr(cfg, 'HEADERS', {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
}))

# constants 

BG       = "#0a0e0a"
BG2      = "#0d1a0d"
GREEN    = "#00ff41"
GREEN2   = "#00cc33"
GREEN3   = "#007a1f"
DIM      = "#1a2e1a"
DIMMER   = "#112211"
AMBER    = "#ffb800"
RED      = "#ff3333"
GRAY     = "#4a6a4a"
FONT_M   = ("Courier New", 11)
FONT_S   = ("Courier New", 9)
FONT_L   = ("Courier New", 13, "bold")
FONT_XL  = ("Courier New", 18, "bold")
CHUNK    = 256 * 1024

DEFAULT_EXTS = ["mp4", "mkv", "pdf", "pptx", "ppt" , "zip"]

_base_url   = ""
_stop_event = threading.Event()
_msg_queue  = queue.Queue()

# download logic 

def url_to_local(file_url, base_url, output_dir):
    relative = urllib.parse.unquote(file_url[len(base_url):])
    return os.path.join(output_dir, relative.lstrip("/"))

def is_target(href, exts):
    lower = href.lower().split("?")[0]
    return any(lower.endswith("." + e) for e in exts)

def is_subdir(href):
    return (href.endswith("/") and not href.startswith("?")
            and not href.startswith("/") and not href.startswith("http")
            and href != "../")

def msg(kind, **kw):
    _msg_queue.put({"kind": kind, **kw})

def scrape(url, output_dir, exts, delay, timeout, stats):
    if _stop_event.is_set():
        return
    msg("log", text=f"SCAN  {url}", color=GREEN2)

    for attempt in range(1, 4):
        if _stop_event.is_set():
            return
        try:
            r = _SESSION.get(url, timeout=30)
            r.raise_for_status()
            break
        except Exception as e:
            status = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            if status == 403:
                msg("log", text=f"403 Forbidden - WAF/Cloudflare: {url}", color=RED)
                msg("log", text="Try higher delay or cloudscraper.", color=AMBER)
                return
            if attempt == 3:
                msg("log", text=f"FAIL  {url}  ({e})", color=RED)
                return
            wait = attempt * 3
            msg("log", text=f"ERR   attempt {attempt}/3 — retry in {wait}s", color=AMBER)
            time.sleep(wait)

    soup  = BeautifulSoup(r.text, "html.parser")
    links = [a.get('href') for a in soup.find_all("a", href=True) if a.get('href')]

    # Dir listing validation
    text_lower = r.text.lower()
    if len(links) == 0 or 'index of' not in text_lower:
        msg("log", text=f"FAIL No dir listing/blocked (WAF/SPA): {url}", color=RED)
        msg("log", text="Expected 'Index of /' page. For JS sites use browser tool.", color=AMBER)
        return
    text_lower = r.text.lower()
    if "wordpress" in text_lower or "wp-content" in text_lower:
        msg("log", text="WARN: WordPress site. Needs 'Index of /' listing.", color=AMBER)
    elif "youtube" in url.lower():
        msg("log", text="WARN: YouTube - use yt-dlp. Dir listings only.", color=AMBER)

    for href in links:
        if _stop_event.is_set():
            return
        abs_url = urllib.parse.urljoin(url, href)
        if is_target(href, exts):
            local = url_to_local(abs_url, _base_url, output_dir)
            download_file(abs_url, local, timeout, stats)
            time.sleep(delay)
        elif is_subdir(href):
            scrape(abs_url, output_dir, exts, delay, timeout, stats)

def download_file(url, local_path, timeout, stats):
    if _stop_event.is_set():
        return
    filename = os.path.basename(local_path)

    if os.path.exists(local_path):
        msg("log", text=f"SKIP  {filename}", color=GRAY)
        stats["skipped"] += 1
        msg("stats", **stats)
        return

    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    msg("log", text=f"DL    {filename}", color=GREEN)
    msg("file_start", name=filename)

    for attempt in range(1, 4):
        if _stop_event.is_set():
            return
        try:
            r = _SESSION.get(url, stream=True, timeout=timeout)
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            done  = 0

            with open(local_path, "wb") as fh:
                for chunk in r.iter_content(chunk_size=CHUNK):
                    if _stop_event.is_set():
                        fh.close()
                        os.remove(local_path)
                        return
                    fh.write(chunk)
                    done += len(chunk)
                    msg("progress", done=done, total=total, name=filename)

            stats["downloaded"] += 1
            stats["bytes"] += done
            msg("stats", **stats)
            msg("file_done", name=filename)
            msg("log", text=f"DONE  {filename}  ({done/1e6:.1f} MB)", color=GREEN)
            return

        except Exception as e:
            msg("log", text=f"ERR   {filename} attempt {attempt}/3: {e}", color=AMBER)
            if os.path.exists(local_path):
                os.remove(local_path)
            if attempt < 3:
                time.sleep(attempt * 3)

    stats["failed"] += 1
    msg("stats", **stats)
    msg("log", text=f"FAIL  {filename}", color=RED)

def run_download(url, output_dir, exts, delay, timeout):
    global _base_url
    _base_url = url
    stats = {"downloaded": 0, "skipped": 0, "failed": 0, "bytes": 0}
    msg("log", text=f"{'='*54}", color=GREEN3)
    msg("log", text=f"TARGET  {url}", color=GREEN)
    msg("log", text=f"OUTPUT  {output_dir}", color=GREEN2)
    msg("log", text=f"TYPES   {' '.join(exts)}", color=GREEN2)
    msg("log", text=f"BACKEND {_BACKEND}", color=GREEN2)
    msg("log", text=f"{'='*54}", color=GREEN3)

    try:
        scrape(url, output_dir, exts, delay, timeout, stats)
    except Exception as e:
        msg("log", text=f"FATAL {e}", color=RED)

    msg("log", text=f"{'='*54}", color=GREEN3)
    done_msg = f"DONE  ↓{stats['downloaded']}  skip:{stats['skipped']}  fail:{stats['failed']}  {stats['bytes']/1e6:.1f}MB"
    if stats['downloaded'] == 0:
        done_msg += " | No files found. Use Apache/nginx dir listing URL ('Index of /')."
    msg("log", text=done_msg, color=GREEN)
    msg("log", text=f"{'='*54}", color=GREEN3)
    msg("done")

# GUI 

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UNBOUNDX DOWNLOADER")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.geometry("860x700")
        self.minsize(700, 560)

        self._dl_thread = None
        self._anim_frame = 0
        self._anim_id    = None
        self._running    = False
        self._blink_on   = True
        self._blink_id   = None

        self._build_ui()
        self._start_blink()
        self.after(80, self._poll_queue)

    # UI construction 
    def _build_ui(self):
        # header 
        hdr = tk.Frame(self, bg=BG, pady=12)
        hdr.pack(fill="x", padx=18)

        tk.Label(hdr, text="▓▒░ UNBOUNDX DOWNLOADER ░▒▓",
                 font=("Courier New", 17, "bold"), fg=GREEN, bg=BG).pack(side="left")

        self._status_dot = tk.Label(hdr, text="●", font=("Courier New", 14),
                                    fg=GREEN3, bg=BG)
        self._status_dot.pack(side="right", padx=4)
        tk.Label(hdr, text="SYS:", font=FONT_S, fg=GREEN3, bg=BG).pack(side="right")

        tk.Frame(self, bg=GREEN3, height=1).pack(fill="x", padx=18)

        # URL row 
        url_row = tk.Frame(self, bg=BG, pady=10)
        url_row.pack(fill="x", padx=18)
        tk.Label(url_row, text="TARGET URL ▸", font=FONT_M, fg=GREEN3, bg=BG).pack(side="left", padx=(0,8))

        url_default = getattr(cfg, 'BASE_URL', '') if cfg else ''
        self._url_var = tk.StringVar(value=url_default)
        url_entry = tk.Entry(url_row, textvariable=self._url_var,
                             font=FONT_M, fg=GREEN, bg=DIMMER,
                             insertbackground=GREEN, relief="flat",
                             bd=0, highlightthickness=1,
                             highlightcolor=GREEN3, highlightbackground=GREEN3)
        url_entry.pack(side="left", fill="x", expand=True, ipady=6)

        # output row 
        out_row = tk.Frame(self, bg=BG, pady=4)
        out_row.pack(fill="x", padx=18)
        tk.Label(out_row, text="OUTPUT DIR ▸", font=FONT_M, fg=GREEN3, bg=BG).pack(side="left", padx=(0,8))

        out_default = getattr(cfg, 'OUTPUT_DIR', './downloads') if cfg else './downloads'
        self._out_var = tk.StringVar(value=out_default)
        out_entry = tk.Entry(out_row, textvariable=self._out_var,
                             font=FONT_M, fg=GREEN, bg=DIMMER,
                             insertbackground=GREEN, relief="flat",
                             bd=0, highlightthickness=1,
                             highlightcolor=GREEN3, highlightbackground=GREEN3)
        out_entry.pack(side="left", fill="x", expand=True, ipady=6)

        browse_btn = tk.Button(out_row, text=" BROWSE ", font=FONT_S,
                               fg=GREEN3, bg=DIM, relief="flat",
                               activeforeground=GREEN, activebackground=BG2,
                               cursor="hand2", command=self._browse)
        browse_btn.pack(side="left", padx=(6,0), ipady=4)

        # ext checkboxes 
        ext_row = tk.Frame(self, bg=BG, pady=8)
        ext_row.pack(fill="x", padx=18)
        tk.Label(ext_row, text="FILE TYPES ▸", font=FONT_M, fg=GREEN3, bg=BG).pack(side="left", padx=(0,8))

        self._ext_vars = {}
        for ext in ["mp4", "mkv", "pdf", "pptx", "ppt", "zip" ,"mp3", "jpeg", "png"]:
            v = tk.BooleanVar(value=ext in DEFAULT_EXTS)
            self._ext_vars[ext] = v
            cb = tk.Checkbutton(ext_row, text=ext, variable=v,
                                font=FONT_S, fg=GREEN, bg=BG,
                                selectcolor=DIM, activeforeground=GREEN,
                                activebackground=BG, relief="flat",
                                cursor="hand2")
            cb.pack(side="left", padx=4)

        tk.Frame(self, bg=GREEN3, height=1).pack(fill="x", padx=18)

        # current file progress 
        prog_frame = tk.Frame(self, bg=BG, pady=8)
        prog_frame.pack(fill="x", padx=18)

        self._file_label = tk.Label(prog_frame, text="IDLE", font=FONT_S,
                                    fg=GREEN3, bg=BG, anchor="w")
        self._file_label.pack(fill="x")

        # canvas progress bar
        self._bar_canvas = tk.Canvas(prog_frame, height=18, bg=DIMMER,
                                     highlightthickness=0, bd=0)
        self._bar_canvas.pack(fill="x", pady=(4,0))
        self._bar_fill   = self._bar_canvas.create_rectangle(0,0,0,18, fill=GREEN3, outline="")
        self._bar_glow   = self._bar_canvas.create_rectangle(0,0,0,18, fill=GREEN, outline="")
        self._bar_text   = self._bar_canvas.create_text(8, 9, text="", anchor="w",
                                                         font=("Courier New", 8, "bold"),
                                                         fill=BG)
        self._bar_canvas.bind("<Configure>", self._on_bar_resize)

        # stats row 
        stats_row = tk.Frame(self, bg=BG, pady=4)
        stats_row.pack(fill="x", padx=18)

        def stat_block(parent, label):
            f = tk.Frame(parent, bg=DIM, padx=12, pady=6)
            f.pack(side="left", padx=(0,8))
            tk.Label(f, text=label, font=("Courier New", 8), fg=GREEN3, bg=DIM).pack()
            val = tk.Label(f, text="0", font=("Courier New", 14, "bold"), fg=GREEN, bg=DIM)
            val.pack()
            return val

        self._stat_dl    = stat_block(stats_row, "DOWNLOADED")
        self._stat_skip  = stat_block(stats_row, "SKIPPED")
        self._stat_fail  = stat_block(stats_row, "FAILED")
        self._stat_bytes = stat_block(stats_row, "TOTAL MB")

        tk.Frame(self, bg=GREEN3, height=1).pack(fill="x", padx=18)

        # log terminal 
        log_frame = tk.Frame(self, bg=BG)
        log_frame.pack(fill="both", expand=True, padx=18, pady=(8,0))

        tk.Label(log_frame, text="[ TERMINAL OUTPUT ]", font=FONT_S,
                 fg=GREEN3, bg=BG, anchor="w").pack(fill="x")

        txt_frame = tk.Frame(log_frame, bg=BG)
        txt_frame.pack(fill="both", expand=True)

        self._log = tk.Text(txt_frame, font=("Courier New", 9),
                            bg=DIMMER, fg=GREEN2, insertbackground=GREEN,
                            relief="flat", bd=0, state="disabled",
                            wrap="none", cursor="arrow")
        self._log.pack(side="left", fill="both", expand=True)

        scroll = tk.Scrollbar(txt_frame, command=self._log.yview, bg=DIM,
                              troughcolor=DIMMER, activebackground=GREEN3)
        scroll.pack(side="right", fill="y")
        self._log["yscrollcommand"] = scroll.set

        self._log.tag_config("green",  foreground=GREEN)
        self._log.tag_config("green2", foreground=GREEN2)
        self._log.tag_config("green3", foreground=GREEN3)
        self._log.tag_config("amber",  foreground=AMBER)
        self._log.tag_config("red",    foreground=RED)
        self._log.tag_config("gray",   foreground=GRAY)

        # bottom bar 
        tk.Frame(self, bg=GREEN3, height=1).pack(fill="x", padx=18, pady=(8,0))
        bot = tk.Frame(self, bg=BG, pady=10)
        bot.pack(fill="x", padx=18)

        self._dl_btn = tk.Button(bot, text="▶  DOWNLOAD",
                                 font=("Courier New", 13, "bold"),
                                 fg=BG, bg=GREEN, relief="flat",
                                 activeforeground=BG, activebackground=GREEN2,
                                 cursor="hand2", padx=20, pady=8,
                                 command=self._toggle)
        self._dl_btn.pack(side="left")

        self._anim_label = tk.Label(bot, text="", font=("Courier New", 10),
                                    fg=GREEN3, bg=BG, width=30, anchor="w")
        self._anim_label.pack(side="left", padx=16)

        tk.Label(bot, text=f"BACKEND: {_BACKEND}", font=("Courier New", 8),
                 fg=GREEN3, bg=BG).pack(side="right")

    # UI helpers 

    def _on_bar_resize(self, event):
        self._update_bar(self._last_done if hasattr(self, "_last_done") else 0,
                         self._last_total if hasattr(self, "_last_total") else 0)

    def _update_bar(self, done, total):
        self._last_done  = done
        self._last_total = total
        w = self._bar_canvas.winfo_width() or 1
        pct = done / total if total else 0
        glow_w = max(3, int(w * pct))
        fill_w = max(0, glow_w - 4)
        self._bar_canvas.coords(self._bar_fill, 0, 0, fill_w, 18)
        self._bar_canvas.coords(self._bar_glow, fill_w, 2, glow_w, 16)
        if total:
            label = f" {pct*100:.0f}%  {done/1e6:.1f} / {total/1e6:.1f} MB"
        elif done:
            label = f" {done/1e6:.1f} MB"
        else:
            label = ""
        self._bar_canvas.itemconfig(self._bar_text, text=label)

    def _log_line(self, text, color="green2"):
        ts = datetime.now().strftime("%H:%M:%S")
        self._log.config(state="normal")
        self._log.insert("end", f"{ts}  {text}\n", color)
        self._log.see("end")
        self._log.config(state="disabled")

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self._out_var.get())
        if d:
            self._out_var.set(d)

    def _start_blink(self):
        self._blink_on = not self._blink_on
        self._status_dot.config(fg=GREEN if self._blink_on else GREEN3)
        self._blink_id = self.after(800, self._start_blink)

    # animation frames 

    _SPINNERS = [
        "▓▒░░░░░░░░░░░░░░░░░░",
        "░▓▒░░░░░░░░░░░░░░░░░",
        "░░▓▒░░░░░░░░░░░░░░░░",
        "░░░▓▒░░░░░░░░░░░░░░░",
        "░░░░▓▒░░░░░░░░░░░░░░",
        "░░░░░▓▒░░░░░░░░░░░░░",
        "░░░░░░▓▒░░░░░░░░░░░░",
        "░░░░░░░▓▒░░░░░░░░░░░",
        "░░░░░░░░▓▒░░░░░░░░░░",
        "░░░░░░░░░▓▒░░░░░░░░░",
        "░░░░░░░░░░▓▒░░░░░░░░",
        "░░░░░░░░░░░▓▒░░░░░░░",
        "░░░░░░░░░░░░▓▒░░░░░░",
        "░░░░░░░░░░░░░▓▒░░░░░",
        "░░░░░░░░░░░░░░▓▒░░░░",
        "░░░░░░░░░░░░░░░▓▒░░░",
        "░░░░░░░░░░░░░░░░▓▒░░",
        "░░░░░░░░░░░░░░░░░▓▒░",
        "░░░░░░░░░░░░░░░░░░▓▒",
        "░░░░░░░░░░░░░░░░░░░▓",
    ]

    def _tick_anim(self):
        if not self._running:
            return
        frame = self._SPINNERS[self._anim_frame % len(self._SPINNERS)]
        self._anim_label.config(text=f"  {frame}  DOWNLOADING")
        self._anim_frame += 1
        self._anim_id = self.after(55, self._tick_anim)

    def _stop_anim(self):
        if self._anim_id:
            self.after_cancel(self._anim_id)
            self._anim_id = None
        self._anim_label.config(text="")

    # download control 

    def _toggle(self):
        if self._running:
            _stop_event.set()
            self._dl_btn.config(text="▶  DOWNLOAD", fg=BG, bg=GREEN)
            self._running = False
            self._stop_anim()
            self._log_line("ABORTED BY USER", "amber")
        else:
            self._start_download()

    def _start_download(self):
        url = self._url_var.get().strip()
        if not url:
            self._log_line("ERROR: no URL entered", "red")
            return
        if not url.endswith("/"):
            url += "/"

        out = self._out_var.get().strip() or "./downloads"
        exts = [e for e, v in self._ext_vars.items() if v.get()]
        if not exts:
            self._log_line("ERROR: no file types selected", "red")
            return

        _stop_event.clear()
        self._running = True
        self._dl_btn.config(text="■  STOP", fg=BG, bg=RED)
        self._anim_frame = 0
        self._tick_anim()
        self._update_bar(0, 0)
        self._file_label.config(text="SCANNING...", fg=GREEN3)

        self._dl_thread = threading.Thread(
            target=run_download,
            args=(url, out, exts, 0.5, 120),
            daemon=True,
        )
        self._dl_thread.start()

    # queue polling 

    def _poll_queue(self):
        try:
            while True:
                m = _msg_queue.get_nowait()
                kind = m["kind"]

                if kind == "log":
                    color_map = {
                        GREEN:  "green",
                        GREEN2: "green2",
                        GREEN3: "green3",
                        AMBER:  "amber",
                        RED:    "red",
                        GRAY:   "gray",
                    }
                    tag = color_map.get(m.get("color", GREEN2), "green2")
                    self._log_line(m["text"], tag)

                elif kind == "progress":
                    self._update_bar(m["done"], m["total"])

                elif kind == "file_start":
                    self._file_label.config(text=f"▶  {m['name']}", fg=GREEN)

                elif kind == "file_done":
                    self._file_label.config(text=f"✔  {m['name']}", fg=GREEN2)

                elif kind == "stats":
                    self._stat_dl.config(text=str(m["downloaded"]))
                    self._stat_skip.config(text=str(m["skipped"]))
                    self._stat_fail.config(text=str(m["failed"]))
                    self._stat_bytes.config(text=f"{m['bytes']/1e6:.1f}")

                elif kind == "done":
                    self._running = False
                    self._stop_anim()
                    self._dl_btn.config(text="▶  DOWNLOAD", fg=BG, bg=GREEN)
                    self._file_label.config(text="COMPLETE", fg=GREEN)
                    self._update_bar(1, 1)

        except queue.Empty:
            pass
        self.after(80, self._poll_queue)

    def destroy(self):
        _stop_event.set()
        super().destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
