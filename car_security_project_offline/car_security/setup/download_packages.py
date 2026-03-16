"""
setup/download_packages.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Run this ONCE on a machine WITH internet to download all pip
packages as .whl files into the  packages/  folder.

Then copy the entire project (including packages/) to the RPi
and install fully offline using:
    pip install --no-index --find-links=packages/ -r requirements.txt

Usage (internet machine):
    python setup/download_packages.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
import subprocess

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG_DIR      = os.path.join(BASE_DIR, "packages")
REQUIREMENTS = os.path.join(BASE_DIR, "requirements.txt")

# ARM64 platform tag for RPi4 (64-bit OS) — change to armv7l for 32-bit
PLATFORM = "manylinux2014_aarch64"
PYTHON   = "cp311"  # Python 3.11 — match your RPi Python version

def main():
    os.makedirs(PKG_DIR, exist_ok=True)

    print("=" * 58)
    print("  Downloading pip packages for offline RPi4 install")
    print("=" * 58)
    print(f"\n  Target:   {PKG_DIR}")
    print(f"  Platform: {PLATFORM} (RPi4 64-bit)")
    print(f"  Python:   {PYTHON}\n")

    cmd = [
        sys.executable, "-m", "pip", "download",
        "--dest",     PKG_DIR,
        "--platform", PLATFORM,
        "--python-version", "3.11",
        "--only-binary=:all:",
        "-r", REQUIREMENTS,
    ]

    print("  Running pip download...\n")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        whl_count = len([f for f in os.listdir(PKG_DIR) if f.endswith(".whl")])
        print(f"\n  Downloaded {whl_count} packages to: {PKG_DIR}")
        print("\n  To install on RPi (no internet needed):")
        print("    pip install --no-index --find-links=packages/ "
              "-r requirements.txt --break-system-packages")
    else:
        print("\n  Some packages failed. Pure-Python packages may need")
        print("  --no-binary flag. Try installing those separately.")

    print("\n" + "=" * 58)


if __name__ == "__main__":
    main()
