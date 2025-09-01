# -*- coding: utf-8 -*-
from __future__ import annotations

import streamlit as st
from typing import Dict, Any, List

# Local imports
from .utils import apply_css, food_recommendations, number_or_none, only_entered_values
from .drug_data import ANTICANCER

try:
    import config as APP_CONFIG  # project_root/config.py
except Exception:
    class _C:  # fallback
        APP_NAME = "피수치 가이드"
        VERSION = "v3.14"
        AUTHOR = "Hoya/GPT"
        CONSULT = "Hoya/GPT"
    APP_CONFIG = _C()

def _top_header():
    st.title(f"🩸 {APP_CONFIG.APP_NAME}  ({APP_CONFIG.VERSION})")
    st.caption(f"제작: {APP_CONFIG.AUTHOR} · 자문: {APP_CONFIG.CONSULT}")

def _general_tab():
    st.subheader("기본 수치 입력")
    col1, col2 = st.columns(2)
    with col1:
        wbc = st.number_input("WBC (x10³/µL)", min_value=0.0, step=0.1, format="%.1f")
        hb  = st.number_input("Hb (g/dL)", min_value=0.0, step=0.1, format="%.1f")
        plt = st.number_input("혈소판 (x10³/µL)", min_value=0.0, step=1.0, format="%.0f")
    with col2:
        anc = st.number_input("호중구 ANC (cells/µL)", min_value=0.0, step=10.0, format="%.0f")
        alb = st.number_input("Albumin (g/dL)", min_value=0.0, step=0.1, format="%.1f")
        k   = st.number_input("K⁺ (mmol/L)", min_value=0.0, step=0.1, format="%.1f")

    entered = only_entered_values({
        "WBC": number_or_none(wbc),
        "Hb": number_or_none(hb),
        "PLT": number_or_none(plt),
        "ANC": number_or_none(anc),
        "Albumin": number_or_none(alb),
        "K": number_or_none(k),
    })

    st.markdown("### 입력한 수치")
    if not entered:
        st.info("입력한 수치가 없습니다. 값을 입력하면 여기 표시됩니다.")
    else:
        for k_, v_ in entered.items():
            st.write(f"- **{k_}**: {v_}")

    st.markdown("### 간단 해석 & 음식 가이드")
    recs = food_recommendations(entered)
    if recs:
        for title, foods in recs:
            st.write(f"**{title}** → " + ", ".join(foods))
        if "ANC" in entered and entered["ANC"] < 500:
            st.warning("호중구(ANC) 500 미만: 생채소 금지, 모든 음식은 충분히 가열(전자레인지 30초 이상), "
                       "조리 후 남은 음식은 2시간 이후 섭취 금지, 껍질 있는 과일은 주치의와 상담 후 결정.")
    else:
        st.info("조건에 해당하는 음식 가이드가 없습니다.")

def _drug_tab():
    st.subheader("항암제 간단 보기 (샘플)")
    q = st.text_input("약물 검색 (이름 또는 별칭 일부)", "")
    names = sorted(ANTICANCER.keys())
    filtered = [n for n in names if q.strip() == "" or q.lower() in n.lower() or q.lower() in ANTICANCER.get(n, {}).get("alias", "").lower()]
    if not filtered:
        st.info("검색 결과가 없습니다.")
        return
    sel = st.selectbox("약물 선택", filtered, index=0)
    data = ANTICANCER.get(sel, {})
    with st.container(border=True):
        st.markdown(f"**이름:** {sel}")
        if data.get("alias"):
            st.markdown(f"**별칭:** {data['alias']}")
        if data.get("notes"):
            st.markdown(f"**요약:** {data['notes']}")

def _help_tab():
    st.subheader("도움말")
    st.markdown("""
- 이 버전(v3.14)은 **모바일 화면 최적화**와 **기본 구조 안정화**에 집중한 패키지입니다.
- *streamlit run streamlit_app.py* 로 실행하세요.
- 화면 상단에 입력한 수치만 표시되며, 조건에 따라 음식 가이드가 나타납니다.
- 항암제 탭은 검색/선택 기반 요약 미니 사전(샘플)입니다.
""")

def main():
    # 페이지/레이아웃 설정은 가장 먼저!
    st.set_page_config(page_title=f"{APP_CONFIG.APP_NAME} {APP_CONFIG.VERSION}", layout="wide")
    apply_css()

    _top_header()
    t1, t2, t3 = st.tabs(["일반 해석", "항암제", "도움말"])
    with t1:
        _general_tab()
    with t2:
        _drug_tab()
    with t3:
        _help_tab()
