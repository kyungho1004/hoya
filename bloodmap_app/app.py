# -*- coding: utf-8 -*-
# Path fix (user-requested): make sure parent of this file (project root) is importable.
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from bloodmap_app.utils.interpret import interpret_labs, compare_with_previous, food_suggestions

def main():
    st.set_page_config(page_title="피수치 가이드 (경량본)", layout="centered")
    st.title("🩸 피수치 가이드 (경량본)")
    st.caption("모듈 경로 꼬임 방지 적용 · 기본 ANC/CRP 해석 · 데모용 최소 구성")

    # --- Inputs
    st.header("1) 기본 입력")
    nickname = st.text_input("별명(옵션)")
    anc_place = st.radio("현재 식사 장소", ["가정", "병원"], horizontal=True)
    st.header("2) 검사 수치")
    vals = {}
    cols = st.columns(2)
    with cols[0]:
        vals["ANC"] = st.text_input("ANC", placeholder="예: 1200")
        vals["Hb"]  = st.text_input("Hb", placeholder="예: 12.5")
        vals["PLT"] = st.text_input("혈소판", placeholder="예: 150")
    with cols[1]:
        vals["CRP"] = st.text_input("CRP", placeholder="예: 0.2")
        vals["Na"]  = st.text_input("Na", placeholder="예: 140")
        vals["K"]   = st.text_input("K", placeholder="예: 4.1")

    st.divider()
    if st.button("🔎 해석하기", use_container_width=True):
        st.subheader("📋 해석 결과")
        for line in interpret_labs(vals, {}):
            st.write(line)

        st.markdown("### 🥗 음식 가이드")
        fs = food_suggestions(vals, anc_place)
        for f in (fs or ["입력값 기준 추가 권장 없음"]):
            st.write("- " + f)

        if nickname:
            st.markdown("### 비교(데모)")
            for l in compare_with_previous(nickname, vals):
                st.write(l)

    st.markdown("---")
    st.caption("이 경량본은 경로 문제 해결을 위한 테스트용입니다. 전체 기능 합본은 이후 단계에서 모듈만 교체하면 됩니다.")

if __name__ == "__main__":
    main()
