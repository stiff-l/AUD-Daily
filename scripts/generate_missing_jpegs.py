"""
Backfill script — generates JPEG files for any HTML files that are missing a JPEG.

Scans both forex and commodities HTML directories and converts any HTML
file that does not have a corresponding JPEG in the sibling JPEG/ directory.

Usage:
    python3 scripts/generate_missing_jpegs.py
    python3 scripts/generate_missing_jpegs.py --dry-run
"""

import os
import sys
import argparse

# Allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.html_utils import html_to_jpeg

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCAN_DIRS = [
    {
        "html_dir": os.path.join(BASE_DIR, "data", "forex_data", "HTML"),
        "jpeg_dir": os.path.join(BASE_DIR, "data", "forex_data", "JPEG"),
        "label": "Forex",
    },
    {
        "html_dir": os.path.join(BASE_DIR, "data", "commodities_data", "HTML"),
        "jpeg_dir": os.path.join(BASE_DIR, "data", "commodities_data", "JPEG"),
        "label": "Commodities",
    },
]


def find_missing(html_dir: str, jpeg_dir: str):
    """Return list of (html_path, jpeg_path) pairs where JPEG is absent."""
    if not os.path.isdir(html_dir):
        return []
    missing = []
    for filename in sorted(os.listdir(html_dir)):
        if not filename.endswith(".html"):
            continue
        jpeg_name = filename.replace(".html", ".jpg")
        jpeg_path = os.path.join(jpeg_dir, jpeg_name)
        if not os.path.exists(jpeg_path):
            missing.append((os.path.join(html_dir, filename), jpeg_path))
    return missing


def main():
    parser = argparse.ArgumentParser(description="Generate missing JPEG files from existing HTML files.")
    parser.add_argument("--dry-run", action="store_true", help="List missing JPEGs without generating them.")
    args = parser.parse_args()

    total_missing = 0
    total_generated = 0
    total_failed = 0

    for entry in SCAN_DIRS:
        label = entry["label"]
        html_dir = entry["html_dir"]
        jpeg_dir = entry["jpeg_dir"]

        missing = find_missing(html_dir, jpeg_dir)
        total_missing += len(missing)

        print(f"\n[{label}] {len(missing)} missing JPEG(s)")

        if not missing:
            continue

        os.makedirs(jpeg_dir, exist_ok=True)

        for html_path, jpeg_path in missing:
            basename = os.path.basename(html_path)
            if args.dry_run:
                print(f"  MISSING: {basename}")
                continue

            print(f"  Generating: {basename}")
            result = html_to_jpeg(html_path, jpeg_path)
            if result:
                total_generated += 1
                print(f"  ✓ Done: {os.path.basename(jpeg_path)}")
            else:
                total_failed += 1
                print(f"  ✗ Failed: {basename}")

    print(f"\n{'--- DRY RUN ---' if args.dry_run else '--- SUMMARY ---'}")
    print(f"  Missing : {total_missing}")
    if not args.dry_run:
        print(f"  Generated: {total_generated}")
        print(f"  Failed   : {total_failed}")


if __name__ == "__main__":
    main()
