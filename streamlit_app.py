# -*- coding: utf-8 -*-
"""Launcher that preserves original imports (data.*, utils.*)."""
import os, sys
BASE = os.path.join(os.path.dirname(__file__), "bloodmap_app")
if BASE not in sys.path:
    sys.path.insert(0, BASE)
import app  # noqa: F401
