
from datetime import date
import os, pathlib
import streamlit as st

from config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE,
                    DISCLAIMER, ORDER, FEVER_GUIDE,
                    LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
                    LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP)
from utils.inputs import num_input_generic, entered
from utils.interpret import interpret_labs, compare_with_previous, food_suggestions, summarize_meds, abx_summary
from utils.graphs import render_graphs
from utils.schedule import render_schedule

st.set_page_config(page_title=PAGE_TITLE, layout="centered")
st.title(APP_TITLE)
st.caption(MADE_BY)
st.markdown(CAFE_LINK_MD)
st.sidebar.info(f"RUNNING FILE: {pathlib.Path(__file__).as_posix()}")

if "records" not in st.session_state: st.session_state.records = {}
if "schedules" not in st.session_state: st.session_state.schedules = {}

st.header("1️⃣ 환자/모드")
nickname = st.text_input("별명", placeholder="예: 홍길동")
anc_place = st.radio("현재 식사 장소(ANC 가이드용)", ["가정", "병원"], horizontal=True)

st.header("2️⃣ 기본 혈액 검사 수치")
vals = {}
for name in ORDER:
    if name == LBL_CRP:
        vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=2, placeholder="예: 0.12")
    else:
        vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=1, placeholder="예: 3.5")

st.header("3️⃣ 스케줄")
render_schedule(nickname)

if st.button("🔎 해석하기", use_container_width=True):
    st.subheader("📋 해석 결과")
    for line in interpret_labs(vals, {"diuretic_amt":0}): st.write(line)
    for f in food_suggestions(vals, anc_place): st.markdown(f)
    st.markdown("### 🌡️ 발열 가이드")
    st.write(FEVER_GUIDE)

render_graphs()

st.markdown("---")
st.caption(FOOTER_CAFE)
st.markdown("> " + DISCLAIMER)
