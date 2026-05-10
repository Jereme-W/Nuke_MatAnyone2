"""Nuke plugin bootstrap for MatAnyone2 for Nuke."""

from __future__ import annotations

import os
import sys


PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
VENDOR_DIR = os.path.join(PLUGIN_DIR, "vendor", "py310")

for path in (VENDOR_DIR, PLUGIN_DIR):
    if os.path.isdir(path) and path not in sys.path:
        sys.path.insert(0, path)

