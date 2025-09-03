\
import streamlit as st

def render_schedule(nickname):
    st.markdown("### 🗓️ 항암 스케줄 표")
    st.caption("별명별로 주차/일정 메모 기능(간단 버전)")
    if not nickname:
        st.info("별명을 입력하면 스케줄을 기록/보기 할 수 있어요.")
        return
    plan = st.text_area("이번 주 메모", key=f"sched_{nickname}", placeholder="예: 9/3 ARA-C 저용량 SC, 9/5 외래 방문 ...")
    if st.button("메모 저장", key=f"sched_btn_{nickname}"):
        st.session_state.schedules.setdefault(nickname, []).append(plan)
        st.success("저장되었습니다.")
    if st.session_state.schedules.get(nickname):
        st.write("이전 메모:")
        for i, p in enumerate(reversed(st.session_state.schedules[nickname][-5:]), 1):
            st.write(f"- {p}")
