import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime

def render_graphs(nickname, order, records):
    if not nickname or not records or nickname not in records:
        return
    show = st.toggle("📈 별명 저장 데이터 추세 그래프 보기", value=True)
    if not show:
        return
    recs = records.get(nickname, [])
    if not recs:
        st.info("기록이 없습니다.")
        return
    # 최근 30개까지만
    recs = recs[-30:]
    # 각 항목별 라인그래프 (WBC/ANC/CRP 우선)
    focus = [x for x in ["WBC","ANC","CRP"] if x in order]
    for key in focus:
        xs=[]; ys=[]
        for r in recs:
            ts = r.get("ts")
            try:
                x = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            except Exception:
                continue
            val = r.get("labs",{}).get(key)
            try:
                y = float(val) if val is not None and val!='' else None
            except Exception:
                y = None
            if y is not None:
                xs.append(x); ys.append(y)
        if xs and ys:
            fig, ax = plt.subplots()
            ax.plot(xs, ys, marker="o")
            ax.set_title(f"{nickname} — {key} 추이")
            ax.set_xlabel("날짜"); ax.set_ylabel(key)
            st.pyplot(fig)
