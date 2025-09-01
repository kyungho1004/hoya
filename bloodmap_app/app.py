
# -*- coding: utf-8 -*-
from datetime import datetime, date
import os, json, time

import streamlit as st

from config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE,
                    DISCLAIMER, ORDER, FEVER_GUIDE,
                    LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
                    LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP)

from bloodmap_app.data.drugs import ANTICANCER, ABX_GUIDE
from bloodmap_app.data.foods import FOODS, FOODS_SEASONAL, RECIPE_LINKS
from bloodmap_app.data.ped import PED_TOPICS, PED_INPUTS_INFO, PED_INFECT

from bloodmap_app.utils.inputs import num_input_generic, entered, _parse_numeric
from bloodmap_app.utils.interpret import interpret_labs, compare_with_previous, summarize_meds
from bloodmap_app.utils.reports import build_report, md_to_pdf_bytes_fontlocked
from bloodmap_app.utils.graphs import render_graphs
from bloodmap_app.utils.schedule import render_schedule

def _lookup_abx(name: str):
    """ABX_GUIDE가 dict/list/tuple/str 어떤 형태여도 안전하게 값 찾기."""
    g = ABX_GUIDE
    if isinstance(g, dict):
        return g.get(name)
    if isinstance(g, (list, tuple)):
        for it in g:
            if isinstance(it, dict):
                cand = it.get("name") or it.get("이름") or it.get("계열") or it.get("drug")
                if cand and name.lower() in str(cand).lower():
                    return it
            elif isinstance(it, str) and name.lower() in it.lower():
                return it
    return None

def abx_summary(abx_dict):
    lines=[]
    for k, amt in abx_dict.items():
        try: use=float(amt)
        except Exception: use=0.0
        if use>0:
            v = _lookup_abx(k)
            if isinstance(v, dict):
                tip = ", ".join(v.get("주의", v.get("tips", []))) if isinstance(v.get("주의"), list) else (v.get("주의","") or v.get("설명",""))
            elif isinstance(v, (list, tuple)):
                tip = ", ".join([str(x) for x in v])
            else:
                tip = str(v) if v is not None else ""
            shown=f"{int(use)}" if float(use).is_integer() else f"{use:.1f}"
            lines.append(f"• {k}: {shown}  — 주의: {tip}")
    return lines

def main():
    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    st.title(APP_TITLE)
    st.markdown(MADE_BY)
    st.markdown(CAFE_LINK_MD)
    st.caption("✅ 모바일 줄꼬임 방지 · 음식가이드 · 그래프/스케줄 · 보고서 PDF · ABX 견고화(예외 없음)")

    os.makedirs("fonts", exist_ok=True)

    if "records" not in st.session_state: st.session_state.records = {}
    if "schedules" not in st.session_state: st.session_state.schedules = {}

    # 환자/모드
    st.divider(); st.header("1️⃣ 환자/암·소아 정보")
    c1,c2 = st.columns(2)
    with c1: nickname = st.text_input("별명(저장/그래프/스케줄용)", placeholder="예: 홍길동")
    with c2: test_date = st.date_input("검사 날짜", value=date.today())
    anc_place = st.radio("현재 식사 장소(ANC 가이드용)", ["가정","병원"], horizontal=True)
    mode = st.selectbox("모드 선택", ["일반/암","소아(일상/호흡기)","소아(감염질환)"])

    group = cancer = infect_sel = ped_topic = None
    if mode == "일반/암":
        group = st.selectbox("암 그룹 선택", ["미선택/일반","혈액암","고형암","소아암","희귀암"])
        if group == "혈액암":
            cancer = st.selectbox("혈액암 종류", ["AML","APL","ALL","CML","CLL"])
        elif group == "고형암":
            cancer = st.selectbox("고형암 종류", ["폐암(Lung cancer)","유방암(Breast cancer)","위암(Gastric cancer)","대장암(Cololoractal cancer)"])
        else:
            st.info("암 그룹을 선택하면 해당 암종에 맞는 항암제 목록이 나타납니다.")
    elif mode == "소아(일상/호흡기)":
        st.markdown("### 🧒 소아 일상 주제 선택")
        st.caption(PED_INPUTS_INFO)
        ped_topic = st.selectbox("소아 주제", PED_TOPICS)
    else:
        st.markdown("### 🧫 소아·영유아 감염질환")
        infect_sel = st.selectbox("질환 선택", list(PED_INFECT.keys()))

    # 항암제/항생제
    meds = {}; extras = {}
    st.markdown("### 🧪 항생제 선택 및 입력")
    extras["abx"] = {}
    abx_choices = list(ABX_GUIDE.keys()) if isinstance(ABX_GUIDE, dict) else [str(k) for k in ABX_GUIDE]
    selected_abx = st.multiselect("항생제 계열 선택", abx_choices, default=[])
    for abx in selected_abx:
        extras["abx"][abx] = num_input_generic(f"{abx} - 복용/주입량", key=f"abx_{abx}", decimals=1, placeholder="예: 1")

    # 기본 입력
    st.divider(); st.header("2️⃣ 기본 입력")
    vals = {}
    for name in ORDER:
        if name == LBL_CRP:
            vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=2, placeholder="예: 0.12")
        elif name in (LBL_WBC, LBL_ANC, LBL_AST, LBL_ALT, LBL_LDH, LBL_BNP, LBL_Glu):
            vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=1, placeholder="예: 1200")
        else:
            vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=1, placeholder="예: 3.5")

    # 스케줄
    render_schedule(nickname)

    # 실행
    st.divider()
    if st.button("🔎 해석하기", use_container_width=True):
        st.subheader("📋 해석 결과")
        if mode == "일반/암":
            for line in interpret_labs(vals, extras): st.write(line)

            fs = []
            # 음식 가이드는 interpret에서 제공하거나 여기서 간단 표기 가능(생략)

        if extras.get("abx"):
            abx_lines = abx_summary(extras["abx"])
            if abx_lines:
                st.markdown("### 🧪 항생제 주의 요약")
                for l in abx_lines: st.write(l)

        st.markdown("### 🌡️ 발열 가이드")
        st.write(FEVER_GUIDE)

        meta = {"group": group, "cancer": cancer, "infect_sel": infect_sel, "anc_place": anc_place, "ped_topic": ped_topic}
        report_md = build_report(mode, meta, vals, [], {}, summarize_meds(meds) if meds else [], [], abx_summary(extras.get("abx", {})) if extras.get("abx") else [])

        st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                           mime="text/markdown")

        try:
            pdf_bytes = md_to_pdf_bytes_fontlocked(report_md)
            st.download_button("🖨️ 보고서(.pdf) 다운로드", data=pdf_bytes,
                               file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                               mime="application/pdf")
        except Exception as e:
            st.info("PDF 모듈이 없거나 폰트 미설치로 PDF 생성이 비활성화되었습니다.")

    # 그래프
    render_graphs()

    st.markdown("---")
    st.caption(FOOTER_CAFE)
    st.markdown("> " + DISCLAIMER)
