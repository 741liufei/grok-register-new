"""Install a pinned Camoufox release without querying the GitHub REST API."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import BinaryIO

from camoufox.pkgman import (
    AvailableVersion,
    CamoufoxFetcher,
    RepoConfig,
    Version,
    camoufox_path,
    launch_path,
)


class VerifiedCamoufoxFetcher(CamoufoxFetcher):
    """Use Camoufox's installer, but reject incomplete or altered downloads."""

    def __init__(self, *args, expected_sha256: str, expected_size: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.expected_sha256 = expected_sha256.lower()
        self.expected_size = expected_size

    def download_file(self, file: BinaryIO, url: str) -> BinaryIO:
        downloaded = super().download_file(file, url)
        downloaded.flush()
        downloaded.seek(0)

        digest = hashlib.sha256()
        size = 0
        while chunk := downloaded.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)

        actual_sha256 = digest.hexdigest()
        if size != self.expected_size:
            raise RuntimeError(
                f"Camoufox package size mismatch: expected {self.expected_size}, got {size}"
            )
        if actual_sha256 != self.expected_sha256:
            raise RuntimeError(
                "Camoufox package SHA-256 mismatch: "
                f"expected {self.expected_sha256}, got {actual_sha256}"
            )

        print(f"Verified Camoufox package: {size} bytes, sha256={actual_sha256}", flush=True)
        downloaded.seek(0)
        return downloaded


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--build", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--size", required=True, type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if len(args.sha256) != 64 or any(c not in "0123456789abcdefABCDEF" for c in args.sha256):
        raise ValueError("--sha256 must be a 64-character hexadecimal digest")

    selected = AvailableVersion(
        version=Version(version=args.version, build=args.build),
        url=args.url,
        is_prerelease=False,
        asset_size=args.size,
        sha256=args.sha256.lower(),
    )
    fetcher = VerifiedCamoufoxFetcher(
        repo_config=RepoConfig.get_default(),
        selected_version=selected,
        expected_sha256=args.sha256,
        expected_size=args.size,
    )
    fetcher.install(replace=True)

    browser_dir = camoufox_path(download_if_missing=False)
    executable = Path(launch_path(browser_dir))
    if not executable.is_file():
        raise RuntimeError(f"Camoufox executable is missing: {executable}")
    print(f"Camoufox installation ready: {executable}", flush=True)


if __name__ == "__main__":
    main()
