
# -*- coding: utf-8 -*-
import streamlit as st
st.set_page_config(page_title="피수치 가이드 / BloodMap", layout="centered")
st.caption("✅ 엔트리포인트 OK — from bloodmap_app.app import main → main()")
from bloodmap_app.app import main
if __name__ == "__main__":
    main()
