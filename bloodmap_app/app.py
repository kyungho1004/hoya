
# -*- coding: utf-8 -*-
import io
import streamlit as st

from bloodmap_app.counter_cloud import ensure_sid, bump_visit_once, bump_download
from bloodmap_app.safe_drugs import render_drug_panel

# Optional user modules
try:
    from bloodmap_app.config import APP_TITLE, PAGE_TITLE, MADE_BY, FEVER_GUIDE
except Exception:
    APP_TITLE = "🩸 피수치 가이드 (v3.14 · merged)"
    PAGE_TITLE = "피수치 가이드 by Hoya/GPT"
    MADE_BY = "제작/자문: Hoya/GPT"
    FEVER_GUIDE = "🌡️ 38.0~38.5℃ 해열제/경과, 38.5℃↑ 병원 연락, 39.0℃↑ 즉시 병원."

try:
    from bloodmap_app.interpret import interpret_labs, food_suggestions
    HAS_INTERPRET = True
except Exception:
    HAS_INTERPRET = False

try:
    from bloodmap_app.graphs import render_graphs
except Exception:
    def render_graphs(): st.info("그래프 모듈을 불러오지 못했습니다. pandas 설치/임포트 확인")

try:
    from bloodmap_app.schedule import render_schedule
except Exception:
    def render_schedule(nickname: str): st.info("스케줄 모듈을 불러오지 못했습니다.")

def _load_css():
    try:
        import pathlib
        css = pathlib.Path(__file__).with_name("style.css").read_text(encoding="utf-8")
        st.markdown("<style>"+css+"</style>", unsafe_allow_html=True)
    except Exception:
        pass

def _analytics():
    try:
        ensure_sid(st.session_state)
        data = bump_visit_once(st.session_state)
        a,b = st.columns(2)
        a.metric("👥 방문", int(data.get("visits",0)))
        b.metric("📥 다운로드", int(data.get("downloads",0)))
    except Exception:
        pass

def _report_button(summary="요약 없음", details="상세 없음"):
    md = "# 피수치 가이드 보고서\n\n## 요약\n" + summary + "\n\n## 상세\n" + details
    buf = io.BytesIO(md.encode("utf-8"))
    clicked = st.download_button("📥 보고서(.md) 다운로드", buf, file_name="bloodmap_report.md", mime="text/markdown")
    if clicked:
        try: bump_download(st.session_state)
        except Exception: pass

def main():
    _load_css()
    st.set_page_config(page_title=PAGE_TITLE, page_icon="🩸", layout="centered")
    st.title(APP_TITLE)
    st.caption("✅ 모바일 줄꼬임 방지 · 별명 저장/그래프 · 항암 스케줄표 · 음식 가이드 · 카운터 내장")
    _analytics()

    nickname = st.text_input("별명(저장/그래프/스케줄용, 선택)", key="nickname")
    tabs = st.tabs(["기본 해석", "항암치료", "그래프", "스케줄"])

    with tabs[0]:
        st.subheader("🩺 기본 수치 입력")
        cols = st.columns(3)
        with cols[0]:
            wbc = st.number_input("WBC", min_value=0.0, step=0.1)
            hb  = st.number_input("Hb",  min_value=0.0, step=0.1)
            plt = st.number_input("PLT", min_value=0.0, step=1.0)
        with cols[1]:
            anc = st.number_input("ANC", min_value=0.0, step=10.0)
            crp = st.number_input("CRP", min_value=0.0, step=0.1)
            glu = st.number_input("Glucose", min_value=0.0, step=1.0)
        with cols[2]:
            alb = st.number_input("Albumin", min_value=0.0, step=0.1)
            na  = st.number_input("Na", min_value=0.0, step=0.1)
            k   = st.number_input("K",  min_value=0.0, step=0.1)

        labs = {"WBC(백혈구)": wbc, "Hb(적혈구)": hb, "PLT(혈소판)": plt,
                "ANC(호중구,면역력)": anc, "CRP(염증수치)": crp, "Glucose(혈당)": glu,
                "Albumin(알부민)": alb, "Na(나트륨)": na, "K(포타슘)": k}

        if HAS_INTERPRET:
            lines = interpret_labs(labs, {"diuretic_amt": 0})
            if lines:
                st.success("\n".join(lines))
            else:
                st.info("입력값을 넣으면 자동 해석이 표시됩니다.")
        else:
            st.info("해석 모듈을 불러오지 못했습니다. (interpret.py 점검)")

        _report_button("입력값 요약 생성됨")

    with tabs[1]:
        render_drug_panel()

    with tabs[2]:
        render_graphs()

    with tabs[3]:
        render_schedule(nickname)

if __name__ == "__main__":
    main()
