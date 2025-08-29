
from datetime import date
import streamlit as st
def render_schedule(nickname: str):
    st.subheader("📆 항암 스케줄표")
    st.info("별명 입력 시 스케줄 관리가 가능합니다.")
