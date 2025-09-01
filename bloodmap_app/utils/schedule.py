
# -*- coding: utf-8 -*-
try:
    import streamlit as st
except Exception:
    class _Dummy:
        def __getattr__(self, k):
            def _f(*a, **kw): return None
            return _f
    st = _Dummy()

from datetime import date

def render_schedule(nickname: str):
    st.divider()
    st.header("📆 항암 스케줄표 (별명별 관리)")
    if nickname and nickname.strip():
        st.session_state.schedules.setdefault(nickname, [])
        colA, colB, colC = st.columns([1,1,2])
        with colA:
            sch_date = st.date_input("날짜 선택", value=date.today(), key="sch_date")
        with colB:
            sch_drug = st.text_input("항암제/치료명", key="sch_drug", placeholder="예: ARA-C, MTX, 외래채혈")
        with colC:
            sch_note = st.text_input("비고(용량/주기 등)", key="sch_note", placeholder="예: HDAC Day1, 100mg/m2")

        if st.button("➕ 일정 추가", use_container_width=True):
            st.session_state.schedules[nickname].append({
                "date": sch_date.isoformat(),
                "drug": sch_drug.strip(),
                "note": sch_note.strip()
            })
            st.success("스케줄이 추가되었습니다.")
    else:
        st.info("별명을 입력하면 스케줄표를 사용할 수 있어요.")
