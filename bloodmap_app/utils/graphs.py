
import streamlit as st
from ..config import (LBL_WBC, LBL_Hb, LBL_PLT, LBL_CRP, LBL_ANC)

def render_graphs():
    st.divider()
    st.header("📈 추이 그래프 (별명별)")
    nickname = st.text_input("그래프 볼 별명", key="graph_nick", placeholder="예: 홍길동")
    if not nickname:
        st.info("별명을 입력하면 저장된 기록으로 그래프를 볼 수 있어요.")
        return
    records = (st.session_state.get("records") or {}).get(nickname, [])
    if not records:
        st.info("해당 별명으로 저장된 기록이 없습니다.")
        return
    # 간단 라인 그래프
    import pandas as pd
    rows = []
    for rec in records:
        dt = rec.get("ts")
        labs = rec.get("labs", {})
        rows.append({
            "ts": dt,
            LBL_WBC: labs.get(LBL_WBC),
            LBL_Hb: labs.get(LBL_Hb),
            LBL_PLT: labs.get(LBL_PLT),
            LBL_CRP: labs.get(LBL_CRP),
            LBL_ANC: labs.get(LBL_ANC),
        })
    df = pd.DataFrame(rows).set_index("ts")
    st.line_chart(df[[LBL_WBC, LBL_ANC]].dropna(how="all"))
    st.line_chart(df[[LBL_Hb, LBL_PLT, LBL_CRP]].dropna(how="all"))
