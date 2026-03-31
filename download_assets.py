#!/usr/bin/env python3
"""
Download all images, videos, and documents from on.energy payload JSON files.
Includes Storyblok CDN assets.
"""

import os
import re
import time
import glob
import urllib.parse
from pathlib import Path

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SITE_DIR = Path(r"C:\Users\admin\Desktop\ONENERGY\site")
ASSETS_DIR = Path(r"C:\Users\admin\Desktop\ONENERGY\assets")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

TARGET_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".avif", ".bmp", ".ico",
    ".mp4", ".webm", ".mov", ".avi",
    ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
    ".woff", ".woff2", ".ttf", ".otf",
}

session = requests.Session()
session.headers.update(HEADERS)

stats = {"downloaded": 0, "skipped": 0, "errors": 0}


def get_save_path(url):
    """Determine local save path for a URL."""
    parsed = urllib.parse.urlparse(url)

    # Storyblok CDN
    if "storyblok.com" in parsed.netloc:
        # Keep the path structure but save under assets/storyblok/
        path = parsed.path.lstrip("/")
        return ASSETS_DIR / "storyblok" / path

    # on.energy itself
    if "on.energy" in parsed.netloc:
        path = parsed.path.lstrip("/")
        return SITE_DIR / path

    # Other CDNs
    path = parsed.netloc.replace(".", "_") + parsed.path
    return ASSETS_DIR / "other" / path.lstrip("/")


def download_url(url):
    """Download a URL and save to appropriate path."""
    save_path = get_save_path(url)

    if save_path.exists() and save_path.stat().st_size > 0:
        stats["skipped"] += 1
        return True

    for attempt in range(3):
        try:
            resp = session.get(url, timeout=60, stream=True)
            if resp.status_code == 404:
                print(f"  [404] {url}")
                stats["errors"] += 1
                return False
            if resp.status_code != 200:
                print(f"  [HTTP {resp.status_code}] {url}")
                if attempt < 2:
                    time.sleep(2)
                    continue
                stats["errors"] += 1
                return False

            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    f.write(chunk)

            size = save_path.stat().st_size
            print(f"  [OK] {url} -> {save_path.name} ({size:,} bytes)")
            stats["downloaded"] += 1
            return True

        except Exception as e:
            if attempt < 2:
                print(f"  [Retry {attempt+1}] {url}: {e}")
                time.sleep(2)
            else:
                print(f"  [Error] {url}: {e}")
                stats["errors"] += 1
                return False
    return False


def main():
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    # Collect all URLs from JSON files
    all_urls = set()
    json_files = list(SITE_DIR.rglob("*.json"))
    print(f"Scanning {len(json_files)} JSON payload files...")

    for json_file in json_files:
        try:
            text = json_file.read_text(encoding="utf-8", errors="ignore")
            # Find all URLs
            urls = re.findall(r'"(https?://[^"\s]{10,})"', text)
            for u in urls:
                # Clean up escaped unicode
                u = u.replace("\\u002F", "/").replace("\\/", "/")
                # Check extension
                ext = Path(urllib.parse.urlparse(u).path).suffix.lower()
                if ext in TARGET_EXTENSIONS or "storyblok.com" in u:
                    all_urls.add(u)
        except Exception as e:
            print(f"  Error reading {json_file}: {e}")

    # Also scan HTML files for any missed assets
    html_files = list(SITE_DIR.rglob("*.html"))
    print(f"Scanning {len(html_files)} HTML files...")
    for html_file in html_files:
        try:
            text = html_file.read_text(encoding="utf-8", errors="ignore")
            urls = re.findall(r'"(https?://[^"\s]{10,})"', text)
            for u in urls:
                ext = Path(urllib.parse.urlparse(u).path).suffix.lower()
                if ext in TARGET_EXTENSIONS or "storyblok.com" in u:
                    all_urls.add(u)
        except Exception:
            pass

    # Filter to media/document URLs only
    media_urls = set()
    for u in all_urls:
        ext = Path(urllib.parse.urlparse(u).path).suffix.lower()
        if ext in TARGET_EXTENSIONS or "storyblok.com/f/" in u:
            media_urls.add(u)

    print(f"\nFound {len(media_urls)} asset URLs to download")
    print("=" * 60)

    for i, url in enumerate(sorted(media_urls), 1):
        print(f"\n[{i}/{len(media_urls)}] {url}")
        download_url(url)
        time.sleep(0.3)

    print("\n" + "=" * 60)
    print("DOWNLOAD COMPLETE")
    print(f"  Downloaded: {stats['downloaded']}")
    print(f"  Skipped:    {stats['skipped']}")
    print(f"  Errors:     {stats['errors']}")

    # Print summary of what's saved
    print(f"\nFiles saved:")
    total_size = 0
    for root, dirs, files in os.walk(ASSETS_DIR):
        for f in files:
            fp = Path(root) / f
            total_size += fp.stat().st_size
    print(f"  Assets dir: {ASSETS_DIR}")
    print(f"  Total size: {total_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
