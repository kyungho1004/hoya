import streamlit as st
def render_schedule(nickname):
    st.markdown(f"🗓️ {nickname or '무명'} 스케줄(데모) — 항암 주기/통원 일정은 다음 업데이트에 저장/불러오기 지원")
