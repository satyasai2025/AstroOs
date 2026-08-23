#!/usr/bin/env python3
"""
AstroOS — Frozen Calculation Module Guard

Every file listed in FROZEN_MODULES.md has been deep-audited this
session against classical Vedic astrology rules and, where possible,
numerically cross-checked against PyJHora, with zero known remaining
calculation errors. This script re-hashes each listed file and fails
if any hash has drifted from the recorded value, meaning someone
changed a frozen calculation module without going through the unlock
process (see FROZEN_MODULES.md's "How to modify a frozen file" section).

Usage:
    python scripts/verify_frozen_modules.py            # verify (CI mode)
    python scripts/verify_frozen_modules.py --update    # regenerate hashes (admin-only, local use)
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "FROZEN_MODULES.md"
_ENTRY_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([a-f0-9]{64})`\s*\|")
_PENDING_ENTRY_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`PENDING`\s*\|")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_manifest() -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines():
        m = _ENTRY_RE.match(line)
        if m:
            entries[m.group(1)] = m.group(2)
    return entries


def verify() -> int:
    entries = _parse_manifest()
    if not entries:
        print("FROZEN_MODULES.md has no parseable entries — nothing to verify.")
        return 0

    mismatches: list[str] = []
    missing: list[str] = []

    for rel_path, expected_hash in entries.items():
        path = REPO_ROOT / rel_path
        if not path.exists():
            missing.append(rel_path)
            continue
        actual_hash = _sha256(path)
        if actual_hash != expected_hash:
            mismatches.append(rel_path)

    if missing:
        print("FROZEN FILE MISSING (deleted or moved without unlock):")
        for f in missing:
            print(f"  - {f}")

    if mismatches:
        print("FROZEN FILE CHANGED WITHOUT UNLOCK:")
        for f in mismatches:
            print(f"  - {f}")
        print()
        print("These files were verified error-free by deep audit. If this")
        print("change is intentional and admin-approved, regenerate the")
        print("manifest with: python scripts/verify_frozen_modules.py --update")
        print("and commit the updated FROZEN_MODULES.md alongside the change.")

    if missing or mismatches:
        return 1

    print(f"OK — all {len(entries)} frozen modules match their recorded hashes.")
    return 0


def update() -> int:
    lines = MANIFEST_PATH.read_text(encoding="utf-8").splitlines()
    changed = 0
    missing = []
    new_lines = []
    for line in lines:
        m = _ENTRY_RE.match(line) or _PENDING_ENTRY_RE.match(line)
        if m:
            rel_path = m.group(1)
            old_hash = m.group(2) if m.re is _ENTRY_RE else "PENDING"
            path = REPO_ROOT / rel_path
            if not path.exists():
                missing.append(rel_path)
            else:
                new_hash = _sha256(path)
                if new_hash != old_hash:
                    changed += 1
                    line = line.replace(f"`{old_hash}`", f"`{new_hash}`", 1)
        new_lines.append(line)

    MANIFEST_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    if missing:
        print("WARNING — listed files not found on disk (left unchanged):")
        for f in missing:
            print(f"  - {f}")
    print(f"Updated {changed} hash(es) in FROZEN_MODULES.md.")
    return 0


if __name__ == "__main__":
    if "--update" in sys.argv:
        sys.exit(update())
    sys.exit(verify())
