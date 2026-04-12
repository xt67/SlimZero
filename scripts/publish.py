"""
SlimZero Publishing Script

Publishes to PyPI or TestPyPI.

Usage:
    # TestPyPI (recommended before production release)
    python scripts/publish.py --testpypi

    # Production PyPI
    python scripts/publish.py --pypi

    # Both
    python scripts/publish.py --testpypi --pypi
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

PYPI_TOKEN = os.environ.get("PYPI_TOKEN", "")
TESTPYPI_TOKEN = os.environ.get("TESTPYPI_TOKEN", "")


def build_package() -> str:
    """Build the package and return the dist directory."""
    dist_dir = Path("dist")
    if dist_dir.exists():
        for f in dist_dir.glob("*"):
            f.unlink()

    subprocess.run([sys.executable, "-m", "build"], check=True)
    return "dist"


def publish_testpypi() -> None:
    """Publish to TestPyPI."""
    if not TESTPYPI_TOKEN:
        print("Error: TESTPYPI_TOKEN environment variable not set")
        sys.exit(1)

    dist_dir = build_package()

    print("Uploading to TestPyPI...")
    subprocess.run([
        sys.executable, "-m", "twine", "upload",
        "--repository", "testpypi",
        "--username", "__token__",
        "--password", TESTPYPI_TOKEN,
        f"{dist_dir}/*",
    ], check=True)
    print("Successfully published to TestPyPI!")
    print("Install with: pip install --index-url https://test.pypi.org/simple/ slimzero")


def publish_pypi() -> None:
    """Publish to PyPI."""
    if not PYPI_TOKEN:
        print("Error: PYPI_TOKEN environment variable not set")
        sys.exit(1)

    dist_dir = build_package()

    print("Uploading to PyPI...")
    subprocess.run([
        sys.executable, "-m", "twine", "upload",
        "--skip-existing",
        "--username", "__token__",
        "--password", PYPI_TOKEN,
        f"{dist_dir}/*",
    ], check=True)
    print("Successfully published to PyPI!")
    print("Update with: pip install --upgrade slimzero")


def verify_package() -> None:
    """Verify the built package contents."""
    from slimzero import __version__
    from slimzero.core import SlimZero
    from slimzero.schemas import SlimZeroResult

    print(f"Package version: {__version__}")
    print("All core imports successful!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publish SlimZero to PyPI")
    parser.add_argument("--testpypi", action="store_true", help="Publish to TestPyPI")
    parser.add_argument("--pypi", action="store_true", help="Publish to PyPI")
    parser.add_argument("--verify", action="store_true", help="Verify package contents")
    args = parser.parse_args()

    if args.verify:
        verify_package()
    elif args.testpypi:
        publish_testpypi()
    elif args.pypi:
        publish_pypi()
    else:
        parser.print_help()
