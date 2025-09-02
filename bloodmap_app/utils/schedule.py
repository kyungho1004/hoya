
import streamlit as st

def render_schedule(nickname: str):
    st.header("🗓️ 스케줄")
    if not nickname:
        st.info("별명을 입력하면 스케줄을 저장할 수 있어요.")
        return
    sch = st.session_state.setdefault("schedules", {}).setdefault(nickname, [])
    with st.form(key="sch_form", clear_on_submit=True):
        date = st.date_input("날짜")
        note = st.text_input("메모", placeholder="예: 외래/CT/항암 D1")
        submitted = st.form_submit_button("추가")
    if submitted and note:
        sch.append({"date": str(date), "note": note})
        st.success("추가됨")
    if sch:
        for item in sch[-10:]:
            st.write(f"- {item['date']}: {item['note']}")
