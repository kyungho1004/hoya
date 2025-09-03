# -*- coding: utf-8 -*-
import importlib, types, streamlit as st
from pathlib import Path

def _call_if_exists(mod: types.ModuleType) -> bool:
    for fname in ("main", "app", "run"):
        fn = getattr(mod, fname, None)
        if callable(fn):
            fn()
            return True
    return False

def main():
    # 1) strict relative import: bloodmap_app.app_user
    try:
        from . import app_user as user_mod
    except Exception as e_rel:
        # 2) module name fallback
        try:
            user_mod = importlib.import_module("bloodmap_app.app_user")
        except Exception as e_abs:
            st.warning(f"사용자 app 불러오기 오류: {e_abs}")
            st.error("bloodmap_app.app_user 모듈을 찾지 못했습니다.")
            return

    if not _call_if_exists(user_mod):
        st.error("bloodmap_app.app_user 에 main/app/run 이 없습니다.")
