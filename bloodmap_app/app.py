
from datetime import date
import streamlit as st

# ===== 세션 방문 수 추적 =====
if "visit_count" not in st.session_state:
    st.session_state.visit_count = 0
st.session_state.visit_count += 1

# ===== 디버그용 제목 (버전명 확인용) =====
st.set_page_config(page_title="피수치 가이드 v3.14 ✅ DEBUG", layout="centered")
st.title("🩸 피수치 가이드 v3.14 ✅✅✅ DEBUG 확인용")
st.markdown("👤 제작자: Hoya / GPT")
st.markdown("📅 기준일: " + date.today().isoformat())

# ===== 공유 버튼 =====
st.markdown("🔗 [공유 링크](https://hdzwo5ginueir7hknzzfg4.streamlit.app/)")

# ===== 조회수 표시 =====
st.markdown(f"📊 현재 페이지 방문 수 (세션 기준): **{st.session_state.visit_count}회**")
