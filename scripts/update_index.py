#!/usr/bin/env python3
"""Rebuild catalog.json from plugins/<id>/<version>/ directories.

Run in CI after merge to main (commit result with '[skip ci]').
sha256 = sha256 of sorted "relpath:sha256(file)" lines over the package dir.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _package_sha256(pkg_dir: Path) -> str:
    lines: list[str] = []
    for file in sorted(pkg_dir.rglob("*")):
        if not file.is_file():
            continue
        digest = hashlib.sha256(file.read_bytes()).hexdigest()
        lines.append(f"{file.relative_to(pkg_dir).as_posix()}:{digest}")
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def main() -> int:
    plugins: list[dict] = []
    for version_dir in sorted((REPO_ROOT / "plugins").glob("*/*")):
        if not version_dir.is_dir():
            continue
        manifest_path = version_dir / "plugin.json"
        if not manifest_path.is_file():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        services = [manifest.get("service", "")]
        services += [s for s in manifest.get("services", []) if s not in services]
        plugins.append(
            {
                "id": manifest.get("id", version_dir.parent.name),
                "name": manifest.get("name", manifest.get("id", "")),
                "version": manifest.get("version", "0.0.0"),
                "author": os.environ.get("CATALOG_AUTHOR", "community"),
                "description": manifest.get("name", ""),
                "path": version_dir.relative_to(REPO_ROOT).as_posix(),
                "services": [s for s in services if s],
                "sha256": _package_sha256(version_dir),
            }
        )

    catalog = {
        "schema": "stitch.catalog/v1",
        "updated_at": datetime.now(UTC).isoformat(),
        "plugins": plugins,
    }
    out = REPO_ROOT / "catalog.json"
    out.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"catalog.json rebuilt: {len(plugins)} plugin(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
