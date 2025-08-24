
import streamlit as st

st.set_page_config(page_title="피수치 자동 해석기", layout="centered")
st.title("🔬 피수치 자동 해석기 by Hoya")
st.write("여기에 수치를 입력하고 해석 결과를 확인하세요.")

# 간단한 입력 예시
wbc = st.number_input("WBC (백혈구)", min_value=0.0, step=0.1)
hb = st.number_input("Hb (헤모글로빈)", min_value=0.0, step=0.1)
plt = st.number_input("혈소판 (PLT)", min_value=0.0, step=1.0)
anc = st.number_input("ANC (호중구)", min_value=0.0, step=1.0)

# 간단한 해석 출력
if st.button("해석하기"):
    st.subheader("🧾 결과 요약")
    if anc < 500:
        st.warning("⚠️ 호중구 수치 낮음 → 감염주의 필요")
    else:
        st.success("✅ 호중구 수치 안정적")

    if hb < 8:
        st.warning("⚠️ 빈혈 위험")
    if plt < 50:
        st.warning("⚠️ 출혈 위험")
    if wbc > 11:
        st.info("ℹ️ 백혈구 수치 상승 가능성 있음")

st.caption("제작: Hoya / 자문: Hoya-GPT")
