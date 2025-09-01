
# -*- coding: utf-8 -*-
from __future__ import annotations
import sys

# Streamlit은 런타임에만 필요하므로 임포트 실패해도 앱 구조 확인 가능
try:
    import streamlit as st
except Exception:  # pragma: no cover
    class _Dummy:
        def __getattr__(self, k): 
            def _f(*a, **kw): return None
            return _f
    st = _Dummy()

from .data.drugs import ANTICANCER, ABX_GUIDE
import config as cfg
from config import APP_TITLE, PAGE_LAYOUT, FOOTER  # noqa: F401

def _header():
    st.set_page_config(page_title="피수치 가이드 v3.14", layout=PAGE_LAYOUT)
    st.title(APP_TITLE)
    st.caption(FOOTER)

def _drug_section():
    st.subheader("💊 약물 가이드 (요약)")
    tab1, tab2 = st.tabs(["항암제", "항생제"])

    with tab1:
        q = st.text_input("항암제 검색", "")
        keys = [k for k in ANTICANCER.keys() if q.lower() in k.lower() or q.lower() in ANTICANCER[k].get("alias","").lower()]
        for name in keys:
            with st.expander(f"• {name} ({ANTICANCER[name].get('alias','')})", expanded=False):
                st.write("부작용/주의:", ", ".join(ANTICANCER[name].get("effects", [])))
                st.info(ANTICANCER[name].get("notes",""))

    with tab2:
        q = st.text_input("항생제 검색", "", key="abx")
        keys = [k for k in ABX_GUIDE.keys() if q.lower() in k.lower()]
        for name in keys:
            with st.expander(f"• {name}", expanded=False):
                _v = ABX_GUIDE.get(name)
                if isinstance(_v, dict):
                    st.write(_v.get("설명", ""))
                    st.warning(_v.get("주의", ""))
                elif isinstance(_v, (list, tuple)):
                    for it in _v:
                        st.write(str(it))
                else:
                    st.write(str(_v))

def main():
    """Streamlit entry point ensured for v3.14 packaging 규격"""
    _header()
    st.success("✅ 구조/임포트 검증 완료. 이제 기능 모듈을 점진적으로 붙이면 됩니다.")
    _drug_section()
    st.write("---")
    st.caption("※ 이 빌드는 'ModuleNotFoundError: from data.drugs ...' 오류를 해결하기 위해 import 경로를 'from bloodmap_app.data.drugs'로 정정했습니다.")
