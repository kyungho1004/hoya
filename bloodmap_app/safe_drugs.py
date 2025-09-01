
# -*- coding: utf-8 -*-
import streamlit as st
from bloodmap_app.drugs import ANTICANCER

def render_drug_panel():
    st.subheader("💊 항암치료 · 약물 요약 (안전 모드)")
    search = st.text_input("약물 검색(영문/한글 별칭 가능)", value="").strip().lower()
    try:
        items = []
        for name, meta in ANTICANCER.items():
            nm = str(name).lower()
            alias = str(meta.get("alias","")).lower()
            if (not search) or (search in nm) or (search in alias):
                items.append((name, meta))
        if not items:
            st.info("검색 결과가 없습니다.")
            return
        for name, meta in items:
            title = "• " + str(name) + " (" + str(meta.get("alias","")) + ")"
            with st.expander(title, expanded=False):
                st.write("분류: " + str(meta.get("class","-")))
                for n in meta.get("notes", []) or meta.get("aes", []):
                    st.markdown("- " + str(n))
    except Exception as e:
        st.warning("약물 섹션 로드 중 오류가 있었지만 앱은 계속 실행됩니다.")
        try: st.exception(e)
        except Exception: pass
