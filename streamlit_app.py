
from datetime import datetime, date
import streamlit as st

from bloodmap_app.config import FEVER_GUIDE
from bloodmap_app.data.drugs import ANTICANCER, ABX_GUIDE
from bloodmap_app.data.foods import FOODS
from bloodmap_app.data.ped import PED_TOPICS, PED_INPUTS_INFO, PED_INFECT
from bloodmap_app.utils.inputs import num_input_generic, entered
from bloodmap_app.utils.interpret import interpret_labs, compare_with_previous, food_suggestions, summarize_meds, abx_summary
from bloodmap_app.utils.reports import build_report, md_to_pdf_bytes_fontlocked
from bloodmap_app.utils.graphs import render_graphs
from bloodmap_app.utils.schedule import render_schedule

# ===== 방문 수 추적 =====
if "visit_count" not in st.session_state:
    st.session_state.visit_count = 0
st.session_state.visit_count += 1

# ===== 제목/소개 영역 =====
st.set_page_config(page_title="피수치 해석기 v3.14", layout="centered")
st.title("🩸 피수치 해석기 v3.14")
st.markdown("👤 제작자: Hoya / GPT")
st.markdown("📅 기준일: " + date.today().isoformat())
st.markdown("🔗 [공유 링크](https://hdzwo5ginueir7hknzzfg4.streamlit.app/)")
st.info("입력한 수치에 따라 해석과 음식 가이드를 제공합니다. 항암제 부작용 요약, 보고서 다운로드 가능.")
st.markdown(f"📊 현재 페이지 방문 수 (세션 기준): **{st.session_state.visit_count}회**")
st.caption("이 카운터는 임시입니다. 실제 누적 조회수/사용자 수는 향후 Supabase 등 외부 연동 시 가능.")
st.caption("보고서 다운로드 수, 평균 사용 시간도 추적 예정입니다.")

# ===== 수치 입력 =====
st.header("🧪 혈액 수치 입력")

vals = {}
for label in ["WBC(백혈구)", "Hb(적혈구)", "PLT(혈소판)", "ANC(호중구,면역력)", "Ca(칼슘)", "Na(나트륨)", "K(포타슘)",
              "Albumin(알부민)", "Glucose(혈당)", "Total Protein(총단백질)", "AST(간수치)", "ALT(간세포수치)",
              "LDH(유산탈수효소)", "CRP(염증수치)", "Cr(신장수치)", "UA(요산수치)", "TB(총빌리루빈)", "BUN(신장수치)", "BNP(심장척도)"]:
    vals[label] = num_input_generic(label, key=f"v_{label}", decimals=2 if label == "CRP(염증수치)" else 1, placeholder="예: 1.2")

# ===== 약물 입력 =====
st.header("💊 항암제 선택")

meds = {}
selected_drugs = st.multiselect("복용 중인 항암제 선택", list(ANTICANCER.keys()))
for d in selected_drugs:
    alias = ANTICANCER[d]["alias"]
    amt = num_input_generic(f"{d} ({alias}) - 용량/횟수", key=f"med_{d}", decimals=1, placeholder="예: 1.0")
    if amt and float(amt) > 0:
        meds[d] = {"dose_or_tabs": amt}

# ===== 이뇨제 입력 =====
extras = {}
st.header("💧 동반약제")
extras["diuretic_amt"] = num_input_generic("이뇨제 복용량(회/일)", key="diuretic_amt", decimals=1, placeholder="예: 1")

# ===== 실행 버튼 =====
if st.button("🔎 해석하기"):
    st.subheader("📋 해석 결과")

    # 해석 출력
    for line in interpret_labs(vals, extras):
        st.write(line)

    # 음식 가이드
    fs = food_suggestions(vals, "가정")
    if fs:
        st.markdown("### 🥗 음식 가이드")
        for f in fs: st.markdown(f)

    # 항암제 부작용 요약
    if meds:
        st.markdown("### 💊 항암제 요약")
        for line in summarize_meds(meds): st.write(line)

    # 발열 안내
    st.markdown("### 🌡️ 발열 가이드")
    st.write(FEVER_GUIDE)
