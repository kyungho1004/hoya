\
import streamlit as st

def render_graphs():
    st.header("📈 추이 그래프")
    st.caption("별명별 저장 데이터를 기반으로 차트를 표시합니다. (간단 버전)")
    if "records" not in st.session_state or not st.session_state.records:
        st.info("저장된 기록이 없습니다.")
        return
    nick = st.text_input("그래프 볼 별명", key="graph_nick", placeholder="예: 홍길동")
    if not nick or nick not in st.session_state.records:
        st.info("별명 입력 후 엔터(또는 저장된 기록이 있는 별명인지 확인).")
        return
    # 간단 표시
    st.write(f"총 기록: {len(st.session_state.records[nick])}건")
