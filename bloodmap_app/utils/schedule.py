
import streamlit as st

def render_schedule(nickname: str):
    st.markdown("### 🗓️ 항암 스케줄/메모")
    if not nickname:
        st.caption("별명을 입력하면 스케줄을 저장할 수 있어요.")
        return
    if "schedules" not in st.session_state:
        st.session_state.schedules = {}
    sched = st.session_state.schedules.setdefault(nickname, [])
    note = st.text_input("메모/스케줄 입력", key=f"sched_{nickname}")
    if st.button("추가", key=f"sched_add_{nickname}") and note.strip():
        sched.append({"text": note.strip()})
    if sched:
        for i, item in enumerate(sched, 1):
            st.write(f"{i}. {item['text']}")
