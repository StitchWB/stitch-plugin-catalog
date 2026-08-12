#!/usr/bin/env python3
"""Validate community plugin packages (CI gate + local pre-flight).

Usage:
    python scripts/validate_package.py [package_dir ...]

With no arguments, validates every plugins/<id>/<version>/ directory.
Requires the open-core app repo on sys.path (CI installs it; locally run
from the app repo's python/ dir or set PYTHONPATH).

Checks per package:
  * plugin.json passes autoreg.plugin.manifest.validate_manifest, kind=data,
    engine.api <= 2
  * scenario.json parses via parse_scenario_v2 with KNOWN StepKind values only
  * every selector_candidates entry is concrete (kind + non-empty value)
  * fill steps templating ${account.password} are marked sensitive
  * capabilities are within the whitelist prefixes
  * no secrets-looking literals anywhere in the package JSON
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

try:
    from autoreg.plugin.manifest import validate_manifest
    from autoreg.scenario.parse_v2 import parse_scenario_v2
    from autoreg.scenario.schema import StepKind
except ImportError as exc:  # pragma: no cover
    print(f"FATAL: cannot import autoreg parsers ({exc}).", file=sys.stderr)
    print("Run from the app repo python/ dir or set PYTHONPATH.", file=sys.stderr)
    sys.exit(2)

KNOWN_KINDS = {k.value if hasattr(k, "value") else str(k) for k in StepKind}

CAPABILITY_PREFIXES = (
    "imap.otp",
    "captcha.solve",
    "stripe.fill_checkout",
    "account.save",
    "extract",
    "branch",
    "totp.register",
)

SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret"
    r"|password|passwd|private[_-]?key)\s*[:=]\s*['\"][A-Za-z0-9_\-./+]{16,}"
)


def _fail(msg: str, errors: list[str]) -> None:
    errors.append(msg)


def validate_package(pkg_dir: Path) -> list[str]:
    errors: list[str] = []

    manifest_path = pkg_dir / "plugin.json"
    if not manifest_path.is_file():
        return [f"{pkg_dir}: missing plugin.json"]
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))

    try:
        manifest = validate_manifest(raw)
    except Exception as exc:
        return [f"{pkg_dir}: manifest invalid: {exc}"]
    if manifest.kind != "data":
        _fail(f"{pkg_dir}: kind must be 'data' (got {manifest.kind!r})", errors)
    api = manifest.engine.get("api", 0)
    if not isinstance(api, int) or api > 2:
        _fail(f"{pkg_dir}: engine.api too new ({api})", errors)

    for cap in manifest.capabilities:
        prefix = cap.split(":", 1)[0]
        if prefix not in CAPABILITY_PREFIXES:
            _fail(f"{pkg_dir}: capability {cap!r} not in whitelist", errors)

    scenario_path = pkg_dir / manifest.entry.get("scenario", "scenario.json")
    if not scenario_path.is_file():
        _fail(f"{pkg_dir}: missing {scenario_path.name}", errors)
    else:
        sraw = json.loads(scenario_path.read_text(encoding="utf-8"))
        try:
            scenario = parse_scenario_v2(sraw)
        except Exception as exc:
            _fail(f"{pkg_dir}: scenario parse error: {exc}", errors)
            scenario = None
        if scenario is not None:
            for step in scenario.steps:
                kind = step.kind.value if hasattr(step.kind, "value") else str(step.kind)
                if kind not in KNOWN_KINDS:
                    _fail(f"{pkg_dir}: unknown step kind {kind!r} (step {step.id})", errors)
                for cand in step.selector_candidates:
                    if not cand.get("kind") or not cand.get("value"):
                        _fail(
                            f"{pkg_dir}: step {step.id} has non-concrete candidate",
                            errors,
                        )
                value = step.value or ""
                if kind == "fill" and "${account.password}" in value and not step.sensitive:
                    _fail(
                        f"{pkg_dir}: step {step.id} fills password but not sensitive",
                        errors,
                    )

    for json_file in pkg_dir.glob("*.json"):
        text = json_file.read_text(encoding="utf-8")
        if SECRET_RE.search(text):
            _fail(f"{pkg_dir}: secrets-looking literal in {json_file.name}", errors)

    return errors


def main(argv: list[str]) -> int:
    targets = [Path(a) for a in argv[1:]]
    if not targets:
        targets = sorted(
            d for d in (REPO_ROOT / "plugins").glob("*/*") if d.is_dir()
        )
    if not targets:
        print("No packages to validate.")
        return 0

    total = 0
    for pkg_dir in targets:
        errs = validate_package(pkg_dir)
        if errs:
            total += len(errs)
            for e in errs:
                print(f"ERROR {e}")
        else:
            print(f"OK    {pkg_dir}")
    if total:
        print(f"{total} validation error(s).")
        return 1
    print("All packages valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
