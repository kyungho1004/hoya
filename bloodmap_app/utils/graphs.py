import streamlit as st

def render_graphs():
    st.markdown("---")
    st.subheader("📈 별명별 추이 그래프 (WBC, Hb, PLT, CRP, ANC)")
    try:
        import pandas as pd  # noqa
        HAS_PD = True
    except Exception:
        HAS_PD = False

    if not HAS_PD:
        st.info("그래프는 pandas 설치 시 활성화됩니다. (pip install pandas)")
        return

    if "records" in st.session_state and st.session_state.records:
        sel = st.selectbox("별명 선택", sorted(st.session_state.records.keys()))
        rows = st.session_state.records.get(sel, [])
        if rows:
            data = [ {"ts": r["ts"], **{k: r["labs"].get(k) for k in ["WBC(백혈구)", "Hb(적혈구)", "PLT(혈소판)", "CRP(염증수치)", "ANC(호중구,면역력)"]}} for r in rows ]
            import pandas as pd  # local import
            df = pd.DataFrame(data).set_index("ts")
            st.line_chart(df.dropna(how="all"))
        else:
            st.info("선택한 별명의 저장 기록이 없습니다.")
    else:
        st.info("아직 저장된 기록이 없습니다.")
