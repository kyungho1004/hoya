
# -*- coding: utf-8 -*-
import importlib, types, streamlit as st
from pathlib import Path

# Optional CSS
css_path = Path(__file__).with_name("style.css")
if css_path.exists():
    try:
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    except Exception:
        pass

def _call_if_exists(mod: types.ModuleType) -> bool:
    for fname in ("main", "app", "run"):
        fn = getattr(mod, fname, None)
        if callable(fn):
            fn()
            return True
    return False

def main():
    # Prefer user's app module
    try:
        user_mod = importlib.import_module("bloodmap.app_user")
        if _call_if_exists(user_mod):
            return
    except Exception as e:
        st.warning(f"사용자 app 불러오기 오류: {e}")

    st.error("bloodmap.app_user 에 main/app/run 이 없습니다.")
