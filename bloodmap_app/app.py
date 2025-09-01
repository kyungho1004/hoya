
# -*- coding: utf-8 -*-
from datetime import datetime, date
import os, json, time
try:
    import streamlit as st
except Exception:
    class _Dummy:
        def __getattr__(self, k):
            def _f(*a, **kw): return None
            return _f
    st = _Dummy()

from config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE,
                    DISCLAIMER, ORDER, FEVER_GUIDE,
                    LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
                    LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP,
                    FONT_PATH_REG)
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

USAGE_FILE = "usage_log.json"

def _load_usage():
    if os.path.exists(USAGE_FILE):
        try:
            with open(USAGE_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            if not isinstance(d, dict):
                raise ValueError("bad json")
            return d
        except Exception:
            pass
    return {"views":0, "real_users":0, "avg_time_sec":0.0, "downloads":0}

def _save_usage(d):
    try:
        with open(USAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _update_avg(old_avg, old_n, add_seconds):
    try:
        return (old_avg*old_n + float(add_seconds)) / max(1, (old_n+1))
    except Exception:
        return old_avg

def main():
    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    st.title(APP_TITLE)
    st.markdown(MADE_BY)
    st.markdown(CAFE_LINK_MD)
    st.caption("✅ 모바일 줄꼬임 방지 · 별명 저장/그래프 · 암별/소아 패널 · PDF 한글 폰트 고정 · 수치 비교 · 스케줄 · 조회수/사용 로그")
    os.makedirs("fonts", exist_ok=True)

    # ===== Usage logging =====
    usage = _load_usage()

    # session start time
    if "session_start" not in st.session_state:
        st.session_state.session_start = time.time()

    # views
    if "view_logged" not in st.session_state:
        usage["views"] = usage.get("views",0) + 1
        _save_usage(usage)
        st.session_state.view_logged = True

    # show current stats
    st.sidebar.info(f"👀 조회수: {usage.get('views',0)} · ✅ 실사용자: {usage.get('real_users',0)} · ⏱ 평균사용(초): {int(usage.get('avg_time_sec',0))} · ⬇️ 다운로드: {usage.get('downloads',0)}")

    if "records" not in st.session_state:
        st.session_state.records = {}
    if "schedules" not in st.session_state:
        st.session_state.schedules = {}

    # ===== patient / mode =====
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

    # ===== drugs & extras =====
    meds = {}; extras = {}
    if mode == "일반/암" and group and group != "미선택/일반" and cancer:
        st.markdown("### 💊 항암제 선택 및 입력")
        heme_by_cancer = {"AML":["ARA-C","Daunorubicin","Idarubicin","Cyclophosphamide","Etoposide","Fludarabine","Hydroxyurea","MTX","ATRA","G-CSF"],
                          "APL":["ATRA","Idarubicin","Daunorubicin","ARA-C","G-CSF"],
                          "ALL":["Vincristine","Asparaginase","Daunorubicin","Cyclophosphamide","MTX","ARA-C","Topotecan","Etoposide"],
                          "CML":["Imatinib","Dasatinib","Nilotinib","Hydroxyurea"],
                          "CLL":["Fludarabine","Cyclophosphamide","Rituximab"]}
        solid_by_cancer = {"폐암(Lung cancer)":["Cisplatin","Carboplatin","Paclitaxel","Docetaxel","Gemcitabine","Pemetrexed","Gefitinib","Erlotinib","Osimertinib","Alectinib","Bevacizumab","Pembrolizumab","Nivolumab"],
                           "유방암(Breast cancer)":["Doxorubicin","Cyclophosphamide","Paclitaxel","Docetaxel","Trastuzumab","Bevacizumab"]}
        rare_by_cancer = {"담낭암(Gallbladder cancer)":["Gemcitabine","Cisplatin"],
                          "망막모세포종(Retinoblastoma)":["Vincristine","Etoposide","Carboplatin"]}
        default_drugs_by_group = {"혈액암": heme_by_cancer.get(cancer, []),
                                  "고형암": solid_by_cancer.get(cancer, []),
                                  "소아암": ["Cyclophosphamide","Ifosfamide","Doxorubicin","Vincristine","Etoposide","Carboplatin","Cisplatin","Topotecan","Irinotecan"],
                                  "희귀암": rare_by_cancer.get(cancer, [])}
        drug_list = list(dict.fromkeys(default_drugs_by_group.get(group, [])))
    else:
        drug_list = []

    drug_search = st.text_input("🔍 항암제 검색", key="drug_search")
    drug_choices = [d for d in drug_list if not drug_search or drug_search.lower() in d.lower() or drug_search.lower() in ANTICANCER.get(d,{}).get("alias","").lower()]
    selected_drugs = st.multiselect("항암제 선택", drug_choices, default=[])
    for d in selected_drugs:
        alias = ANTICANCER.get(d,{}).get("alias","")
        if d == "ATRA":
            amt = num_input_generic(f"{d} ({alias}) - 캡슐 개수", key=f"med_{d}", as_int=True, placeholder="예: 2")
        elif d == "ARA-C":
            ara_form = st.selectbox(f"{d} ({alias}) - 제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"], key=f"ara_form_{d}")
            amt = num_input_generic(f"{d} ({alias}) - 용량/일", key=f"med_{d}", decimals=1, placeholder="예: 100")
            if amt and float(amt)>0: meds[d]={"form":ara_form,"dose":amt}
            continue
        else:
            amt = num_input_generic(f"{d} ({alias}) - 용량/알약", key=f"med_{d}", decimals=1, placeholder="예: 1.5")
        if amt and float(amt)>0: meds[d]={"dose_or_tabs":amt}

    st.markdown("### 🧪 항생제 선택 및 입력")
    extras["abx"] = {}
    abx_search = st.text_input("🔍 항생제 검색", key="abx_search")
    abx_choices = [a for a in ABX_GUIDE.keys() if not abx_search or abx_search.lower() in a.lower() or any(abx_search.lower() in tip.lower() for tip in ABX_GUIDE[a])]
    selected_abx = st.multiselect("항생제 계열 선택", abx_choices, default=[])
    for abx in selected_abx:
        extras["abx"][abx] = num_input_generic(f"{abx} - 복용/주입량", key=f"abx_{abx}", decimals=1, placeholder="예: 1")

    st.markdown("### 💧 동반 약물/상태")
    extras["diuretic_amt"] = num_input_generic("이뇨제(복용량/회/일)", key="diuretic_amt", decimals=1, placeholder="예: 1")

    # ===== basic inputs =====
    st.divider()
    st.header("2️⃣ 기본 입력")
    vals = {}
    def _input_one(name, pref="v_"):
        if name == "CRP(염증수치)": return num_input_generic(f"{name}", key=f"{pref}{name}", decimals=2, placeholder="예: 0.12")
        elif name in (LBL_WBC, LBL_ANC, LBL_AST, LBL_ALT, LBL_LDH, LBL_BNP, LBL_Glu):
            return num_input_generic(f"{name}", key=f"{pref}{name}", decimals=1, placeholder="예: 1200")
        else:
            return num_input_generic(f"{name}", key=f"{pref}{name}", decimals=1, placeholder="예: 3.5")
    if st.checkbox("⚙️ PC용 표 모드(가로형)"):
        left, right = st.columns(2); half=(len(ORDER)+1)//2
        with left:
            for name in ORDER[:half]: vals[name]=_input_one(name, "l_")
        with right:
            for name in ORDER[half:]: vals[name]=_input_one(name, "r_")
    else:
        for name in ORDER: vals[name]=_input_one(name, "v_")

    # ===== schedule =====
    render_schedule(nickname)

    # ===== run =====
    st.divider()
    run = st.button("🔎 해석하기", use_container_width=True)
    if run:
        # mark real user & session duration
        usage = _load_usage()
        usage["real_users"] = usage.get("real_users",0) + 1
        elapsed = max(0, time.time() - st.session_state.get("session_start", time.time()))
        usage["avg_time_sec"] = _update_avg(usage.get("avg_time_sec",0.0), max(1, usage.get("real_users",1)-1), elapsed)
        _save_usage(usage)

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
            shown = [ (k, v) for k, v in (locals().get('extra_vals') or {}).items() if entered(v) ]
            if shown:
                st.markdown("### 🧬 암별 디테일 수치")
                for k, v in shown: st.write(f"- {k}: {v}")
            for f in food_suggestions(vals, anc_place): st.markdown(f)
        elif mode == "소아(일상/호흡기)":
            st.info("위 위험도 배너를 참고하세요.")
        else:
            st.success("선택한 감염질환 요약을 보고서에 포함했습니다.")

        if meds:
            st.markdown("### 💊 항암제 부작용·상호작용 요약")
            for line in summarize_meds(meds): st.write(line)

        if extras.get("abx"):
            abx_lines = abx_summary(extras["abx"])
            if abx_lines:
                st.markdown("### 🧪 항생제 주의 요약")
                for l in abx_lines: st.write(l)

        st.markdown("### 🌡️ 발열 가이드")
        st.write(FEVER_GUIDE)

        # build report
        meta = {"group": group, "cancer": cancer, "infect_sel": infect_sel, "anc_place": anc_place, "ped_topic": None}
        report_md = build_report(mode, meta, vals, [], {}, summarize_meds(meds) if meds else [], food_suggestions(vals, anc_place) if (mode=="일반/암") else [], abx_summary(extras.get("abx", {})) if extras.get("abx") else [])

        # downloads with click detection → usage["downloads"]++
        clicked_any = False
        if st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"), file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md", mime="text/markdown"):
            clicked_any = True
        try:
            pdf_bytes = md_to_pdf_bytes_fontlocked(report_md)
            if st.download_button("🖨️ 보고서(.pdf) 다운로드", data=pdf_bytes, file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", mime="application/pdf"):
                clicked_any = True
        except Exception as e:
            st.info("PDF 모듈이 없거나 폰트 미설치로 PDF 생성이 비활성화되었습니다.")

        if clicked_any:
            usage = _load_usage()
            usage["downloads"] = usage.get("downloads",0) + 1
            _save_usage(usage)

        # persist record
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
