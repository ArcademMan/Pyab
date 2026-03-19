"""
Build script for PyAB using Nuitka (standalone, no onefile).
Usage: python build.py
"""

import subprocess
import sys

CMD = [
    sys.executable, "-m", "nuitka",

    # ── Output mode ──────────────────────────────────────────────
    "--standalone",

    # ── Info ──────────────────────────────────────────────────────
    "--company-name=AmMstools",
    "--product-name=PyAB",
    "--product-version=1.0.0",
    "--file-description=PyAB - Game Backup Manager",
    "--copyright=AmMstools",

    # ── Icon ─────────────────────────────────────────────────────
    "--windows-icon-from-ico=Pyab.ico",

    # ── Output name ────────────────────────────────────────────
    "--output-filename=Pyab.exe",

    # ── No console ───────────────────────────────────────────────
    "--windows-console-mode=disable",

    # ── PySide6 plugin ───────────────────────────────────────────
    "--enable-plugin=pyside6",

    # ── Include data ─────────────────────────────────────────────
    "--include-data-dir=assets=assets",
    "--include-data-dir=core/shared/locale=core/shared/locale",

    # ── Hidden imports ───────────────────────────────────────────
    "--include-module=win32gui",
    "--include-module=win32process",
    "--include-module=win32api",
    "--include-module=mss",
    "--include-module=mss.windows",
    "--include-module=PIL",
    "--include-module=psutil",
    "--include-module=watchdog",
    "--include-module=watchdog.observers",
    "--include-module=watchdog.events",

    # ── Cleanup ──────────────────────────────────────────────────
    "--remove-output",

    # ── Entry point ──────────────────────────────────────────────
    "launcher.py",
]

if __name__ == "__main__":
    print("Building PyAB with Nuitka (standalone)...")
    print(f"Command: {' '.join(CMD)}\n")
    sys.exit(subprocess.call(CMD))
