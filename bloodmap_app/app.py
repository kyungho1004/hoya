
import streamlit as st
from bloodmap_app.config import ORDER, EXPLAIN, ALIAS
from bloodmap_app.utils.foods import FOOD_RECOMMENDATIONS
from bloodmap_app.utils.analysis import analyze_blood_data

def main():
    st.set_page_config(page_title="피수치 가이드", layout="centered")
    st.title("🩸 피수치 가이드 실행 중")

    st.subheader("수치를 입력하세요")
    user_data = {}
    for item in ORDER:
        value = st.text_input(f"{item}", key=item)
        if value:
            try:
                user_data[item] = float(value)
            except ValueError:
                st.warning(f"{item}은 숫자로 입력해야 합니다.")

    if st.button("해석하기") and user_data:
        st.subheader("📊 해석 결과")
        result = analyze_blood_data(user_data)
        st.write(result)

        st.subheader("🥗 음식 추천")
        recommendations = FOOD_RECOMMENDATIONS(user_data)
        st.write(recommendations)
