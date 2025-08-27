# -*- coding: utf-8 -*-
"""
피수치 자동 해석기 - v2.9 통합본 + 즉시반영 세트 (클린 빌드)
- 레짐 프리셋(혈액암 + 고형암 자동 체크)
- 약물 상호작용 배지(QT↑/신독성↑/출혈 위험/골수억제)
- 사용자 임계값 경고 배너 + 상단 3줄 요약
- 캡슐/정 약물은 '개수(정수)' 입력 (ATRA/6-MP/Hydroxyurea/Capecitabine)
- 모바일 줄꼬임 방지, 보고서 파일명 'bloodmap_별명_YYYYMMDD'
"""
from io import BytesIO
from datetime import datetime, date
import streamlit as st

# Optional pandas (for charts)
try:
    import pandas as pd
    HAS_PD = True
except Exception:
    HAS_PD = False

# Optional PDF (reportlab)
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    HAS_PDF = True
except Exception:
    HAS_PDF = False

# -------------------- CONFIG --------------------
st.set_page_config(page_title="피수치 자동 해석기 by Hoya", layout="centered")
st.title("🩸 피수치 자동 해석기")
st.markdown("👤 **제작자: Hoya / 자문: GPT**")

# 페이지 조회수(간단 카운터)
st.session_state.setdefault("page_views", 0)
st.session_state["page_views"] += 1

# 별명별 기록 저장소
st.session_state.setdefault("records", {})  # {nickname: [ {ts, category, cancer, labs, meds, extras, preset} ]}

# 순서 고정(20)
ORDER = [
    "WBC", "Hb", "PLT", "ANC",
    "Ca", "P", "Na", "K",
    "Albumin", "Glucose", "Total Protein",
    "AST", "ALT", "LDH", "CRP",
    "Cr", "UA", "TB", "BUN", "BNP"
]

# 항암제/항생제/음식/가이드 데이터
ANTICANCER = {
    "6-MP":{"alias":"6-머캅토퓨린","aes":["골수억제","간수치 상승","구내염","오심"],"warn":["황달/진한 소변 시 진료","감염 징후 즉시 연락"],"ix":["알로푸리놀 병용 감량 가능","와파린 효과 변동"]},
    "MTX":{"alias":"메토트렉세이트","aes":["골수억제","간독성","신독성","구내염","광과민"],"warn":["탈수 시 독성↑","고용량 후 류코보린"],"ix":["NSAIDs/TMP-SMX 병용 독성↑","일부 PPI 상호작용"]},
    "ATRA":{"alias":"트레티노인","aes":["분화증후군","발열","피부/점막 건조","두통"],"warn":["분화증후군 의심 시 즉시 병원"],"ix":["테트라사이클린계와 가성뇌종양"]},
    "ARA-C":{"alias":"시타라빈","aes":["골수억제","발열","구내염","(HDAC) 신경독성"],"warn":["HDAC 시 신경증상 즉시 보고"],"ix":["효소유도제 상호작용"]},
    "G-CSF":{"alias":"그라신","aes":["골통/근육통","주사부위 반응","드물게 비장비대"],"warn":["좌상복부 통증 시 평가"],"ix":[]},
    "Hydroxyurea":{"alias":"하이드록시우레아","aes":["골수억제","피부색소침착","궤양"],"warn":["임신 회피"],"ix":[]},
    "Daunorubicin":{"alias":"도우노루비신","aes":["골수억제","심독성","오심/구토","점막염"],"warn":["누적용량 심기능"],"ix":["심독성↑ 병용 주의"]},
    "Idarubicin":{"alias":"이달루비신","aes":["골수억제","심독성","점막염"],"warn":["심기능"],"ix":[]},
    "Mitoxantrone":{"alias":"미토잔트론","aes":["골수억제","심독성","청록색 소변"],"warn":["심기능"],"ix":[]},
    "Cyclophosphamide":{"alias":"사이클로포스파미드","aes":["골수억제","출혈성 방광염","탈모"],"warn":["수분섭취·메스나"],"ix":["CYP 상호작용"]},
    "Etoposide":{"alias":"에토포사이드","aes":["골수억제","저혈압(주입)"],"warn":[],"ix":[]},
    "Topotecan":{"alias":"토포테칸","aes":["골수억제","설사"],"warn":[],"ix":[]},
    "Fludarabine":{"alias":"플루다라빈","aes":["면역억제","감염 위험↑","혈구감소"],"warn":["PCP 예방 고려"],"ix":[]},
    "Vincristine":{"alias":"빈크리스틴","aes":["말초신경병증","변비/장폐색"],"warn":["척수강내(IT) 투여 금지"],"ix":["CYP3A 상호작용"]},

    # --- 고형암 약물 ---
    "Paclitaxel":{"alias":"파클리탁셀","aes":["말초신경병증","탈모","골수억제"],"warn":["과민반응 전처치"],"ix":[]},
    "Docetaxel":{"alias":"도세탁셀","aes":["골수억제","부종","손발저림"],"warn":["스테로이드 전처치"],"ix":[]},
    "Cisplatin":{"alias":"시스플라틴","aes":["신독성","구토","이독성"],"warn":["수분·이뇨요법"],"ix":[]},
    "Carboplatin":{"alias":"카보플라틴","aes":["골수억제","구토"],"warn":["AUC 기반 용량"],"ix":[]},
    "Oxaliplatin":{"alias":"옥살리플라틴","aes":["말초감각이상(냉자극)","골수억제"],"warn":[],"ix":[]},
    "Pemetrexed":{"alias":"페메트렉시드","aes":["골수억제","피부발진"],"warn":["엽산/비타민B12 보충"],"ix":[]},
    "Gemcitabine":{"alias":"젬시타빈","aes":["골수억제","발열"],"warn":[],"ix":[]},
    "5-FU":{"alias":"플루오로우라실","aes":["점막염","설사","골수억제"],"warn":["DPD 결핍 주의"],"ix":[]},
    "Capecitabine":{"alias":"카페시타빈","aes":["수족증후군","설사","피로"],"warn":["DPD 결핍 주의"],"ix":[]},
    "Irinotecan":{"alias":"이리노테칸","aes":["설사(급성/지연)","골수억제"],"warn":["아트로핀/로페라미드 지침"],"ix":[]},
    "Doxorubicin":{"alias":"독소루비신","aes":["심독성","골수억제","탈모"],"warn":["누적용량·심장감시"],"ix":[]},
    "Ifosfamide":{"alias":"이포스파마이드","aes":["출혈성 방광염","신경독성","골수억제"],"warn":["메스나·수분"],"ix":[]},
    "Trastuzumab":{"alias":"트라스투주맙","aes":["심기능 저하"],"warn":["LVEF 모니터"],"ix":[]}
}

