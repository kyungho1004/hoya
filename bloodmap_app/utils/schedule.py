# -*- coding: utf-8 -*-
import streamlit as st

def render_schedule(nickname_key):
    st.markdown("### 🗓️ 항암 스케줄")
    if not nickname_key:
        st.caption("※ 별명을 입력하면 스케줄을 저장할 수 있어요.")
        return
    if "schedules" not in st.session_state:
        st.session_state.schedules = {}
    plan = st.text_area("스케줄 메모", key=f"sch_{nickname_key}", placeholder="예: D1 ARA-C, D3 G-CSF 시작 ...")
    if st.button("스케줄 저장", key=f"sch_btn_{nickname_key}"):
        st.session_state.schedules[nickname_key] = plan
        st.success("스케줄 저장 완료")
