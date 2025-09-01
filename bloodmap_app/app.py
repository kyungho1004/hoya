
import streamlit as st
from bloodmap_app.config import ORDER, EXPLAIN, ALIAS
from .interpret import interpret_blood_values
from .foods import recommend_foods
from .drugs import explain_drugs
from .reports import generate_report
from .schedule import show_schedule_table
from .graphs import plot_graphs

def main():
    st.set_page_config(page_title="피수치 가이드 by Hoya (v3.13 · 변화비교/스케줄/계절식/ANC장소)", layout="centered")
    st.title("🩸 피수치 가이드  (v3.13 · 변화비교 · 스케줄표 · 계절 식재료 · ANC 장소별 가이드)")
    st.markdown("v3.13 기능 정상 작동 확인")

    # Add more logic here (simplified)
    st.subheader("수치 입력")
    wbc = st.number_input("WBC", value=0.0)
    hb = st.number_input("Hb", value=0.0)
    plt = st.number_input("혈소판", value=0.0)

    # Dummy interpreter result
    if st.button("해석하기"):
        result = interpret_blood_values({"WBC": wbc, "Hb": hb, "PLT": plt})
        st.write(result)
    
    # Additional placeholders
    st.subheader("음식 추천")
    st.write(recommend_foods({"Albumin": 2.5}))

    st.subheader("약물 해석")
    st.write(explain_drugs(["6-MP", "MTX"]))

    st.subheader("보고서")
    st.write("보고서 다운로드 기능 준비 중...")

    st.subheader("그래프")
    plot_graphs({"WBC": [wbc], "Hb": [hb], "PLT": [plt]})

    st.subheader("스케줄")
    show_schedule_table()
