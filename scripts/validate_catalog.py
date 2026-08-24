#!/usr/bin/env python3
"""Offline catalog validator for CI.

Replicates the ``catalog-lint`` rules from ``stitch_plugin_tools.catalog_lint``
so this repo's CI can validate ``catalog.json`` without depending on the
private main repo's tooling export (the public Stitch-Manager export does not
yet ship the ``catalog-lint`` subcommand).

Rules (mirror catalog_lint.py exactly — do not diverge):
  1. JSON must parse and be a dict with a ``plugins`` list.
  2. Each entry must be a dict with ``id`` (str) and ``version`` (str).
  3. Version must be semver (``MAJOR.MINOR.PATCH`` with optional pre-release).
  4. If ``source`` is present:
     - Must be a dict with ``type`` ∈ {``"git"``, ``"release"``}.
     - git: ``url`` required (str).
     - release: ``url`` required (str) + ``sha256`` required (hex64).
     - Unknown ``type`` → error.
  5. Duplicate ``id`` + ``version`` pairs → error.
  6. Legacy entries (no ``source``) are accepted (backward compat).

Exit 0 on success, 1 on any error.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$")


def _is_hex64(s: str) -> bool:
    return len(s) == 64 and all(c in "0123456789abcdef" for c in s.lower())


def lint_entry(entry: Any) -> list[str]:
    errors: list[str] = []

    if not isinstance(entry, dict):
        return [f"entry is not an object (got {type(entry).__name__})"]

    eid = entry.get("id")
    if not eid or not isinstance(eid, str):
        errors.append("missing or non-string 'id'")
    version = entry.get("version")
    if not version or not isinstance(version, str):
        errors.append("missing or non-string 'version'")
    elif not _SEMVER_RE.match(version):
        errors.append(f"version {version!r} is not semver (MAJOR.MINOR.PATCH)")

    source = entry.get("source")
    if source is not None:
        if not isinstance(source, dict):
            errors.append("'source' must be an object")
        else:
            stype = source.get("type")
            if stype == "git":
                url = source.get("url")
                if not url or not isinstance(url, str):
                    errors.append("git source requires 'url'")
            elif stype == "release":
                url = source.get("url")
                if not url or not isinstance(url, str):
                    errors.append("release source requires 'url'")
                sha256 = source.get("sha256")
                if not sha256 or not isinstance(sha256, str):
                    errors.append("release source requires 'sha256'")
                elif not _is_hex64(sha256):
                    errors.append("release source 'sha256' must be hex64")
            else:
                errors.append(f"unknown source type: {stype!r}")

    return errors


def lint_catalog(catalog_path: str | Path) -> int:
    path = Path(catalog_path)
    if not path.is_file():
        print(f"error: catalog file not found: {path}", file=sys.stderr)
        return 1

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"error: JSON parse failed: {exc}", file=sys.stderr)
        return 1

    if not isinstance(raw, dict):
        print("error: catalog root must be an object", file=sys.stderr)
        return 1

    plugins = raw.get("plugins")
    if not isinstance(plugins, list):
        print("error: catalog must have a 'plugins' array", file=sys.stderr)
        return 1

    seen: dict[str, int] = {}
    total_errors = 0
    entries_ok = 0

    for i, entry in enumerate(plugins):
        label = f"entry[{i}]"
        if isinstance(entry, dict) and entry.get("id") and entry.get("version"):
            label = f"entry[{i}] {entry['id']}@{entry['version']}"

        errs = lint_entry(entry)
        if errs:
            for e in errs:
                print(f"  FAIL  {label}: {e}")
            total_errors += len(errs)
        else:
            print(f"  OK    {label}")
            entries_ok += 1

        if isinstance(entry, dict):
            eid = entry.get("id")
            ver = entry.get("version")
            if isinstance(eid, str) and isinstance(ver, str):
                key = f"{eid}@{ver}"
                if key in seen:
                    print(
                        f"  FAIL  {label}: duplicate id@version "
                        f"(also at entry[{seen[key]}])"
                    )
                    total_errors += 1
                else:
                    seen[key] = i

    print(f"\n{entries_ok} ok, {total_errors} error(s) in {len(plugins)} entries")
    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <catalog.json>", file=sys.stderr)
        sys.exit(2)
    sys.exit(lint_catalog(sys.argv[1]))
