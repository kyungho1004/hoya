import streamlit as st

st.set_page_config(page_title="피수치 자동 해석기", layout="centered")
st.title("🔬 피수치 자동 해석기 by Hoya")
st.write("혈액 수치를 입력하고 해석 결과 및 영양 가이드를 확인하세요.")

# 입력값 받기
wbc = st.number_input("WBC (백혈구)", min_value=0.0, step=0.1)
hb = st.number_input("Hb (헤모글로빈)", min_value=0.0, step=0.1)
plt = st.number_input("혈소판 (PLT)", min_value=0.0, step=1.0)
anc = st.number_input("ANC (호중구)", min_value=0.0, step=1.0)
alb = st.number_input("Albumin (알부민)", min_value=0.0, step=0.1)
k = st.number_input("K⁺ (칼륨)", min_value=0.0, step=0.1)
na = st.number_input("Na⁺ (소디움)", min_value=0.0, step=0.1)
ca = st.number_input("Ca²⁺ (칼슘)", min_value=0.0, step=0.1)

# 해석 결과 출력
if st.button("해석하기"):
    st.subheader("🧾 결과 요약")

    if anc < 500:
        st.warning("⚠️ 호중구 수치 낮음 → 감염주의 필요")
        st.info("🥗 음식 가이드: 생채소 금지, 익힌 음식 권장, 멸균/살균 식품 선호. 남은 음식은 2시간 이내 섭취, 껍질 있는 과일은 주치의 상담 후 결정.")
    else:
        st.success("✅ 호중구 수치 안정적")

    if hb < 8:
        st.warning("⚠️ 심한 빈혈 가능성")
        st.info("🥗 추천 음식: 소고기, 시금치, 두부, 달걀 노른자, 렌틸콩")

    if plt < 50:
        st.warning("⚠️ 출혈 위험")

    if wbc > 11:
        st.info("ℹ️ 백혈구 수치 상승 → 감염 또는 염증 가능성")

    if alb < 3.5:
        st.warning("⚠️ 알부민 수치 낮음 → 영양 상태 저하 가능")
        st.info("🥗 추천 음식: 달걀, 연두부, 흰살 생선, 닭가슴살, 귀리죽")

    if k < 3.5:
        st.warning("⚠️ 저칼륨혈증 위험")
        st.info("🥗 추천 음식: 바나나, 감자, 고구마, 호박죽, 오렌지")

    if na < 135:
        st.warning("⚠️ 저나트륨혈증 가능성")
        st.info("🥗 추천 음식: 전해질 음료, 미역국, 바나나, 오트밀죽, 삶은 감자")

    if ca < 8.5:
        st.warning("⚠️ 저칼슘혈증 가능성")
        st.info("🥗 추천 음식: 연어통조림, 두부, 케일, 브로콜리")

st.caption("제작: Hoya / 자문: Hoya-GPT")

