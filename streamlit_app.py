# -*- coding: utf-8 -*-
"""Launcher for Bloodmap App (v3.14).  
조건: 압축 해제 후 바로 `streamlit run streamlit_app.py` 실행 가능."""
import os, sys

# Ensure relative import to package works regardless of CWD
BASE = os.path.join(os.path.dirname(__file__), "bloodmap_app")
if BASE not in sys.path:
    sys.path.insert(0, BASE)

# Streamlit UI
try:
    import streamlit as st
except Exception as e:
    raise RuntimeError("Streamlit is required to run this app. `pip install streamlit`") from e

# Import main() from package
from bloodmap_app.app import main

# Optional page config
st.set_page_config(page_title="피수치 가이드 v3.14", layout="centered")

if __name__ == "__main__":
    main()