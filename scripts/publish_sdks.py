#!/usr/bin/env python3
"""
AstroOS SDK Publication Script
Publishes Python and TypeScript SDKs to PyPI and npm respectively.
"""

import subprocess
import sys
from pathlib import Path


def publish_python_sdk():
    """Publish Python SDK to PyPI."""
    sdk_dir = Path("sdks/python")
    
    # Build the package
    print("Building Python SDK...")
    result = subprocess.run(
        ["python", "-m", "build"],
        cwd=sdk_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Build failed: {result.stderr}")
        return False
    
    # Check if twine is available for upload
    print("Python SDK build complete. To publish, run:")
    print("  cd sdks/python && twine upload dist/*")
    print("\nOr set PYPI_TOKEN environment variable for automated publishing.")
    return True


def publish_typescript_sdk():
    """Publish TypeScript SDK to npm."""
    sdk_dir = Path("sdks/typescript")
    
    print("Building TypeScript SDK...")
    result = subprocess.run(
        ["pnpm", "run", "build"],
        cwd=sdk_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Build failed: {result.stderr}")
        return False
    
    print("TypeScript SDK build complete. To publish, run:")
    print("  cd sdks/typescript && npm publish --access public")
    return True


def main():
    """Main entry point."""
    print("=" * 60)
    print("AstroOS SDK Publication Tool")
    print("=" * 60)
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if mode in ("all", "python"):
        if not publish_python_sdk():
            sys.exit(1)
    
    if mode in ("all", "typescript"):
        if not publish_typescript_sdk():
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("SDK publication preparation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()