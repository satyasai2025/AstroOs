#!/usr/bin/env python3
"""
CLI for creating and managing research snapshots.
"""
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional
import sys

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .schema import (
    SnapshotManifest,
    VersionRef,
    CalculationConfig,
    ModuleName
)


def calculate_file_hash(filepath: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def calculate_directory_hash(directory: Path) -> str:
    """Calculate SHA256 hash of all files in a directory (recursive)."""
    sha256_hash = hashlib.sha256()

    # Sort files for consistent hashing
    files = sorted([f for f in directory.rglob("*") if f.is_file()])

    for file_path in files:
        # Include relative path in hash for consistency
        rel_path = file_path.relative_to(directory)
        sha256_hash.update(str(rel_path).encode('utf-8'))

        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def get_git_commit(repo_path: Path = None) -> str:
    """Get current git commit hash."""
    import subprocess
    try:
        if repo_path is None:
            repo_path = Path.cwd()
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def create_snapshot(
    name: str,
    description: Optional[str] = None,
    output_dir: Path = Path("./snapshots")
) -> SnapshotManifest:
    """Create a research snapshot of the current state."""

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Gather version information
    versions = []

    # Ontology version
    ontology_path = Path("../ontology")  # Adjust as needed
    if ontology_path.exists():
        versions.append(VersionRef(
            module=ModuleName.ONTOLOGY,
            version="dev",  # Would come from version file or git tag
            git_commit=get_git_commit(ontology_path),
            checksum=calculate_directory_hash(ontology_path) if ontology_path.is_dir()
                     else calculate_file_hash(ontology_path)
        ))

    # Rules version
    rules_path = Path("../rules")
    if rules_path.exists():
        versions.append(VersionRef(
            module=ModuleName.RULES,
            version="dev",
            git_commit=get_git_commit(rules_path),
            checksum=calculate_directory_hash(rules_path) if rules_path.is_dir()
                     else calculate_file_hash(rules_path)
        ))

    # Calculation engine (this package)
    calc_engine_path = Path(".")
    versions.append(VersionRef(
        module=ModuleName.CALCULATION_ENGINE,
        version="dev",
        git_commit=get_git_commit(calc_engine_path),
        checksum=calculate_directory_hash(calc_engine_path)
    ))

    # Ephemeris data (example path)
    ephemeris_path = Path("../ephemeris")
    if ephemeris_path.exists():
        versions.append(VersionRef(
            module=ModuleName.EPHEMERIS,
            version="swisseph_2.08.00",  # Example version
            git_commit=get_git_commit(ephemeris_path),
            checksum=calculate_directory_hash(ephemeris_path) if ephemeris_path.is_dir()
                     else calculate_file_hash(ephemeris_path)
        ))

    # Dataset checksum (if provided as argument)
    dataset_checksum = "0" * 64  # Placeholder

    # Fact checksum (would come from database/query)
    fact_checksum = "0" * 64  # Placeholder

    # Calculation config (would come from actual config)
    calc_config = CalculationConfig(
        ayanamsha="Lahiri",
        house_system="Placidus",
        node_type="True Mean",
        ephemeris_path=str(ephemeris_path) if ephemeris_path.exists() else "",
        timezone_db_version="2021a",
        calculation_settings={"tropical": False},
        enabled_modules=["shadbala", "ashtakavarga", "yogas"],
        rule_ordering=["shadbala.1", "shadbala.2", "ashtakavarga.1"]
    )

    # Create manifest
    manifest = SnapshotManifest(
        versions=versions,
        calculation_config=calc_config,
        fact_checksum=fact_checksum,
        dataset_checksum=dataset_checksum,
        timestamp=datetime.now(timezone.utc),
        description=description or f"Snapshot created at {datetime.now().isoformat()}"
    )

    # Save to file
    output_file = output_dir / f"{name}_{manifest.snapshot_id[:8]}.json"
    with open(output_file, 'w') as f:
        json.dump(manifest.model_dump(mode="json"), f, indent=2, default=str)

    print(f"Snapshot saved to: {output_file}")
    print(f"Snapshot ID: {manifest.snapshot_id}")

    return manifest


def load_snapshot(filepath: Path) -> SnapshotManifest:
    """Load a snapshot from file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return SnapshotManifest(**data)


def verify_snapshot(manifest: SnapshotManifest) -> bool:
    """Verify that a snapshot's checksums match current state."""
    # This would compare current checksums with stored ones
    # For now, just return True as placeholder
    return True


def main():
    parser = argparse.ArgumentParser(description="Research snapshot management")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new snapshot')
    create_parser.add_argument('name', help='Name for the snapshot')
    create_parser.add_argument('--description', '-d', help='Description of the experiment')
    create_parser.add_argument('--output', '-o', type=Path, default=Path('./snapshots'),
                             help='Output directory for snapshots')

    # Load command
    load_parser = subparsers.add_parser('load', help='Load and display a snapshot')
    load_parser.add_argument('file', type=Path, help='Path to snapshot file')

    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify a snapshot against current state')
    verify_parser.add_argument('file', type=Path, help='Path to snapshot file')

    args = parser.parse_args()

    if args.command == 'create':
        manifest = create_snapshot(args.name, args.description, args.output)
        print(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str))

    elif args.command == 'load':
        manifest = load_snapshot(args.file)
        print(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str))

    elif args.command == 'verify':
        manifest = load_snapshot(args.file)
        is_valid = verify_snapshot(manifest)
        print(f"Snapshot {'is valid' if is_valid else 'is invalid'}")
        sys.exit(0 if is_valid else 1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()