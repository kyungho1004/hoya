# -*- coding: utf-8 -*-
import uuid
from datetime import datetime
import streamlit as st

from .utils import bump_view_count, get_total_views, ensure_storage_writable
from .drug_data import ANTICANCER, ANTIBIOTICS

def main():
    st.set_page_config(page_title="피수치 가이드 v3.14 · Bloodmap", layout="centered")
    st.markdown("<style>" + (Path(__file__).with_name("style.css").read_text(encoding="utf-8")) + "</style>", unsafe_allow_html=True)

    # === Safe unique session key ===
    if "session_key" not in st.session_state:
        st.session_state.session_key = str(uuid.uuid4())

    # === Top bar ===
    st.title("🩸 피수치 가이드 · v3.14")
    st.caption("制作者: Hoya/GPT · 자문: Hoya/GPT")

    # === View counter (once per session) ===
    writable = ensure_storage_writable()
    total_views = bump_view_count(st.session_state.session_key) if writable else get_total_views()
    with st.container():
        st.markdown(f"**조회수:** {total_views:,}회  \n"
                    f"<span class='small'>세션당 1회 집계 · {datetime.now():%Y-%m-%d %H:%M}</span>",
                    unsafe_allow_html=True)

    # === Sidebar (correctly indented with 'with') ===
    with st.sidebar:
        st.header("빠른 이동")
        st.markdown("- 일반 해석\n- 항암치료\n- 항생제\n- 도움말")

    # === Content blocks ===
    with st.container():
        st.subheader("일반 해석 (샘플)")
        wbc = st.number_input("WBC (백혈구)", min_value=0.0, step=0.1)
        hb = st.number_input("Hb (혈색소)", min_value=0.0, step=0.1)
        plt = st.number_input("혈소판 (PLT)", min_value=0.0, step=1.0)
        if st.button("간단 해석 보기"):
            tips = []
            if wbc and wbc < 1.0: tips.append("감염 주의 (면역저하)")
            if hb and hb < 8.0: tips.append("빈혈 증상 주의")
            if plt and plt < 50: tips.append("출혈 주의")
            if tips:
                st.success(", ".join(tips))
            else:
                st.info("특이 소견 없음 (입력값 기준)")

    with st.container():
        st.subheader("항암치료 (샘플)")
        drug = st.selectbox("항암제 선택", ["선택 없음"] + sorted(ANTICANCER.keys()))
        if drug != "선택 없음":
            info = ANTICANCER.get(drug, {})
            st.write(f"- 별칭: {info.get('alias','-')}")
            st.write(f"- 주의: {info.get('note','-')}")

    with st.container():
        st.subheader("항생제 (샘플)")
        abx = st.selectbox("항생제 선택", ["선택 없음"] + sorted(ANTIBIOTICS.keys()))
        if abx != "선택 없음":
            info = ANTIBIOTICS.get(abx, {})
            st.write(f"- 주의: {info.get('note','-')}")

    st.markdown("---")
    st.markdown("### 📤 보고서(.md) 다운로드는 추후 활성화 예정")

if __name__ == "__main__":
    main()
