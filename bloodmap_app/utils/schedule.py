
from datetime import date
import streamlit as st
def render_schedule(nickname: str):
    st.divider()
    st.header("📆 항암 스케줄표 (별명별 관리)")
    if nickname and nickname.strip():
        st.session_state.schedules.setdefault(nickname, [])
        colA, colB, colC = st.columns([1,1,2])
        with colA: sch_date = st.date_input("날짜 선택", value=date.today(), key="sch_date")
        with colB: sch_drug = st.text_input("항암제/치료명", key="sch_drug", placeholder="예: ARA-C, MTX, 외래채혈")
        with colC: sch_note = st.text_input("비고(용량/주기 등)", key="sch_note", placeholder="예: HDAC Day1, 100mg/m2")
        if st.button("➕ 일정 추가", use_container_width=True):
            st.session_state.schedules[nickname].append({"date": sch_date.isoformat(), "drug": sch_drug.strip(), "note": sch_note.strip()})
            st.success("스케줄이 추가되었습니다.")
        rows = st.session_state.schedules.get(nickname, [])
        if rows:
            try:
                import pandas as pd
                df = pd.DataFrame(rows).sort_values("date")
                st.table(df); csv = df.to_csv(index=False).encode("utf-8-sig")
                st.download_button("📥 스케줄(.csv) 다운로드", data=csv, file_name=f"{nickname}_schedule.csv", mime="text/csv")
            except Exception:
                for r in sorted(rows, key=lambda x: x["date"]): st.write(f"- {r['date']} · {r['drug']} · {r['note']}")
        else: st.info("일정을 추가해 관리하세요. (별명 기준으로 저장됩니다)")
    else: st.info("별명을 입력하면 스케줄표를 사용할 수 있어요.")
