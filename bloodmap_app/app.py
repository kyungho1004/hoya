
def main():
    from datetime import date, datetime
    import os
    import streamlit as st
    from .config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE,
                         DISCLAIMER, ORDER, FEVER_GUIDE,
                         LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
                         LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP,
                         FONT_PATH_REG)
    from .data.drugs import ANTICANCER, ABX_GUIDE
    from .utils.inputs import num_input_generic, entered, _parse_numeric
    from .utils.interpret import interpret_labs, compare_with_previous, food_suggestions, summarize_meds, abx_summary
    from .utils.reports import build_report, md_to_pdf_bytes_fontlocked
    from .utils.graphs import render_graphs
    from .utils.schedule import render_schedule
    from . import config as CFG

    try:
        import pandas as pd
        HAS_PD=True
    except Exception:
        HAS_PD=False

    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    st.title(APP_TITLE)
    st.markdown(MADE_BY)
    st.markdown(CAFE_LINK_MD)
    st.caption("✅ 모바일 줄꼬임 방지 · PIN(4자리) · 별명 저장/그래프 · 육종 분리 · 특수검사 토글")

    # css
    try:
        with open(os.path.join(os.path.dirname(__file__), "style.css"), "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass

    # 공유/조회수
    st.markdown("### 🔗 공유하기")
    c1, c2, c3 = st.columns([1,1,2])
    with c1:
        st.link_button("📱 카카오톡/메신저", "https://hdzwo5ginueir7hknzzfg4.streamlit.app/")
    with c2:
        st.link_button("📝 카페/블로그", "https://cafe.naver.com/bloodmap")
    with c3:
        st.code("https://hdzwo5ginueir7hknzzfg4.streamlit.app/", language="text")

    os.makedirs("fonts", exist_ok=True)
    from .utils import counter as _bm_counter
    try:
        _bm_counter.bump()
        st.caption(f"👀 조회수(방문): {_bm_counter.count()}")
    except Exception:
        pass

    if "records" not in st.session_state:
        st.session_state.records = {}

    st.divider()
    st.header("1️⃣ 환자/암 정보")

    c1, c2 = st.columns([2,1])
    with c1:
        nickname = st.text_input("별명", placeholder="예: 홍길동")
    with c2:
        pin = st.text_input("PIN(4자리)", max_chars=4, placeholder="예: 1234")
        if pin and (not pin.isdigit() or len(pin)!=4):
            st.error("PIN은 숫자 4자리여야 합니다.")

    test_date = st.date_input("검사 날짜", value=date.today())
    anc_place = st.radio("현재 식사 장소(ANC 가이드용)", ["가정", "병원"], horizontal=True)

    group = st.selectbox("암 그룹 선택", ["미선택/일반", "혈액암", "고형암", "소아암", "희귀암"])
    cancer = None
    if group == "혈액암":
        cancer = st.selectbox("혈액암 종류", ["AML","APL","ALL","CML","CLL"])
    elif group == "고형암":
        cancer = st.selectbox("고형암 종류", [
            "폐암(Lung cancer)","유방암(Breast cancer)","위암(Gastric cancer)",
            "대장암(Cololoractal cancer)","간암(HCC)","췌장암(Pancreatic cancer)",
            "담도암(Cholangiocarcinoma)","자궁내막암(Endometrial cancer)",
            "구강암/후두암","피부암(흑색종)","육종(Sarcoma)","신장암(RCC)",
            "갑상선암","난소암","자궁경부암","전립선암","뇌종양(Glioma)","식도암","방광암"
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
        st.info("암 그룹을 선택하면 해당 진단명 기반 항암제/특수검사가 자동 노출됩니다.")

    st.divider()
    st.header("2️⃣ 기본 혈액 검사 수치 (입력한 값만 해석)")

    vals = {}
    for name in CFG.ORDER:
        decimals = 2 if name==CFG.LBL_CRP else 1
        vals[name] = num_input_generic(name, key=f"v_{name}", decimals=decimals, placeholder="")

    # --- 특수검사 토글 ---
    items_map = {
        "AML": [("PT","PT","sec",1),("aPTT","aPTT","sec",1),("Fibrinogen","Fibrinogen","mg/dL",1),("D-dimer","D-dimer","µg/mL FEU",2)],
        "APL": [("PT","PT","sec",1),("aPTT","aPTT","sec",1),("Fibrinogen","Fibrinogen","mg/dL",1),("D-dimer","D-dimer","µg/mL FEU",2),("DIC Score","DIC Score","pt",0)],
        "육종(Sarcoma)": [("ALP","ALP","U/L",0),("CK","CK","U/L",0)],
        "위암(Gastric cancer)": [("CEA","CEA","ng/mL",1),("CA72-4","CA72-4","U/mL",1),("CA19-9","CA19-9","U/mL",1)],
        "폐암(Lung cancer)": [("CEA","CEA","ng/mL",1),("CYFRA 21-1","CYFRA 21-1","ng/mL",1),("NSE","NSE","ng/mL",1)],
        "방광암": [("NMP22","NMP22","U/mL",1),("UBC","UBC","µg/L",1)],
    }
    special_vals = {}
    if group != "미선택/일반" and cancer:
        st.markdown("### 3️⃣ 특수검사")
        use_special = st.checkbox("특수검사 입력 열기(토글)", value=False,
                                  help="혈액검사 섹션 **아래**에 위치합니다(요구사항 반영).")
        if use_special:
            for key, label, unit, decs in items_map.get(cancer, []):
                ph = f"예: {('0' if decs==0 else '0.'+('0'*decs))}" if decs is not None else ""
                special_vals[key] = num_input_generic(f"{label}" + (f" ({unit})" if unit else ""), key=f"extra_{key}", decimals=decs, placeholder=ph)
        else:
            st.caption("토글을 켜면 진단명별 특수검사 입력칸이 열립니다.")

    # --- 약물 ---
    st.markdown("### 💊 항암제 선택")
    default_drugs = {
        "혈액암": {
            "AML": ["ARA-C","Daunorubicin","Idarubicin","Cyclophosphamide","Etoposide","Fludarabine","Hydroxyurea","MTX","ATRA","G-CSF"],
            "APL": ["ATRA","Idarubicin","Daunorubicin","ARA-C","G-CSF"],
            "ALL": ["Vincristine","Asparaginase","Daunorubicin","Cyclophosphamide","MTX","ARA-C","Topotecan","Etoposide"],
            "CML": ["Imatinib","Dasatinib","Nilotinib","Hydroxyurea"],
            "CLL": ["Fludarabine","Cyclophosphamide","Rituximab"],
        },
        "고형암": {
            "육종(Sarcoma)": ["Doxorubicin","Ifosfamide","Pazopanib"],
        }
    }
    meds = {}
    dlist = []
    if group in default_drugs and cancer in default_drugs[group]:
        dlist = default_drugs[group][cancer]
    sel = st.multiselect("항암제 선택", dlist, default=[])
    for d in sel:
        if d == "ATRA":
            amt = num_input_generic(f"{d} - 캡슐 개수", key=f"med_{d}", as_int=True, placeholder="예: 2")
            if amt: meds[d] = {"tabs": amt}
        elif d == "ARA-C":
            form = st.selectbox(f"{d} - 제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"], key=f"form_{d}")
            dose = num_input_generic(f"{d} - 용량/일", key=f"dose_{d}", decimals=1, placeholder="예: 100")
            if dose: meds[d] = {"form": form, "dose": dose}
        else:
            tabs = num_input_generic(f"{d} - 용량/알약", key=f"tabs_{d}", decimals=1, placeholder="예: 1.5")
            if tabs: meds[d] = {"dose_or_tabs": tabs}

    st.divider()
    run = st.button("🔎 해석하기", use_container_width=True)

    if run:
        st.subheader("📋 해석 결과")
        lines = interpret_labs(vals, {})
        for l in lines: st.write(l)

        if special_vals:
            st.markdown("### 🧬 특수검사(입력값)")
            for k, v in special_vals.items():
                if entered(v):
                    st.write(f"- {k}: {v}")

        if meds:
            st.markdown("### 💊 항암제 부작용·주의")
            for l in summarize_meds(meds): st.write(l)

        st.markdown("### 🌡️ 발열 가이드")
        st.write(CFG.FEVER_GUIDE)

        # 저장: 별명 + PIN을 키로
        if nickname and pin and pin.isdigit() and len(pin)==4:
            key = f"{nickname.strip()}#{pin}"
            rec = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                   "group": group, "cancer": cancer,
                   "labs": {k: v for k,v in vals.items() if entered(v)},
                   "special": {k: v for k,v in special_vals.items() if entered(v)},
                   "meds": meds}
            st.session_state.records.setdefault(key, []).append(rec)
            st.success("저장 완료(별명+PIN). 아래 그래프 영역에서 향후 확장 예정.")
        else:
            st.info("별명과 PIN(4자리)을 입력하면 기록이 저장됩니다.")

        # 보고서
        md = build_report("일반/암", {"group":group,"cancer":cancer,"anc_place":anc_place}, vals, [], special_vals, summarize_meds(meds), [], [])
        st.download_button("📥 보고서(.md) 다운로드", data=md.encode("utf-8"),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                           mime="text/markdown")
        try:
            pdf_bytes = md_to_pdf_bytes_fontlocked(md)
            st.download_button("🖨️ 보고서(.pdf) 다운로드", data=pdf_bytes,
                               file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                               mime="application/pdf")
        except Exception as e:
            st.info("PDF 모듈 오류 시 reportlab 설치 필요")

    render_schedule(nickname)
    render_graphs()

    st.markdown("---")
    st.caption(FOOTER_CAFE)
    st.markdown("> " + DISCLAIMER)