ABX_GUIDE = {
    "페니실린계":["발진/설사","와파린 효과↑ 가능"],
    "세팔로스포린계":["설사","일부 알코올 병용 시 플러싱 유사 반응"],
    "마크롤라이드":["QT 연장","CYP 상호작용(클라리스/에리쓰)"],
    "플루오로퀴놀론":["힘줄염/파열","광과민","QT 연장"],
    "카바페넴":["경련 위험(고용량/신부전)","광범위 커버"],
    "TMP-SMX":["고칼륨혈증","골수억제","MTX와 병용 주의"],
    "메트로니다졸":["금주","금속맛/구역"],
    "반코마이신":["Red man(주입속도)","신독성(고농도)"]
}

# 정/캡슐 약물(정수 입력)
PILL_MEDS = ["ATRA", "6-MP", "Hydroxyurea", "Capecitabine"]

FOODS = {
    "Albumin_low": ["달걀","연두부","흰살 생선","닭가슴살","귀리죽"],
    "K_low": ["바나나","감자","호박죽","고구마","오렌지"],
    "Hb_low": ["소고기","시금치","두부","달걀 노른자","렌틸콩"],
    "Na_low": ["전해질 음료","미역국","바나나","오트밀죽","삶은 감자"],
    "Ca_low": ["연어 통조림","두부","케일","브로콜리","(참깨 제외)"]
}
FEVER_GUIDE = "🌡️ 38.0~38.5℃ 해열제/경과, 38.5℃↑ 병원 연락, 39.0℃↑ 즉시 병원. (ANC<500 동반 발열=응급)"
NEUTRO_GUIDE = "🧼 호중구 감소 시: 생채소 금지, 익혀 섭취(전자레인지 30초 이상 가능), 2시간 지난 음식 재섭취 금지, 껍질 과일은 주치의와 상담."
IRON_WARN = "⚠️ 항암/백혈병 환자는 철분제 복용을 피하거나 반드시 주치의와 상담하세요. (비타민C 병용 시 흡수↑)"

