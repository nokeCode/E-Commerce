#!/usr/bin/env python3
"""Download GeoLite2 databases from MaxMind into the local geoip folder."""

from __future__ import annotations

import argparse
import os
import tarfile
import tempfile
from pathlib import Path

import requests

MAXMIND_DOWNLOAD_URL = "https://download.maxmind.com/app/geoip_download"


def parse_args() -> argparse.Namespace:
    project_root = Path(__file__).resolve().parents[1]
    default_output_dir = project_root / "geoip"

    parser = argparse.ArgumentParser(
        description="Download GeoLite2 .mmdb files from MaxMind."
    )
    parser.add_argument(
        "--license-key",
        default=os.getenv("MAXMIND_LICENSE_KEY"),
        help="MaxMind license key (or set MAXMIND_LICENSE_KEY).",
    )
    parser.add_argument(
        "--editions",
        nargs="+",
        default=["GeoLite2-City", "GeoLite2-ASN"],
        help="MaxMind edition IDs to download.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(default_output_dir),
        help=f"Destination folder (default: {default_output_dir}).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="HTTP timeout in seconds.",
    )
    return parser.parse_args()


def download_archive(edition: str, license_key: str, timeout: int) -> bytes:
    params = {
        "edition_id": edition,
        "license_key": license_key,
        "suffix": "tar.gz",
    }
    response = requests.get(MAXMIND_DOWNLOAD_URL, params=params, timeout=timeout)
    response.raise_for_status()
    return response.content


def extract_mmdb(archive_bytes: bytes, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as temp_file:
        temp_file.write(archive_bytes)
        temp_archive_path = Path(temp_file.name)

    try:
        with tarfile.open(temp_archive_path, "r:gz") as archive:
            mmdb_members = [
                member for member in archive.getmembers() if member.name.endswith(".mmdb")
            ]
            if not mmdb_members:
                raise RuntimeError("No .mmdb file found in the downloaded archive.")

            with archive.extractfile(mmdb_members[0]) as source:
                if source is None:
                    raise RuntimeError("Unable to read .mmdb content from archive.")
                output_path.write_bytes(source.read())
    finally:
        temp_archive_path.unlink(missing_ok=True)


def main() -> int:
    args = parse_args()

    if not args.license_key:
        raise SystemExit(
            "Missing MaxMind license key. Use --license-key or MAXMIND_LICENSE_KEY."
        )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for edition in args.editions:
        print(f"Downloading {edition}...")
        archive_bytes = download_archive(edition, args.license_key, args.timeout)
        destination = output_dir / f"{edition}.mmdb"
        extract_mmdb(archive_bytes, destination)
        print(f"Saved: {destination}")

    print("GeoIP database download completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
