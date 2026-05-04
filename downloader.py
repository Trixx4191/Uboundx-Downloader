#!/usr/bin/env python3
"""
UnboundX Directory Downloader
"""

import argparse
import os
import sys
import time
import urllib.parse
from bs4 import BeautifulSoup

try:
    import config as cfg
except ImportError:
    cfg = None


def resolve_cfg(attr, fallback):
    return getattr(cfg, attr, fallback) if cfg else fallback

# Session setup
try:
    from curl_cffi import requests as curl_requests
    _SESSION = curl_requests.Session(impersonate="chrome120")
    _BACKEND = "curl_cffi (chrome120 TLS)"
except ImportError:
    import requests as _requests
    _SESSION = _requests.Session()
    _BACKEND = "requests"

_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

_SESSION.headers.update(resolve_cfg('HEADERS', _DEFAULT_HEADERS))

DEFAULT_URL = resolve_cfg('BASE_URL', 'https://example.com/files/')
DEFAULT_OUTPUT_DIR = resolve_cfg('OUTPUT_DIR', './downloads')
DEFAULT_EXTENSIONS = resolve_cfg('EXTENSIONS', ['mp4', 'mkv', 'pdf', 'pptx', 'ppt'])
DEFAULT_DELAY = resolve_cfg('DELAY_SEC', 1.0)
DEFAULT_TIMEOUT = resolve_cfg('TIMEOUT_SEC', 120)
DEFAULT_CHUNK_SIZE = resolve_cfg('CHUNK_SIZE', 256 * 1024)

_base_url = ""


def url_to_local(file_url, base_url, output_dir):
    relative = urllib.parse.unquote(file_url[len(base_url):])
    return os.path.join(output_dir, relative.lstrip("/"))


def is_target_file(href, extensions):
    lower = href.lower().split("?")[0]
    return any(lower.endswith("." + ext) for ext in extensions)


def is_subdirectory(href):
    return (
        href.endswith("/")
        and not href.startswith("?")
        and not href.startswith("/")
        and not href.startswith("http")
        and href != "../"
    )


def scrape(url, output_dir, extensions, delay, timeout):
    print(f"\n  📂  {url}")

    response = None
    for attempt in range(1, 4):
        try:
            response = _SESSION.get(url, timeout=30)
            response.raise_for_status()
            break
        except Exception as exc:
            status = getattr(exc, 'response', None)
            if status is not None:
                status = getattr(status, 'status_code', None)
            if status == 403:
                print(f"  [!] 403 Forbidden - WAF/Cloudflare: {url}")
                print("     Increase --delay or use cloudscraper/Playwright.")
                return
            wait = attempt * 3
            print(f"  [!] Attempt {attempt}/3 failed: {exc}")
            if attempt < 3:
                print(f"      Retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"  [!] Giving up on directory: {url}")
                return

    soup = BeautifulSoup(response.text, "html.parser")
    links = [a.get('href') for a in soup.find_all('a') if a.get('href')]

    text_lower = response.text.lower()
    if len(links) == 0 or 'index of' not in text_lower:
        print(f"  [!] No dir listing/blocked (SPA/WAF): {url}")
        print("     Need Apache/nginx 'Index of /'")
        return

    files = 0
    for href in links:
        href = href.strip()
        if is_target_file(href, extensions):
            abs_url = urllib.parse.urljoin(url, href)
            local_path = url_to_local(abs_url, _base_url, output_dir)
            download_file(abs_url, local_path, timeout)
            files += 1
            time.sleep(delay)
        elif is_subdirectory(href):
            scrape(urllib.parse.urljoin(url, href), output_dir, extensions, delay, timeout)
    if files == 0:
        print(f"  [i] No matching files found in {url}")


def download_file(url, local_path, timeout):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    filename = os.path.basename(local_path)

    if os.path.exists(local_path):
        print(f"  [S] Skipping existing file: {filename}")
        return

    print(f"  [D] Downloading {filename}")
    for attempt in range(1, 4):
        try:
            r = _SESSION.get(url, stream=True, timeout=timeout)
            r.raise_for_status()
            with open(local_path, 'wb') as fh:
                for chunk in r.iter_content(chunk_size=DEFAULT_CHUNK_SIZE):
                    if chunk:
                        fh.write(chunk)
            print(f"  [✓] Saved {filename}")
            return
        except Exception as exc:
            print(f"  [!] Download attempt {attempt}/3 failed for {filename}: {exc}")
            if os.path.exists(local_path):
                try:
                    os.remove(local_path)
                except OSError:
                    pass
            if attempt < 3:
                time.sleep(attempt * 3)
            else:
                print(f"  [X] Failed to download {filename}")


def build_parser():
    parser = argparse.ArgumentParser(description='Mirror Apache/nginx directory listings.')
    parser.add_argument('--url', '-u', dest='url', default=resolve_cfg('BASE_URL', DEFAULT_URL), help='Base directory URL to crawl')
    parser.add_argument('--out', '-o', dest='output_dir', default=resolve_cfg('OUTPUT_DIR', DEFAULT_OUTPUT_DIR), help='Local output directory')
    parser.add_argument('--ext', nargs='+', dest='extensions', default=resolve_cfg('EXTENSIONS', DEFAULT_EXTENSIONS), help='File extensions to download')
    parser.add_argument('--delay', type=float, dest='delay', default=resolve_cfg('DELAY_SEC', DEFAULT_DELAY), help='Seconds between requests')
    parser.add_argument('--timeout', type=int, dest='timeout', default=resolve_cfg('TIMEOUT_SEC', DEFAULT_TIMEOUT), help='Download timeout in seconds')
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    url = args.url.strip()
    if not url:
        parser.error('Missing URL. Provide --url or set BASE_URL in config.py')
    if not url.endswith('/'):
        url += '/'

    output_dir = args.output_dir or DEFAULT_OUTPUT_DIR
    extensions = [ext.lower().lstrip('.') for ext in args.extensions]

    print('=' * 60)
    print(f'URL        : {url}')
    print(f'OUTPUT     : {output_dir}')
    print(f'EXTENSIONS : {extensions}')
    print(f'DELAY      : {args.delay}s')
    print(f'TIMEOUT    : {args.timeout}s')
    print(f'BACKEND    : {_BACKEND}')
    print('=' * 60)

    global _base_url
    _base_url = url
    scrape(url, output_dir, extensions, args.delay, args.timeout)


if __name__ == '__main__':
    main()