CANCERS = [
    "ALL", "APL", "CML", "AML", "CLL",
    "고형암(폐/유방/대장 등)", "육종(Soft tissue/Bone)"
]

CANCER_HINT = {
    "ALL": "기본 CBC/CRP/간신장 + 필요 시 감염평가.",
    "APL": "CBC 외 PT/aPTT/피브리노겐, DIC score 고려.",
    "CML": "WBC↑ 가능, BCR-ABL PCR(선택). 간기능/LDH 동반.",
    "AML": "ANC 모니터링 최우선. Ara-C 사용 시 간/신장 주의.",
    "CLL": "림프구↑, 면역글로불린(선택). 간/신장 동반.",
    "고형암(폐/유방/대장 등)": "기본 CBC/CRP/간신장 + 항암 레짐별 특이 독성 모니터.",
    "육종(Soft tissue/Bone)": "도세/이포스/독소루비신 등 레짐 독성 주의(교육용)."
}

# -------------------- 레짐 프리셋 --------------------
REGIMEN_PRESETS = {
    # 혈액암
    "AML": {
        "7+3 (ARA-C + Daunorubicin)": {"ARA-C": {"form": "정맥(IV)", "dose": 0.0}, "Daunorubicin": {"dose_or_tabs": 0.0}},
        "Idarubicin + ARA-C": {"ARA-C": {"form": "정맥(IV)", "dose": 0.0}, "Idarubicin": {"dose_or_tabs": 0.0}}
    },
    "APL": {
        "ATRA + Idarubicin": {"ATRA": {"dose_or_tabs": 1}, "Idarubicin": {"dose_or_tabs": 0.0}}
    },
    "ALL": {
        "VCR + MTX + Cyclo": {"Vincristine": {"dose_or_tabs": 0.0}, "MTX": {"dose_or_tabs": 0.0}, "Cyclophosphamide": {"dose_or_tabs": 0.0}}
    },
    "CLL": {
        "Fludarabine + Cyclophosphamide": {"Fludarabine": {"dose_or_tabs": 0.0}, "Cyclophosphamide": {"dose_or_tabs": 0.0}}
    },
    "CML": {
        "Hydroxyurea 지혈적": {"Hydroxyurea": {"dose_or_tabs": 1}}
    },

    # 고형암
    "NSCLC": {
        "Carboplatin + Paclitaxel": {"Carboplatin": {"dose_or_tabs": 0.0}, "Paclitaxel": {"dose_or_tabs": 0.0}},
        "Cisplatin + Pemetrexed": {"Cisplatin": {"dose_or_tabs": 0.0}, "Pemetrexed": {"dose_or_tabs": 0.0}}
    },
    "Breast": {
        "AC → T (Doxorubicin + Cyclophosphamide → Paclitaxel)": {"Doxorubicin": {"dose_or_tabs": 0.0}, "Cyclophosphamide": {"dose_or_tabs": 0.0}, "Paclitaxel": {"dose_or_tabs": 0.0}},
        "Docetaxel + Carboplatin (+/- Trastuzumab)": {"Docetaxel": {"dose_or_tabs": 0.0}, "Carboplatin": {"dose_or_tabs": 0.0}, "Trastuzumab": {"dose_or_tabs": 0.0}}
    },
    "CRC": {
        "FOLFOX 유사 (5-FU + Oxaliplatin)": {"5-FU": {"dose_or_tabs": 0.0}, "Oxaliplatin": {"dose_or_tabs": 0.0}},
        "FOLFIRI 유사 (5-FU + Irinotecan)": {"5-FU": {"dose_or_tabs": 0.0}, "Irinotecan": {"dose_or_tabs": 0.0}}
    },
    "Gastric": {
        "Cisplatin + 5-FU": {"Cisplatin": {"dose_or_tabs": 0.0}, "5-FU": {"dose_or_tabs": 0.0}},
        "Docetaxel + Cisplatin + 5-FU": {"Docetaxel": {"dose_or_tabs": 0.0}, "Cisplatin": {"dose_or_tabs": 0.0}, "5-FU": {"dose_or_tabs": 0.0}}
    },
    "HCC": {
        "Doxorubicin 단요법(교육용)": {"Doxorubicin": {"dose_or_tabs": 0.0}}
    },
    "Pancreas": {
        "Gemcitabine + Paclitaxel": {"Gemcitabine": {"dose_or_tabs": 0.0}, "Paclitaxel": {"dose_or_tabs": 0.0}}
    },
    "Sarcoma": {
        "Doxorubicin + Ifosfamide": {"Doxorubicin": {"dose_or_tabs": 0.0}, "Ifosfamide": {"dose_or_tabs": 0.0}}
    }
}

