# 🔬 피수치 자동 해석기 최종 통합본 (코비&형)
# - 항암제 부작용 포함
# - 수치 순서 고정
# - 입력한 수치만 출력
# - 모바일 줄 꼬임 방지
# - 보고서 다운로드 기능
# - Streamlit 기반


import streamlit as st
import datetime
import json
import os


# 페이지 설정
st.set_page_config(page_title="피수치 자동 해석기", layout="centered")
st.title("🔬 피수치 자동 해석기 by Hoya")


# 별명 입력 및 저장 경로 설정
nickname = st.text_input("👤 별명을 입력하세요:")
data_path = "saved_results.json"


# 수치 입력 항목 순서 (고정)
lab_order = [
("WBC (백혈구)", "wbc"),
("Hb (혈색소)", "hb"),
("혈소판 (PLT)", "plt"),
("ANC (호중구)", "anc"),
("칼슘 (Ca)", "ca"),
("인 (P)", "p"),
("나트륨 (Na)", "na"),
("칼륨 (K)", "k"),
("알부민 (Albumin)", "alb"),
("혈당 (Glucose)", "glu"),
("총단백 (Total Protein)", "tp"),
("AST", "ast"),
("ALT", "alt"),
("LDH", "ldh"),
("CRP", "crp"),
("Creatinine (Cr)", "cr"),
("요산 (UA)", "ua"),
("총빌리루빈 (TB)", "tb"),
("BUN", "bun"),
("BNP (선택)", "bnp")
]


# 사용자 입력 저장용 딕셔너리
user_input = {}


st.markdown("---")
st.subheader("🧪 혈액 수치 입력")


# 수치 입력
for label, key in lab_order:
val = st.number_input(label, min_value=0.0, step=0.1, format="%.2f", key=key)
if val != 0.0:
user_input[key] = val


# 항암제 복용 여부 입력
st.markdown("---")
st.subheader("💊 항암제 복용 정보")
chemo_input = {}
chemo_list = ["6-MP", "MTX", "베사노이드", "아라씨", "그라신"]


for drug in chemo_list:
count = st.text_input(f"{drug} 복용량 (정/일):", key=f"{drug}_dose")
if count:
chemo_input[drug] = count


# 해석 버튼
st.markdown("---")
if st.button("🔍 해석하기"):
st.success("✅ 해석 결과를 아래에 표시합니다.")


st.markdown("### 📄 결과 요약")
for k, v in user_input.items():
