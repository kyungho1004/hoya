# -*- coding: utf-8 -*-
"""
Streamlit runner for BloodMap.
Usage:
    streamlit run streamlit_app.py
"""
import streamlit as st
from bloodmap_app.app import main

if __name__ == "__main__":
    st.set_page_config(page_title="피수치 가이드 / BloodMap", layout="centered")
    st.caption("✅ bloodmap_app.app.main() OK — 이 화면 보이면 경로 문제 해결!")
    main()