SOLID_SUBTYPES = ["폐암(NSCLC)", "유방암", "대장암", "위암", "간암(HCC)", "췌장암"]
SOLID_MAP = {
    "폐암(NSCLC)": "NSCLC",
    "유방암": "Breast",
    "대장암": "CRC",
    "위암": "Gastric",
    "간암(HCC)": "HCC",
    "췌장암": "Pancreas"
}

# -------------------- HELPERS --------------------
def entered(v):
    try:
        return v is not None and float(v) > 0
    except Exception:
        return False

def interpret_labs(l):
    out = []
    def add(s): out.append("- " + s)

    if entered(l.get("WBC")):
        w = l["WBC"]
        add(f"WBC {w}: " + ("낮음 → 감염 위험↑" if w < 4 else "높음 → 감염/염증 가능" if w > 10 else "정상"))
    if entered(l.get("Hb")):
        h = l["Hb"]
        add(f"Hb {h}: " + ("낮음 → 빈혈" if h < 12 else "정상"))
    if entered(l.get("PLT")):
        p = l["PLT"]
        add(f"혈소판 {p}: " + ("낮음 → 출혈 위험" if p < 150 else "정상"))
    if entered(l.get("ANC")):
        a = l["ANC"]
        add(f"ANC {a}: " + ("중증 감소(<500)" if a < 500 else "감소(<1500)" if a < 1500 else "정상"))
    if entered(l.get("Albumin")):
        al = l["Albumin"]
        add(f"Albumin {al}: " + ("낮음 → 영양/염증/간질환 가능" if al < 3.5 else "정상"))
    if entered(l.get("Glucose")):
        g = l["Glucose"]
        add(f"Glucose {g}: " + ("고혈당(≥200)" if g >= 200 else "저혈당(<70)" if g < 70 else "정상"))
    if entered(l.get("CRP")):
        c = l["CRP"]
        add(f"CRP {c:.2f}: " + ("상승 → 염증/감염 의심" if c > 0.5 else "정상"))
    if entered(l.get("BUN")) and entered(l.get("Cr")) and l["Cr"] > 0:
        ratio = l["BUN"] / l["Cr"]
        if ratio > 20:
            add(f"BUN/Cr {ratio:.1f}: 탈수 의심")
        elif ratio < 10:
            add(f"BUN/Cr {ratio:.1f}: 간질환/영양 고려")
    return out

def summarize_meds(meds: dict):
    out = []
    for k, v in meds.items():
        info = ANTICANCER.get(k)
        if not info:
            continue
        line = f"• {k} ({info['alias']}): AE {', '.join(info['aes'])}"
        if info.get("warn"):
            line += f" | 주의: {', '.join(info['warn'])}"
        if info.get("ix"):
            line += f" | 상호작용: {', '.join(info['ix'])}"
        if k == "ARA-C" and isinstance(v, dict) and v.get("form"):
            line += f" | 제형: {v['form']}"
        out.append(line)
    return out

def food_suggestions(l):
    foods = []
    if entered(l.get("Albumin")) and l["Albumin"] < 3.5:
        foods.append("알부민 낮음 → " + ", ".join(FOODS["Albumin_low"]))
    if entered(l.get("K")) and l["K"] < 3.5:
        foods.append("칼륨 낮음 → " + ", ".join(FOODS["K_low"]))
    if entered(l.get("Hb")) and l["Hb"] < 12:
        foods.append("Hb 낮음 → " + ", ".join(FOODS["Hb_low"]))
    if entered(l.get("Na")) and l["Na"] < 135:
        foods.append("나트륨 낮음 → " + ", ".join(FOODS["Na_low"]))
    if entered(l.get("Ca")) and l["Ca"] < 8.5:
        foods.append("칼슘 낮음 → " + ", ".join(FOODS["Ca_low"]))
    if entered(l.get("ANC")) and l["ANC"] < 500:
        foods.append(NEUTRO_GUIDE)
    foods.append(IRON_WARN)
    return foods

