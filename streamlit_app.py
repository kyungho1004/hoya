# -*- coding: utf-8 -*-
"""Launcher for Bloodmap v3.14 (mobile-friendly)."""
import os, sys

# Ensure local imports work both in Streamlit Cloud and local runs
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from bloodmap_app.app import main  # noqa: E402

if __name__ == "__main__":
    # When executed directly: run main()
    main()
