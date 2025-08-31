
from datetime import date
import streamlit as st

# ===== 간단한 조회수 추적 (세션 단위) =====
if "visit_count" not in st.session_state:
    st.session_state.visit_count = 0
st.session_state.visit_count += 1

# ===== 타이틀 영역 =====
st.set_page_config(page_title="피수치 가이드 v3.14", layout="centered")
st.title("🩸 피수치 해석기 v3.14")
st.markdown("👤 제작자: Hoya / GPT")
st.markdown("📅 기준일: " + date.today().isoformat())
st.markdown("🔗 [공유 링크](https://hdzwo5ginueir7hknzzfg4.streamlit.app/)")

# ===== 사용 안내 =====
st.info("입력한 수치에 따라 해석과 음식 가이드를 제공합니다. 항암제 부작용 요약, 보고서 다운로드 가능.")

# ===== 조회수 카운터 =====
st.markdown(f"📊 현재 페이지 방문 수 (세션 기준): **{st.session_state.visit_count}회**")

# ===== 향후 기능 안내 =====
st.caption("""
- 이 카운터는 임시입니다. 실제 누적 조회수/사용자 수는 향후 Supabase 등 외부 연동 시 가능.
- 보고서 다운로드 수, 평균 사용 시간도 추적 예정입니다.
""")
