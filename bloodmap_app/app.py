
import streamlit as st
from .config import ORDER, EXPLAIN, ALIAS

def main():
    st.title("🩸 피수치 가이드 실행 중")

    st.header("주문:")
    st.write(ORDER)

    st.header("설명하다:")
    st.write(EXPLAIN)

    st.header("별명:")
    st.write(ALIAS)

    # 예시 기능 - 수치 입력 받기
    st.header("📥 수치 입력")
    values = {}
    for key in ORDER:
        values[key] = st.number_input(f"{key} 입력", value=0.0)

    st.header("🧠 해석 결과")
    for k, v in values.items():
        if v == 0:
            st.warning(f"{k} 수치가 입력되지 않았습니다.")
        else:
            st.success(f"{ALIAS[k]}({k}) = {v} → {EXPLAIN[k]}")

    st.markdown("---")
    st.caption("🔧 자문: Hoya / GPT")
