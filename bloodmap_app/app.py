
# -*- coding: utf-8 -*-
from datetime import datetime, date
import os, json, time
import streamlit as st

# -------------------- Logging (CSV + counters JSON) --------------------
LOG_DIR  = "logs"
LOG_FILE = os.path.join(LOG_DIR, "usage_log.csv")
COUNTER_FILE = os.path.join(LOG_DIR, "usage_counters.json")

os.makedirs(LOG_DIR, exist_ok=True)
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("ts,event,meta\n")
if not os.path.exists(COUNTER_FILE):
    with open(COUNTER_FILE, "w", encoding="utf-8") as f:
        f.write('{"views":0,"real_users":0,"downloads":0,"avg_time_sec":0}')

def _read_counters():
    try:
        with open(COUNTER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"views":0,"real_users":0,"downloads":0,"avg_time_sec":0}

def _write_counters(d):
    try:
        with open(COUNTER_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
    except Exception:
        pass

def write_log(event: str, meta: str = ""):
    """Append a single event row to logs/usage_log.csv"""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()},{event},{meta.replace(',', ' ')}\n")
    except Exception:
        pass

def incr_counter(name: str, add: float = 1.0):
    d = _read_counters()
    if name == "avg_time_sec":
        # caller must pass actual seconds via add
        n = max(1, d.get("real_users", 1))
        d["avg_time_sec"] = (d.get("avg_time_sec", 0.0) * (n-1) + float(add)) / n
    else:
        d[name] = float(d.get(name, 0)) + add
    _write_counters(d)
    return d

# -------------------- App imports --------------------
from config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE,
                    DISCLAIMER, ORDER, FEVER_GUIDE,
                    LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
                    LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP)
from bloodmap_app.data.drugs import ANTICANCER, ABX_GUIDE
from bloodmap_app.data.foods import FOODS
from bloodmap_app.data.ped import PED_TOPICS, PED_INPUTS_INFO, PED_INFECT
from bloodmap_app.utils.inputs import num_input_generic, entered, _parse_numeric
from bloodmap_app.utils.interpret import interpret_labs, compare_with_previous, food_suggestions, summarize_meds, abx_summary
from bloodmap_app.utils.reports import build_report, md_to_pdf_bytes_fontlocked
from bloodmap_app.utils.graphs import render_graphs
from bloodmap_app.utils.schedule import render_schedule

try:
    import pandas as pd
    HAS_PD = True
except Exception:
    HAS_PD = False

