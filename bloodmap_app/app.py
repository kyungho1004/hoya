# -*- coding: utf-8 -*-
from datetime import datetime, date
import streamlit as st
from .config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE, DISCLAIMER, FEVER_GUIDE,
                     ORDER, LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
                     LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP)
from .drug_data import ANTICANCER, ABX_GUIDE
from .utils import num_input, entered, nickname_key, md_to_pdf_bytes

def main():
    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    st.title(APP_TITLE)
    st.caption(MADE_BY)
    st.markdown(CAFE_LINK_MD)

    # 별명 + PIN (중복 방지)
    c1, c2 = st.columns([2,1])
    with c1:
        nickname = st.text_input("별명(저장/그래프/스케줄용)", placeholder="예: 홍길동")
    with c2:
        pin = st.text_input("PIN 4자리(중복 방지)", max_chars=4, placeholder="예: 1024")
        if pin and (not pin.isdigit() or len(pin) != 4):
            st.warning("PIN은 숫자 4자리로 입력하세요.")
    key = nickname_key(nickname or "", pin or "")

    # 1) 암 그룹
    st.divider()
    st.header("1️⃣ 암 그룹 및 특수검사")
    group = st.selectbox("암 그룹 선택", ["미선택/일반", "혈액암", "고형암", "소아암", "희귀암"])
    cancer = None
    if group == "혈액암":
        cancer = st.selectbox("혈액암 종류", ["AML","APL","ALL","CML","CLL","MM(다발골수종)"])
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

    # 2) 기본 혈액 수치
    st.divider()
    st.header("2️⃣ 기본 혈액 검사 수치")
    vals = {}
    for name in ORDER:
        if name == LBL_CRP:
            vals[name] = num_input(name, key=f"v_{name}", decimals=2, placeholder="예: 0.12")
        elif name in (LBL_WBC, LBL_ANC, LBL_AST, LBL_ALT, LBL_LDH, LBL_BNP, LBL_Glu):
            vals[name] = num_input(name, key=f"v_{name}", decimals=1, placeholder="예: 1200")
        else:
            vals[name] = num_input(name, key=f"v_{name}", decimals=1, placeholder="예: 3.5")

    # 3) 특수검사(암별)
    st.divider()
    st.header("3️⃣ 암별 디테일 수치(특수검사)")
    extra_vals = {}
    items = {
        "AML": [("PT","PT","sec",1),("aPTT","aPTT","sec",1),("Fibrinogen","Fibrinogen","mg/dL",1),("D-dimer","D-dimer","µg/mL FEU",2)],
        "APL": [("PT","PT","sec",1),("aPTT","aPTT","sec",1),("Fibrinogen","Fibrinogen","mg/dL",1),("D-dimer","D-dimer","µg/mL FEU",2),("DIC Score","DIC Score","pt",0)],
        "ALL": [("PT","PT","sec",1),("aPTT","aPTT","sec",1),("CNS Sx","CNS 증상 여부(0/1)","",0)],
        "CML": [("BCR-ABL PCR","BCR-ABL PCR","%IS",2),("Basophil%","기저호염기구(Baso) 비율","%",1)],
        "CLL": [("IgG","면역글로불린 IgG","mg/dL",0),("IgA","면역글로불린 IgA","mg/dL",0),("IgM","면역글로불린 IgM","mg/dL",0)],
        "피부암(흑색종)": [("S100","S100","µg/L",1),("LDH","LDH","U/L",0)],
        "육종(Sarcoma)": [("ALP","ALP","U/L",0),("CK","CK","U/L",0)],
        "간암(HCC)": [("AFP","AFP","ng/mL",1),("PIVKA-II","PIVKA-II(DCP)","mAU/mL",0)],
        "위암(Gastric cancer)": [("CA72-4","CA72-4","U/mL",1),("CEA","CEA","ng/mL",1),("CA19-9","CA19-9","U/mL",1)],
        "대장암(Cololoractal cancer)": [("CEA","CEA","ng/mL",1),("CA19-9","CA19-9","U/mL",1)],
        "유방암(Breast cancer)": [("CA15-3","CA15-3","U/mL",1),("CEA","CEA","ng/mL",1),("HER2","HER2","IHC/FISH",0),("ER/PR","ER/PR","%",0)],
        "폐암(Lung cancer)": [("CEA","CEA","ng/mL",1),("CYFRA 21-1","CYFRA 21-1","ng/mL",1),("NSE","NSE","ng/mL",1)],
        "신장암(RCC)": [("CEA","CEA","ng/mL",1),("LDH","LDH","U/L",0)],
        "식도암": [("SCC Ag","SCC antigen","ng/mL",1),("CEA","CEA","ng/mL",1)],
        "방광암": [("NMP22","NMP22","U/mL",1),("UBC","UBC","µg/L",1)],
    }.get(cancer, [])
    if items:
        for key2, label, unit, decs in items:
            ph = f"예: {('0' if decs==0 else '0.'+('0'*decs))}" if decs is not None else ""
            extra_vals[key2] = num_input(f"{label}" + (f" ({unit})" if unit else ""), key=f"extra_{key2}", decimals=decs, placeholder=ph)
    else:
        st.caption("암종을 선택하면 디테일 수치 입력란이 나타납니다.")

    # 4) 약물 — 추천 + 전체 라인업
    st.divider()
    st.header("4️⃣ 약물 입력 (항암제/항생제)")
    meds = {}
    recommended = {
        "혈액암": ["ARA-C","Daunorubicin","Idarubicin","Cyclophosphamide","Etoposide","Fludarabine","Hydroxyurea","MTX","ATRA","G-CSF","Busulfan","Bortezomib","Lenalidomide"],
        "고형암": ["Cisplatin","Carboplatin","Oxaliplatin","Paclitaxel","Docetaxel","Gemcitabine","Pemetrexed","Bevacizumab","Pembrolizumab","Nivolumab","Doxorubicin","Ifosfamide","Pazopanib","Sorafenib","Lenvatinib"],
        "소아암": ["Cyclophosphamide","Ifosfamide","Doxorubicin","Vincristine","Etoposide","Carboplatin","Cisplatin","Topotecan","Irinotecan"],
        "희귀암": ["Imatinib","Sunitinib","Regorafenib","Mitotane","Temozolomide","Dabrafenib","Trametinib"],
    }.get(group, [])
    st.caption("추천 리스트(암종 기반) + 아래 '전체 라인업에서 추가' 로 원하는 약을 더 선택할 수 있어요.")
    selected_reco = st.multiselect("추천 항암제 선택", [d for d in recommended if d in ANTICANCER], default=[])
    for d in selected_reco:
        alias = ANTICANCER.get(d,{}).get("alias","")
        amt = num_input(f"{d} ({alias}) - 용량/일", key=f"med_{d}", decimals=1, placeholder="예: 100")
        if amt and float(amt)>0:
            meds[d] = {"dose": amt}

    with st.expander("📚 전체 라인업에서 추가 선택(항암제 전부)", expanded=False):
        q = st.text_input("🔎 이름/한글/부작용 검색", key="search_all_drugs")
        all_keys = sorted(list(ANTICANCER.keys()))
        if q:
            ql = q.lower()
            all_keys = [k for k in all_keys if ql in k.lower() or ql in ANTICANCER[k].get("alias","").lower() or any(ql in ae.lower() for ae in ANTICANCER[k].get("aes",[]))]
        picked = st.multiselect("항암제(전체 DB)", all_keys, default=[])
        for d in picked:
            if d in meds: 
                continue
            alias = ANTICANCER.get(d,{}).get("alias","")
            amt = num_input(f"{d} ({alias}) - 용량/일", key=f"med_all_{d}", decimals=1, placeholder="예: 100")
            if amt and float(amt)>0:
                meds[d] = {"dose": amt}

    st.subheader("🧪 항생제")
    abx_map = {}
    abx_classes = sorted(list(ABX_GUIDE.keys()))
    abx_sel = st.multiselect("항생제 계열 선택", abx_classes, default=[])
    for abx in abx_sel:
        abx_map[abx] = num_input(f"{abx} - 복용/주입량", key=f"abx_{abx}", decimals=1, placeholder="예: 1")

    # 5) 해석 및 보고서
    st.divider()
    if st.button("🔎 해석하기", use_container_width=True):
        lines = []
        anc = vals.get(LBL_ANC)
        if entered(anc) and anc < 500:
            lines.append("- ANC < 500: 감염 고위험 — 생야채 금지, 충분 가열, 멸균식품 권장, 남은 음식 2시간 이후 섭취 금지")
        hb = vals.get(LBL_Hb)
        if entered(hb) and hb < 8.0:
            lines.append("- 빈혈 가능: 어지럼/호흡곤란 체크, 필요 시 수혈 상의")
        plt = vals.get(LBL_PLT)
        if entered(plt) and plt < 50000:
            lines.append("- 혈소판 저하: 출혈 주의, 부드러운 칫솔/전기면도기 권장")
        if not lines:
            lines.append("- 입력값이 부족하거나 특이사항이 없습니다.")
        for l in lines: st.write(l)

        report_lines = ["# 보고서", "## 입력 수치"]
        for k, v in vals.items():
            if entered(v): report_lines.append(f"- {k}: {v}")
        if extra_vals:
            report_lines.append("\n## 디테일 수치")
            for k, v in extra_vals.items():
                if entered(v): report_lines.append(f"- {k}: {v}")
        if meds:
            report_lines.append("\n## 항암제")
            for k, v in meds.items():
                alias = ANTICANCER.get(k,{}).get("alias","")
                report_lines.append(f"- {k}({alias}): {v}")
        if abx_map:
            report_lines.append("\n## 항생제")
            for k, v in abx_map.items():
                report_lines.append(f"- {k}: 용량 {v}")
        report_lines.append("\n## 발열 가이드")
        report_lines.append(FEVER_GUIDE)
        md_text = "\n".join(report_lines)
        st.download_button("📄 보고서(.md)", data=md_text.encode("utf-8"), file_name="bloodmap_report.md", mime="text/markdown")

        try:
            pdf_bytes = md_to_pdf_bytes(md_text)
            st.download_button("🖨️ 보고서(.pdf)", data=pdf_bytes, file_name="bloodmap_report.pdf", mime="application/pdf")
        except Exception:
            st.info("PDF 모듈(reportlab) 설치 필요")