# 위험 배지
RISK_TAGS = {
    "QT↑": lambda meds, abx: any(x in (abx or []) for x in ["마크롤라이드","플루오로퀴놀론"]),
    "신독성↑": lambda meds, abx: "반코마이신" in (abx or []) or ("MTX" in meds),
    "출혈 위험": lambda meds, abx: "Cyclophosphamide" in meds,
    "골수억제": lambda meds, abx: any(k in meds for k in ["6-MP","MTX","ARA-C","Daunorubicin","Idarubicin","Mitoxantrone","Etoposide","Topotecan","Fludarabine","Hydroxyurea","Vincristine","Cyclophosphamide","Paclitaxel","Docetaxel","Irinotecan","5-FU","Capecitabine"])
}
def collect_risk_badges(meds, abx_list):
    badges = []
    for tag, fn in RISK_TAGS.items():
        try:
            if fn(meds, abx_list):
                badges.append(tag)
        except Exception:
            pass
    return badges

# 사용자 임계값
st.session_state.setdefault("thresholds", {"ANC": 500.0, "Hb": 8.0, "PLT": 50.0, "CRP": 0.5})

# -------------------- UI --------------------
st.divider()
st.header("1️⃣ 환자/검사 정보")
colA, colB = st.columns(2)
with colA:
    nickname = st.text_input("별명(저장/그래프용)", placeholder="예: 홍길동")
with colB:
    exam_date = st.date_input("검사 날짜", value=date.today())

# 암종류 + 고형암 세부
cancer = st.selectbox("암 종류를 선택하세요", CANCERS, index=0, help="선택 시 관련 검사 힌트를 표기합니다.")
solid_detail = None
preset_key = None
if cancer == "고형암(폐/유방/대장 등)":
    solid_detail = st.selectbox("고형암 세부", ["폐암(NSCLC)","유방암","대장암","위암","간암(HCC)","췌장암"])
    preset_key = {"폐암(NSCLC)":"NSCLC","유방암":"Breast","대장암":"CRC","위암":"Gastric","간암(HCC)":"HCC","췌장암":"Pancreas"}[solid_detail]
elif cancer == "육종(Soft tissue/Bone)":
    preset_key = "Sarcoma"
else:
    preset_key = cancer

if cancer in CANCER_HINT:
    st.info(f"🔎 검사 힌트: {CANCER_HINT[cancer]}")

# 레짐 프리셋
preset_name = None
if preset_key in REGIMEN_PRESETS:
    preset_name = st.selectbox("레짐 프리셋(선택)", ["(선택 안 함)"] + list(REGIMEN_PRESETS[preset_key].keys()))
else:
    st.selectbox("레짐 프리셋(선택)", ["(해당 없음)"])

st.divider()
st.header("2️⃣ 해석 카테고리 & 약물/상태")
category = st.radio("카테고리", ["일반 해석","항암치료","항생제","투석 환자","당뇨 환자"], horizontal=True)

meds, extras = {}, {}
if category == "항암치료":
    with st.container(border=True):
        st.markdown("### 💊 항암제/보조제")
        # 프리셋 자동 로드
        if preset_name and preset_name != "(선택 안 함)":
            if st.button("프리셋 자동 로드"):
                for k, v in REGIMEN_PRESETS[preset_key][preset_name].items():
                    meds[k] = v.copy()
                st.success(f"프리셋 적용: {preset_name}")
        # 개별 선택
        if st.checkbox("ARA-C 사용"):
            meds.setdefault("ARA-C", {})
            meds["ARA-C"]["form"] = st.selectbox("ARA-C 제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"])
            meds["ARA-C"]["dose"] = st.number_input("ARA-C 용량/일(임의)", min_value=0.0, step=0.1)
        cols = st.columns(3)
        keys = [
            "6-MP","MTX","ATRA","G-CSF","Hydroxyurea","Daunorubicin","Idarubicin",
            "Mitoxantrone","Cyclophosphamide","Etoposide","Topotecan","Fludarabine","Vincristine",
            "Paclitaxel","Docetaxel","Cisplatin","Carboplatin","Oxaliplatin","Pemetrexed",
            "Gemcitabine","5-FU","Capecitabine","Irinotecan","Doxorubicin","Ifosfamide","Trastuzumab"
        ]
        for i, key in enumerate(keys):
            with cols[i % 3]:
                if st.checkbox(f"{key} 사용", key=f"use_{key}"):
                    meds.setdefault(key, {})
                    if key in PILL_MEDS:
                        meds[key]["dose_or_tabs"] = st.number_input(f"{key} 캡슐/정 개수", min_value=1, step=1, value=1, key=f"dose_{key}")
                    else:
                        meds[key]["dose_or_tabs"] = st.number_input(f"{key} 용량(임의)", min_value=0.0, step=0.1, key=f"dose_{key}")
        if st.checkbox("이뇨제 복용 중"):
            extras["diuretic"] = True
        st.info(FEVER_GUIDE)

