
# -*- coding: utf-8 -*-
import io
import json
import streamlit as st
from .utils import load_analytics, bump_visit, bump_run, mk_report_md
from .drug_data import ANTICANCER

def _load_css() -> None:
    try:
        import pathlib
        css = pathlib.Path(__file__).with_name("style.css").read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception:
        pass

def _show_counter():
    # Session guard
    if "counted" not in st.session_state:
        st.session_state["counted"] = True
        total = bump_visit("session")
    data = load_analytics()
    left, right = st.columns(2)
    left.metric("👥 총 방문(세션)", data.get("visits", 0))
    right.metric("📥 보고서 다운로드", data.get("runs", 0))

def _report_button(summary_text: str, detail_text: str):
    # Create downloadable markdown
    md = mk_report_md(summary_text, detail_text)
    b = io.BytesIO(md.encode("utf-8"))
    if st.download_button("📥 보고서(.md) 다운로드", b, file_name="bloodmap_report.md", mime="text/markdown"):
        bump_run()

def _drug_section():
    st.subheader("💊 항암치료 · 약물 요약")
    search = st.text_input("약물 검색(영문/한글 별칭 모두 가능)", value="")
    matches = []
    for name, meta in ANTICANCER.items():
        alias = meta.get("alias", "").lower()
        if search.strip() == "" or search.lower() in name.lower() or search.lower() in alias:
            matches.append((name, meta))
    if not matches:
        st.info("검색 결과가 없습니다.")
        return
    for name, meta in matches:
        with st.expander(f"• {name} ({meta.get('alias','')})", expanded=False):
            st.write(f"분류: {meta.get('class','-')}")
            for n in meta.get("notes", []):
                st.markdown(f"- {n}")

def _lab_section():
    st.subheader("🩺 기본 수치 입력 (입력한 수치만 결과 표시)")
    # Minimal placeholder inputs for demonstration
    col1, col2 = st.columns(2)
    with col1:
        wbc = st.number_input("WBC", min_value=0.0, step=0.1, value=0.0, help="백혈구")
        hb = st.number_input("Hb", min_value=0.0, step=0.1, value=0.0, help="혈색소")
        plt = st.number_input("혈소판(PLT)", min_value=0.0, step=1.0, value=0.0)
    with col2:
        anc = st.number_input("ANC(호중구)", min_value=0.0, step=10.0, value=0.0)
        crp = st.number_input("CRP", min_value=0.0, step=0.1, value=0.0)
        glu = st.number_input("Glucose", min_value=0.0, step=1.0, value=0.0)

    shown = []
    if wbc: shown.append(f"WBC: {wbc}")
    if hb: shown.append(f"Hb: {hb}")
    if plt: shown.append(f"혈소판: {plt}")
    if anc: shown.append(f"ANC: {anc}")
    if crp: shown.append(f"CRP: {crp}")
    if glu: shown.append(f"Glucose: {glu}")

    if shown:
        st.success(" · ".join(shown))
    else:
        st.info("입력한 수치가 없습니다. 값을 입력하면 요약이 나타납니다.")

    # Food guide stub (월요일 업데이트 항목 반영 형태)
    st.markdown("#### 🍽️ 추천 음식 (데모)")
    recs = []
    if hb and hb < 10:
        recs = ["소고기", "시금치", "두부", "달걀 노른자", "렌틸콩"]
    elif anc and anc < 500:
        recs = ["익힌 음식 위주", "전자레인지 30초 이상", "멸균/살균 식품", "생채소 금지", "껍질 과일은 상담 후"]
    if recs:
        st.write(", ".join(recs))

    _report_button("입력 요약: " + (" · ".join(shown) if shown else "없음"),
                   "추천 음식: " + (", ".join(recs) if recs else "조건 해당 없음"))

def main():
    _load_css()
    st.title("🩸 피수치 가이드 (v3.14-fixed)")
    st.caption("모바일 최적화 · 입력한 수치만 표시 · 보고서 버튼 · 조회수 카운터")

    _show_counter()

    tabs = st.tabs(["기본 해석", "항암치료"])
    with tabs[0]:
        _lab_section()
    with tabs[1]:
        _drug_section()

    st.markdown('<div class="footer">제작/자문: Hoya/GPT · v3.14-fixed</div>', unsafe_allow_html=True)
