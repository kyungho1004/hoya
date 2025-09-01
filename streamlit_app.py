# -*- coding: utf-8 -*-
"""Streamlit launcher for BloodMap (imports package and executes app)."""
import os, sys

ROOT = os.path.dirname(__file__)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Ensure runtime fonts dir exists (optional, used by PDF)
os.makedirs(os.path.join(ROOT, "fonts"), exist_ok=True)

# Importing the package module executes Streamlit code at module scope.
import bloodmap_app.app  # noqa: F401