elif category == "항생제":
    with st.container(border=True):
        st.markdown("### 🧪 항생제")
        extras["abx"] = st.multiselect("사용 중인 항생제", list(ABX_GUIDE.keys()))

elif category == "투석 환자":
    with st.container(border=True):
        st.markdown("### 🫧 투석 추가 항목")
        extras["urine_ml"] = st.number_input("하루 소변량 (mL)", min_value=0.0, step=10.0)
        extras["hd_today"] = st.checkbox("오늘 투석 시행")
        extras["post_hd_weight_delta"] = st.number_input("투석 후 체중 변화 (kg)", min_value=-10.0, max_value=10.0, step=0.1)
        if st.checkbox("이뇨제 복용 중", key="diuretic_dial"):
            extras["diuretic"] = True

elif category == "당뇨 환자":
    with st.container(border=True):
        st.markdown("### 🍚 당뇨 지표")
        extras["FPG"] = st.number_input("식전 혈당 (mg/dL)", min_value=0.0, step=1.0)
        extras["PP1h"] = st.number_input("식후 1시간 혈당 (mg/dL)", min_value=0.0, step=1.0)
        extras["PP2h"] = st.number_input("식후 2시간 혈당 (mg/dL)", min_value=0.0, step=1.0)
        extras["HbA1c"] = st.number_input("HbA1c (%)", min_value=0.0, step=0.1, format="%.1f")

# 사용자 임계값 설정
with st.expander("⚙️ 사용자 임계값 설정(배너 경고)"):
    th = st.session_state["thresholds"]
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        th["ANC"] = st.number_input("ANC 경고 미만", min_value=0.0, value=float(th["ANC"]), step=50.0)
    with c2:
        th["Hb"] = st.number_input("Hb 경고 미만", min_value=0.0, value=float(th["Hb"]), step=0.5, format="%.1f")
    with c3:
        th["PLT"] = st.number_input("PLT 경고 미만", min_value=0.0, value=float(th["PLT"]), step=5.0)
    with c4:
        th["CRP"] = st.number_input("CRP 경고 초과", min_value=0.0, value=float(th["CRP"]), step=0.05, format="%.2f")

st.divider()
st.header("3️⃣ 혈액 검사 수치 입력 (입력한 값만 사용)")

with st.form("labs_form"):
    WBC = st.number_input("WBC (백혈구)", min_value=0.0, step=0.1)
    Hb = st.number_input("Hb (혈색소)", min_value=0.0, step=0.1)
    PLT = st.number_input("PLT (혈소판)", min_value=0.0, step=1.0)
    ANC = st.number_input("ANC (호중구)", min_value=0.0, step=10.0)
    Ca = st.number_input("Ca (칼슘)", min_value=0.0, step=0.1)
    P_ = st.number_input("P (인)", min_value=0.0, step=0.1)
    Na = st.number_input("Na (소디움)", min_value=0.0, step=0.1)
    K = st.number_input("K (포타슘)", min_value=0.0, step=0.1)
    Albumin = st.number_input("Albumin (알부민)", min_value=0.0, step=0.1)
    Glucose = st.number_input("Glucose (혈당)", min_value=0.0, step=1.0)
    TotalProtein = st.number_input("Total Protein (총단백)", min_value=0.0, step=0.1)
    AST = st.number_input("AST", min_value=0.0, step=1.0)
    ALT = st.number_input("ALT", min_value=0.0, step=1.0)
    LDH = st.number_input("LDH", min_value=0.0, step=1.0)
    CRP = st.number_input("CRP", min_value=0.0, step=0.01, format="%.2f")
    Cr = st.number_input("Creatinine (Cr)", min_value=0.0, step=0.1)
    UA = st.number_input("Uric Acid (요산)", min_value=0.0, step=0.1)
    TB = st.number_input("Total Bilirubin (TB)", min_value=0.0, step=0.1)
    BUN = st.number_input("BUN", min_value=0.0, step=0.1)
    BNP = st.number_input("BNP (선택)", min_value=0.0, step=1.0)
    run = st.form_submit_button("🔎 해석하기", use_container_width=True)

