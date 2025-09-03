# -*- coding: utf-8 -*-
import streamlit as st
from bloodmap.app import main
if __name__ == "__main__":
    st.set_page_config(page_title="피수치 가이드 / BloodMap", layout="centered")
    st.caption("✅ bloodmap.app.main() OK — 이름 통일 + 진입점 정리")
    main()