# -------------------- Main --------------------
def main():
    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    st.title(APP_TITLE)
    st.markdown(MADE_BY)
    st.markdown(CAFE_LINK_MD)
    st.caption("✅ 로그 자동 생성(logs/usage_log.csv) · 조회/실사용/다운로드 카운트 · 모바일 줄꼬임 방지")

    # First-time session init
    if "session_start" not in st.session_state:
        st.session_state.session_start = time.time()

    # Log a view (once per session)
    if "view_logged" not in st.session_state:
        write_log("view", "")
        incr_counter("views", 1)
        st.session_state.view_logged = True

    counters = _read_counters()
    st.sidebar.info(f"👀 조회수: {int(counters.get('views',0))} · ✅ 실사용자: {int(counters.get('real_users',0))} · ⏱ 평균(초): {int(counters.get('avg_time_sec',0))} · ⬇️ 다운로드: {int(counters.get('downloads',0))}")

    # States
    if "records" not in st.session_state:
        st.session_state.records = {}
    if "schedules" not in st.session_state:
        st.session_state.schedules = {}

    # Patient / mode
    st.divider()
    st.header("1️⃣ 환자/암·소아 정보")

    c1, c2 = st.columns(2)
    with c1:
        nickname = st.text_input("별명(저장/그래프/스케줄용)", placeholder="예: 홍길동")
    with c2:
        test_date = st.date_input("검사 날짜", value=date.today())

    anc_place = st.radio("현재 식사 장소(ANC 가이드용)", ["가정", "병원"], horizontal=True)
    mode = st.selectbox("모드 선택", ["일반/암", "소아(일상/호흡기)", "소아(감염질환)"])

    group = cancer = infect_sel = ped_topic = None
    if mode == "일반/암":
        group = st.selectbox("암 그룹 선택", ["미선택/일반", "혈액암", "고형암", "소아암", "희귀암"])
        if group == "혈액암":
            cancer = st.selectbox("혈액암 종류", ["AML","APL","ALL","CML","CLL"])
        elif group == "고형암":
            cancer = st.selectbox("고형암 종류", [
                "폐암(Lung cancer)","유방암(Breast cancer)","위암(Gastric cancer)","대장암(Cololoractal cancer)",
                "간암(HCC)","췌장암(Pancreatic cancer)","담도암(Cholangiocarcinoma)","자궁내막암(Endometrial cancer)",
                "구강암/후두암","피부암(흑색종)","육종(Sarcoma)","신장암(RCC)","갑상선암","난소암","자궁경부암",
                "전립선암","뇌종양(Glioma)","식도암","방광암"
            ])
        elif group == "소아암":
            cancer = st.selectbox("소아암 종류", ["Neuroblastoma","Wilms tumor"])
        elif group == "희귀암":
            cancer = st.selectbox("희귀암 종류", [
                "담낭암(Gallbladder cancer)","부신암(Adrenal cancer)","망막모세포종(Retinoblastoma)",
                "흉선종/흉선암(Thymoma/Thymic carcinoma)","신경내분비종양(NET)",
                "간모세포종(Hepatoblastoma)","비인두암(NPC)","GIST"
            ])
        else:
            st.info("암 그룹을 선택하면 해당 암종에 맞는 항암제 목록과 추가 수치가 열립니다.")
    elif mode == "소아(일상/호흡기)":
        st.markdown("### 🧒 소아 일상 주제 선택")
        st.caption(PED_INPUTS_INFO)
        ped_topic = st.selectbox("소아 주제", PED_TOPICS)
    else:
        st.markdown("### 🧫 소아·영유아 감염질환")
        infect_sel = st.selectbox("질환 선택", list(PED_INFECT.keys()))

    table_mode = st.checkbox("⚙️ PC용 표 모드(가로형)")

    # Drugs / ABX (요약은 utils.interpret의 abx_summary 사용)
    meds = {}; extras = {}
    st.markdown("### 🧪 항생제 선택 및 입력")
    extras["abx"] = {}
    abx_search = st.text_input("🔍 항생제 검색", key="abx_search")
    abx_choices = [a for a in ABX_GUIDE.keys()] if isinstance(ABX_GUIDE, dict) else [str(a) for a in ABX_GUIDE]
    abx_choices = [a for a in abx_choices if not abx_search or abx_search.lower() in a.lower()]
    selected_abx = st.multiselect("항생제 계열 선택", abx_choices, default=[])
    for abx in selected_abx:
        extras["abx"][abx] = num_input_generic(f"{abx} - 복용/주입량", key=f"abx_{abx}", decimals=1, placeholder="예: 1")

    st.markdown("### 💧 동반 약물/상태")
    extras["diuretic_amt"] = num_input_generic("이뇨제(복용량/회/일)", key="diuretic_amt", decimals=1, placeholder="예: 1")

    # Basic inputs
    st.divider()
    st.header("2️⃣ 기본 입력")
    vals = {}
    def _input_one(name, pref="v_"):
        if name == "CRP(염증수치)": return num_input_generic(f"{name}", key=f"{pref}{name}", decimals=2, placeholder="예: 0.12")
        elif name in (LBL_WBC, LBL_ANC, LBL_AST, LBL_ALT, LBL_LDH, LBL_BNP, LBL_Glu):
            return num_input_generic(f"{name}", key=f"{pref}{name}", decimals=1, placeholder="예: 1200")
        else:
            return num_input_generic(f"{name}", key=f"{pref}{name}", decimals=1, placeholder="예: 3.5")
    if table_mode:
        left, right = st.columns(2); half=(len(ORDER)+1)//2
        with left:
            for name in ORDER[:half]: vals[name]=_input_one(name, "l_")
        with right:
            for name in ORDER[half:]: vals[name]=_input_one(name, "r_")
    else:
        for name in ORDER: vals[name]=_input_one(name, "v_")

    # Schedule
    render_schedule(nickname)

    # Run
    st.divider()
    run = st.button("🔎 해석하기", use_container_width=True)
    if run:
        write_log("interpret", f"nick={nickname or ''}|mode={mode}")
        d = _read_counters()
        d["real_users"] = int(d.get("real_users",0)) + 1
        # session duration so far
        elapsed = max(0, time.time() - st.session_state.get("session_start", time.time()))
        n = max(1, d["real_users"])
        d["avg_time_sec"] = (d.get("avg_time_sec",0.0) * (n-1) + float(elapsed)) / n
        _write_counters(d)

        st.subheader("📋 해석 결과")
        if mode == "일반/암":
            for line in interpret_labs(vals, extras): st.write(line)
            if nickname and "records" in st.session_state and st.session_state.records.get(nickname):
                st.markdown("### 🔍 수치 변화 비교 (이전 기록 대비)")
                cmp_lines = compare_with_previous(nickname, {k: vals.get(k) for k in ORDER if entered(vals.get(k))})
                if cmp_lines: 
                    for l in cmp_lines: st.write(l)
                else:
                    st.info("비교할 이전 기록이 없거나 값이 부족합니다.")
            for f in food_suggestions(vals, anc_place): st.markdown(f)
        elif mode == "소아(일상/호흡기)":
            st.info("위 위험도 배너를 참고하세요.")
        else:
            st.success("선택한 감염질환 요약을 보고서에 포함했습니다.")

        if extras.get("abx"):
            abx_lines = abx_summary(extras["abx"])
            if abx_lines:
                st.markdown("### 🧪 항생제 주의 요약")
                for l in abx_lines: st.write(l)

        st.markdown("### 🌡️ 발열 가이드")
        st.write(FEVER_GUIDE)

        # report
        meta = {"group": group, "cancer": cancer, "infect_sel": infect_sel, "anc_place": anc_place, "ped_topic": None}
        report_md = build_report(mode, meta, vals, [], {}, summarize_meds(meds) if meds else [], food_suggestions(vals, anc_place) if (mode=="일반/암") else [], abx_summary(extras.get("abx", {})) if extras.get("abx") else [])

        # downloads
        clicked_md = st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"),
                                        file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                        mime="text/markdown")
        if clicked_md:
            write_log("download_md", nickname or "")
            incr_counter("downloads", 1)

        try:
            pdf_bytes = md_to_pdf_bytes_fontlocked(report_md)
            clicked_pdf = st.download_button("🖨️ 보고서(.pdf) 다운로드", data=pdf_bytes,
                                             file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                             mime="application/pdf")
            if clicked_pdf:
                write_log("download_pdf", nickname or "")
                incr_counter("downloads", 1)
        except Exception:
            st.info("PDF 모듈/폰트 미설치 → PDF 비활성화")

        # persist record for graphs
        if nickname and nickname.strip():
            rec = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                   "mode": mode, "group": group, "cancer": cancer, "infect": infect_sel,
                   "labs": {k: vals.get(k) for k in ORDER if entered(vals.get(k))},
                   "meds": meds, "extras": extras}
            st.session_state.records.setdefault(nickname, []).append(rec)
            st.success("저장되었습니다. 아래 그래프에서 추이를 확인하세요.")
        else:
            st.info("별명을 입력하면 추이 그래프를 사용할 수 있어요.")

    # graphs
    render_graphs()

    st.markdown("---")
    st.caption(FOOTER_CAFE)
    st.markdown("> " + DISCLAIMER)
