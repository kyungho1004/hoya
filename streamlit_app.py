
# -*- coding: utf-8 -*-
import streamlit as st, traceback
st.set_page_config(page_title="피수치 가이드", layout="centered")

try:
    from bloodmap_app.app import main
except Exception:
    st.title("🚨 초기화 오류")
    st.caption("Import 단계에서 예외가 발생했습니다. 아래 로그를 개발자에게 전달하세요.")
    st.code(traceback.format_exc())
else:
    try:
        main()
    except Exception:
        st.title("🚨 실행 중 오류")
        st.code(traceback.format_exc())
