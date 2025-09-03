# -*- coding: utf-8 -*-
import streamlit as st

def _series_from_records(recs, key):
    xs, ys = [], []
    for r in recs:
        v = r.get("labs", {}).get(key)
        if v is None: continue
        xs.append(r.get("ts"))
        ys.append(v)
    return xs, ys

def render_graphs():
    if "records" not in st.session_state or not st.session_state.records:
        return
    st.markdown("## 📈 추이 그래프")
    nickname_keys = list(st.session_state.records.keys())
    sel = st.selectbox("별명 선택(그래프)", nickname_keys)
    recs = st.session_state.records.get(sel, [])
    if not recs:
        st.info("기록이 없습니다.")
        return
    import pandas as pd
    cols = ["WBC(백혈구, /µL)","Hb(혈색소, g/dL)","혈소판(PLT, /µL)","CRP(mg/dL)","ANC(호중구, /µL)"]
    data = {}
    for col in cols:
        xs, ys = _series_from_records(recs, col)
        data[col] = ys
    df = pd.DataFrame(data)
    st.line_chart(df)
