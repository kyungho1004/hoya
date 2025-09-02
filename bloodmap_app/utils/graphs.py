
import streamlit as st

def render_graphs():
    st.header("📈 추이 그래프")
    recs = (st.session_state.get("records") or {})
    if not recs:
        st.info("저장된 기록이 없어요. 별명 입력 후 해석하면 자동 저장됩니다.")
        return
    nickname = st.text_input("그래프 볼 별명", key="graph_nick", placeholder="예: 홍길동")
    if not nickname or nickname not in recs:
        st.caption("별명에 저장된 기록이 없거나 미입력.")
        return
    # Build simple time series for 주요 항목
    keys = ["WBC","Hb","PLT","CRP","ANC"]
    series = {k: [] for k in keys}
    for r in recs[nickname]:
        labs = r.get("labs") or {}
        for k in keys:
            v = labs.get(k)
            series[k].append(float(v) if v is not None else None)
    for k in keys:
        vals = [v for v in series[k] if v is not None]
        if vals:
            st.line_chart(vals, height=160, use_container_width=True)
            st.caption(f"{k} 추이(최근 {len(vals)}회)")