# -------------------- RUN --------------------
if run:
    labs = {
        "WBC": WBC, "Hb": Hb, "PLT": PLT, "ANC": ANC,
        "Ca": Ca, "P": P_, "Na": Na, "K": K,
        "Albumin": Albumin, "Glucose": Glucose, "Total Protein": TotalProtein,
        "AST": AST, "ALT": ALT, "LDH": LDH, "CRP": CRP,
        "Cr": Cr, "UA": UA, "TB": TB, "BUN": BUN, "BNP": BNP
    }

    # 상단 3줄 요약
    th = st.session_state["thresholds"]
    alerts = []
    if entered(ANC) and ANC < th["ANC"]:
        alerts.append("ANC 낮음")
    if entered(Hb) and Hb < th["Hb"]:
        alerts.append("Hb 낮음")
    if entered(PLT) and PLT < th["PLT"]:
        alerts.append("혈소판 낮음")
    if entered(CRP) and CRP > th["CRP"]:
        alerts.append("CRP 상승")

    action_lines = []
    if "ANC 낮음" in alerts:
        action_lines.append("호중구 감소: 생채소 금지·익혀먹기·발열 시 즉시 연락")
    if "혈소판 낮음" in alerts:
        action_lines.append("혈소판 저하: 넘어짐/출혈 주의, 칫솔 부드럽게")
    if "Hb 낮음" in alerts:
        action_lines.append("빈혈: 어지럼 주의, 휴식·수분 보충")
    if "CRP 상승" in alerts:
        action_lines.append("염증 의심: 발열 체크, 의사 상담 고려")

    with st.container(border=True):
        st.subheader("🧭 오늘의 3줄 요약")
        if alerts:
            st.error(" • 위험요소: " + ", ".join(alerts))
        else:
            st.success(" • 특별 위험 없음(입력 기준)")
        st.write(" • 권장: " + (" / ".join(action_lines) if action_lines else "일상 관찰"))
        st.write(" • 카테고리/암종류: " + f"{category} / {cancer}")

    # 상세 해석
    st.subheader("📋 해석 결과")
    lines = interpret_labs(labs)
    if lines:
        for x in lines:
            st.write(x)
    else:
        st.info("입력된 수치가 없습니다.")

    # 음식 가이드
    fs = food_suggestions(labs)
    if fs:
        st.markdown("### 🥗 음식 가이드")
        for f in fs:
            st.write("- " + f)

    # 상호작용/위험 배지
    abx_list = extras.get("abx") if isinstance(extras.get("abx"), list) else []
    risk_badges = collect_risk_badges(meds, abx_list)
    if risk_badges:
        st.markdown("### 🚨 위험 배지")
        st.write(" • " + " | ".join(risk_badges))

    # 약물 요약
    if category == "항암치료" and meds:
        st.markdown("### 💊 항암제 부작용·상호작용 요약")
        for line in summarize_meds(meds):
            st.write(line)

    # 항생제 요약
    if category == "항생제" and abx_list:
        st.markdown("### 🧪 항생제 주의 요약")
        for a in abx_list:
            st.write(f"• {a}: {', '.join(ABX_GUIDE[a])}")

    st.markdown("### 🌡️ 발열 가이드")
    st.write(FEVER_GUIDE)

    # 보고서 생성
    def build_report_text(name, d, cancer, category, labs, lines, meds, extras, preset_name):
        lab_lines = []
        for k in ORDER:
            v = labs.get(k)
            if entered(v):
                if k == "CRP":
                    lab_lines.append(f"- {k}: {v:.2f}")
                else:
                    lab_lines.append(f"- {k}: {v}")
        meds_lines = summarize_meds(meds) if meds else []
        abx_lines = []
        if extras.get("abx"):
            for a in extras["abx"]:
                abx_lines.append(f"• {a}: {', '.join(ABX_GUIDE[a])}")
        txt = [
            f"# BloodMap 보고서 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
            f"- 환자: {name or '미기입'}",
            f"- 검사일: {d.isoformat() if isinstance(d, date) else d}",
            f"- 카테고리: {category}",
            f"- 암종류: {cancer}",
            f"- 레짐 프리셋: {preset_name or '(선택 없음)'}",
            "\n## 입력 수치",
            *(lab_lines or ["- (입력 값 없음)"]),
            "\n## 해석 요약",
            *(lines or ["- (해석할 값 없음)"]),
            "\n## 음식 가이드",
            *(food_suggestions(labs) or ["- (권장 없음)"]),
            "\n## 약물 요약",
            *(meds_lines or ["- (해당 없음)"]),
            "\n## 항생제 주의",
            *(abx_lines or ["- (해당 없음)"]),
            "\n## 발열 가이드",
            FEVER_GUIDE
        ]
        return "\n".join(txt)

    report_text = build_report_text(nickname, exam_date, cancer, category, labs, lines, meds, extras, preset_name)
    file_stub = f"bloodmap_{(nickname or 'noname')}_{exam_date.strftime('%Y%m%d')}"

    # 다운로드
    st.download_button("📥 보고서(.md) 다운로드", data=report_text.encode("utf-8"), file_name=f"{file_stub}.md", mime="text/markdown", use_container_width=True)
    st.download_button("📥 보고서(.txt) 다운로드", data=report_text.encode("utf-8"), file_name=f"{file_stub}.txt", mime="text/plain", use_container_width=True)
    if HAS_PDF:
        def make_pdf(text: str) -> bytes:
            buf = BytesIO()
            c = canvas.Canvas(buf, pagesize=A4)
            x, y = 20*mm, A4[1] - 20*mm
            try:
                pdfmetrics.registerFont(TTFont('Nanum', 'NanumGothic.ttf'))
                c.setFont('Nanum', 10)
            except Exception:
                c.setFont('Helvetica', 10)
            for line in text.split("\n"):
                if y < 20*mm:
                    c.showPage()
                    try:
                        c.setFont('Nanum', 10)
                    except Exception:
                        c.setFont('Helvetica', 10)
                    y = A4[1] - 20*mm
                c.drawString(20*mm, y, line)
                y -= 12
            c.save()
            buf.seek(0)
            return buf.read()
        pdf_bytes = make_pdf(report_text)
        st.download_button("📥 보고서(.pdf) 다운로드", data=pdf_bytes, file_name=f"{file_stub}.pdf", mime="application/pdf", use_container_width=True)
    else:
        st.caption("PDF 생성을 위해서는 reportlab 설치가 필요합니다: pip install reportlab")

    # 저장
    if nickname.strip():
        if st.checkbox("📝 이 별명으로 저장", value=True):
            rec = {
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "category": category,
                "cancer": cancer,
                "preset": preset_name,
                "labs": {k: v for k, v in labs.items() if entered(v)},
                "meds": meds,
                "extras": extras
            }
            st.session_state["records"].setdefault(nickname, []).append(rec)
            st.success("저장되었습니다. 아래 그래프에서 추이를 확인하세요.")
    else:
        st.info("별명을 입력하면 추이 그래프를 사용할 수 있어요.")

# -------------------- GRAPHS --------------------
st.markdown("---")
st.subheader("📈 별명별 추이 그래프 (WBC, Hb, PLT, CRP, ANC)")
if not HAS_PD:
    st.info("그래프는 pandas 설치 시 활성화됩니다. (pip install pandas)")
else:
    if st.session_state["records"]:
        sel = st.selectbox("별명 선택", sorted(st.session_state["records"].keys()))
        rows = st.session_state["records"].get(sel, [])
        if rows:
            data = [{"ts": r["ts"], **{k: r["labs"].get(k) for k in ["WBC","Hb","PLT","CRP","ANC"]}} for r in rows]
            df = pd.DataFrame(data).set_index("ts")
            st.line_chart(df.dropna(how="all"))
        else:
            st.info("선택한 별명의 저장 기록이 없습니다.")
    else:
        st.info("아직 저장된 기록이 없습니다.")

st.markdown(f"👁️ 조회수: **{st.session_state['page_views']}**")
