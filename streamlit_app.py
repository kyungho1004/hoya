# -*- coding: utf-8 -*-
"""
BloodMap 피수치 자동 해석기 v2.9 (통합본, 단일 파일)
- 제작자: Hoya/GPT · 자문: Hoya/GPT
- 모바일/PC 동일한 단일 컬럼 UI, 줄꼬임 방지
- 입력한 수치만 결과/보고서에 표시
- 카테고리: 일반 해석 / 항암치료 / 항생제 / 투석 환자 / 당뇨 환자
- (요청 반영) 카테고리 선택을 상단(환자 정보 바로 아래)으로 이동
"""
from __future__ import annotations

import io
from datetime import datetime, date
from typing import Dict, List, Optional

import streamlit as st

# Optional deps
try:
    import pandas as pd
    HAS_PD = True
except Exception:
    HAS_PD = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    HAS_PDF = True
except Exception:
    HAS_PDF = False

# ----------------------------- App Config -----------------------------
st.set_page_config(page_title="피수치 자동 해석기 by Hoya/GPT", layout="centered")
st.title("🩸 피수치 자동 해석기")
st.caption("👤 제작자: **Hoya/GPT** · 자문: **Hoya/GPT**")
st.write("입력한 값만 결과에 반영됩니다. 모바일에서도 줄꼬임 없이 위에서 아래로 고정 순서로 정렬됩니다.")

# Session state init
if "records" not in st.session_state:
    st.session_state.records = {}
if "view_count" not in st.session_state:
    st.session_state.view_count = 0
st.session_state.view_count += 1

# Final ORDER (2025-08-25 확정)
ORDER = [
    "WBC","Hb","PLT","ANC",
    "Ca","P","Na","K","Albumin",
    "Glucose","Total Protein","AST","ALT","LDH",
    "CRP","Cr","Uric Acid","Total Bilirubin","BUN","BNP"
]

# 각 항목별 표시 형식(소수 자릿수)과 step 설정
FORMAT_MAP = {
    "WBC":"%.1f","Hb":"%.1f","PLT":"%.0f","ANC":"%.0f",
    "Ca":"%.1f","P":"%.1f","Na":"%.1f","K":"%.1f","Albumin":"%.1f",
    "Glucose":"%.0f","Total Protein":"%.1f","AST":"%.0f","ALT":"%.0f","LDH":"%.0f",
    "CRP":"%.2f","Cr":"%.1f","Uric Acid":"%.1f","Total Bilirubin":"%.1f","BUN":"%.1f","BNP":"%.0f"
}
STEP_MAP = {k: (1.0 if FORMAT_MAP[k] == "%.0f" else 0.1) for k in FORMAT_MAP}
# CRP는 0.01 단위로 세밀하게 입력
STEP_MAP["CRP"] = 0.01

# 약물/가이드 데이터 (요약)
ANTICANCER = {
    "6-MP":{"alias":"6-머캅토퓨린","aes":["골수억제","간수치 상승","구내염","오심"],"warn":["황달/진한 소변 시 진료","감염 징후 즉시 연락"],"ix":["알로푸리놀 병용 감량 가능","와파린 효과 변동"]},
    "MTX":{"alias":"메토트렉세이트","aes":["골수억제","간독성","신독성","구내염","광과민"],"warn":["탈수 시 독성↑","고용량 후 류코보린"],"ix":["NSAIDs/TMP-SMX 병용 독성↑","일부 PPI 상호작용"]},
    "ATRA":{"alias":"베사노이드(트레티노인)","aes":["분화증후군","발열","피부/점막 건조","두통","설사"],"warn":["분화증후군 의심 시 즉시 병원"],"ix":["테트라사이클린계와 가성뇌종양"]},
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
    "Vincristine":{"alias":"빈크리스틴","aes":["말초신경병증","변비/장폐색"],"warn":["IT 투여 금지"],"ix":["CYP3A 상호작용"]},
}
ABX_GUIDE = {
    "페니실린계":["발진/설사","와파린 효과↑ 가능"],
    "세팔로스포린계":["설사","일부 알코올과 병용 시 플러싱 유사"],
    "마크롤라이드":["QT 연장","CYP 상호작용(클라리스/에리쓰)"],
    "플루오로퀴놀론":["힘줄염/파열","광과민","QT 연장"],
    "카바페넴":["경련 위험(고용량/신부전)","광범위 커버"],
    "TMP-SMX":["고칼륨혈증","골수억제","MTX와 병용 주의"],
    "메트로니다졸":["금주","금속맛/구역"],
    "반코마이신":["Red man(주입속도)","신독성(고농도)"],
}
FOODS = {
    "Albumin_low": ["달걀","연두부","흰살 생선","닭가슴살","귀리죽"],
    "K_low": ["바나나","감자","호박죽","고구마","오렌지"],
    "Hb_low": ["소고기","시금치","두부","달걀 노른자","렌틸콩"],
    "Na_low": ["전해질 음료","미역국","바나나","오트밀죽","삶은 감자"],
    "Ca_low": ["연어 통조림","두부","케일","브로콜리","(참깨 제외)"],
}
NEUTROPENIC_RULES = [
    "생채소·날음식 금지, 모든 음식 익혀 섭취",
    "전자레인지라도 **30초 이상** 재가열 후 섭취",
    "조리 후 남은 음식은 **2시간 이후 섭취 비권장**",
    "멸균/살균 처리 식품 권장",
    "껍질 있는 과일은 **주치의와 상담 후** 섭취 여부 결정",
]
FEVER_GUIDE = (
    "🌡️ **발열 대처**\n"
    "- 38.0~38.5℃: 해열제 복용/경과 관찰\n"
    "- 38.5℃ 이상: **병원 연락**\n"
    "- 39.0℃ 이상: **즉시 병원 방문**\n"
    "- ANC < 500 + 발열: **응급**"
)
ANTIPYRETIC_TIPS = (
    "💊 **해열제 가이드(요약)**\n"
    "- 아세트아미노펜: 필요 시 4~6시간 간격, 1일 최대용량 준수\n"
    "- 이부프로펜: 위장장애/신장 주의, 의사 지시 하 사용\n"
    "- 교차 투여는 **의료진 지시**가 있을 때만"
)

def entered(v) -> bool:
    try:
        return v is not None and str(v) != "" and float(v) > 0
    except Exception:
        return False

def interpret_labs(l: Dict[str, Optional[float]]) -> List[str]:
    out: List[str] = []
    def add(s): out.append("- " + s)
    if entered(l.get("WBC")):
        w = l["WBC"]
        if w < 4: add(f"WBC {w}: 낮음 → 감염 위험↑")
        elif w > 10: add(f"WBC {w}: 높음 → 감염/염증 가능")
        else: add(f"WBC {w}: 정상")
    if entered(l.get("Hb")):
        add(f"Hb {l['Hb']}: {'낮음 → 빈혈' if l['Hb']<12 else '정상'}")
    if entered(l.get("PLT")):
        add(f"혈소판 {l['PLT']}: {'낮음 → 출혈 위험' if l['PLT']<150 else '정상'}")
    if entered(l.get("ANC")):
        anc = l["ANC"]
        if anc < 500: add(f"ANC {anc}: **중증 감소(<500)**")
        elif anc < 1500: add(f"ANC {anc}: 감소(<1500)")
        else: add(f"ANC {anc}: 정상")
    if entered(l.get("Albumin")):
        add(f"Albumin {l['Albumin']}: {'낮음 → 영양/염증/간질환 가능' if l['Albumin']<3.5 else '정상'}")
    if entered(l.get("Glucose")):
        g = l["Glucose"]
        if g >= 200: add(f"Glucose {g}: 고혈당(≥200)")
        elif g < 70: add(f"Glucose {g}: 저혈당(<70)")
        else: add(f"Glucose {g}: 정상")
    if entered(l.get("CRP")):
        add(f"CRP {l['CRP']}: {'상승 → 염증/감염 의심' if l['CRP']>0.5 else '정상'}")
    if entered(l.get("BUN")) and entered(l.get("Cr")) and l["Cr"]>0:
        ratio = l["BUN"]/l["Cr"]
        if ratio > 20: add(f"BUN/Cr {ratio:.1f}: 탈수 의심")
        elif ratio < 10: add(f"BUN/Cr {ratio:.1f}: 간질환/영양 고려")
    return out

def food_suggestions(l: Dict[str, Optional[float]]) -> List[str]:
    foods: List[str] = []
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
        foods.append("🧼 호중구 감소(ANC<500): 생채소 금지 · 모든 음식 익혀 섭취 · 조리 후 2시간 지난 음식 비권장 · 멸균식품 권장 · 껍질 과일은 주치의와 상의")
    foods.append("⚠️ 항암/백혈병 환자는 **철분제** 복용 전 반드시 주치의와 상의 (비타민 C 병용 시 흡수↑).")
    return foods

def summarize_meds(meds: Dict) -> List[str]:
    out = []
    for k, v in meds.items():
        info = ANTICANCER.get(k)
        if not info: 
            continue
        line = f"• {k} ({info['alias']}) — AE: {', '.join(info['aes'])}"
        if info.get("warn"): line += f" | 주의: {', '.join(info['warn'])}"
        if info.get("ix"): line += f" | 상호작용: {', '.join(info['ix'])}"
        if k == "ARA-C" and isinstance(v, dict) and v.get("form"):
            line += f" | 제형: {v['form']}"
        out.append(line)
    return out

def estimate_anc_500_date(records: List[Dict]) -> Optional[str]:
    if not HAS_PD or not records or len(records) < 2:
        return None
    rows = []
    for r in records:
        anc = r.get("labs",{}).get("ANC")
        ts = r.get("ts")
        if entered(anc) and ts:
            try:
                t = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                rows.append({"t": t, "ANC": float(anc)})
            except Exception:
                pass
    if len(rows) < 2:
        return None
    import numpy as np
    import pandas as pd
    df = pd.DataFrame(rows).sort_values("t")
    x = (df["t"] - df["t"].min()).dt.total_seconds() / 86400.0
    y = df["ANC"]
    if y.max() >= 500:
        return "이미 500 이상 도달"
    try:
        A = np.vstack([x, np.ones(len(x))]).T
        slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]
        if slope <= 0:
            return None
        days_needed = (500 - intercept) / slope
        target_date = df["t"].min() + pd.to_timedelta(days_needed, unit="D")
        return target_date.strftime("%Y-%m-%d")
    except Exception:
        return None


def build_report_pdf(text: str) -> bytes:
    """PDF 생성: 가능한 경우 한글 글꼴 등록 후 사용."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.rl_config import TTFSearchPath
    import os

    # 후보 글꼴 경로
    candidates = [
        "NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "Malgun Gothic.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJKkr-Regular.otf",
    ]
    font_name = None
    for path in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("KR", path))
                font_name = "KR"
                break
            except Exception:
                continue

    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    width, height = A4
    x, y = 40, height - 40
    try:
        if font_name:
            c.setFont(font_name, 10)
        else:
            c.setFont("Helvetica", 10)
    except Exception:
        pass

    for raw in text.splitlines():
        line = raw
        if not font_name:
            # 폰트가 없으면 라틴만 안전하게 출력
            try:
                line = raw.encode("latin-1", "ignore").decode("latin-1")
            except Exception:
                line = "".join(ch if ord(ch) < 128 else " " for ch in raw)
        c.drawString(x, y, line[:110])
        y -= 14
        if y < 40:
            c.showPage()
            try:
                if font_name:
                    c.setFont(font_name, 10)
                else:
                    c.setFont("Helvetica", 10)
            except Exception:
                pass
            y = height - 40
    c.save()
    packet.seek(0)
    return packet.read()


# ----------------------------- UI -----------------------------
st.divider()
st.header("1️⃣ 환자 정보")
name = st.text_input("별명(저장/그래프용)", placeholder="예: 홍길동")
test_date = st.date_input("검사 날짜", value=date.today())

st.divider()
st.header("2️⃣ 카테고리")
category = st.selectbox("카테고리 선택", ["일반 해석","항암치료","항생제","투석 환자","당뇨 환자"])

# --- 항암치료 세부옵션 (암종류 등) ---
meds: Dict = {}
extras: Dict = {}
qna: List[str] = []

if category == "항암치료":
    st.subheader("암 종류 (선택)")
    cancer = st.radio("암 종류", ["선택 안 함","AML","APL","ALL","CML","CLL","고형암"], horizontal=True)

    if cancer != "선택 안 함":
        st.info("선택한 암종류에 권장 모니터링 항목과 추가 지표 입력란이 표시됩니다. (입력은 선택)")
        if cancer in ("AML","ALL","CLL"):
            st.markdown("**기본 모니터링 권장:** WBC, Hb, PLT, ANC, Ca/P/Na/K, Albumin, AST/ALT/LDH, CRP, Cr, Glucose, Total Protein")
        if cancer == "APL":
            st.markdown("**APL 권장:** 위 기본 + PT, aPTT, Fibrinogen, (선택) DIC Score")
            extras["PT"] = st.number_input("PT (초)", value=None, step=0.1, format="%.2f")
            extras["aPTT"] = st.number_input("aPTT (초)", value=None, step=0.1, format="%.2f")
            extras["Fibrinogen"] = st.number_input("Fibrinogen (mg/dL)", value=None, step=1.0, format="%.1f")
            extras["DIC_Score"] = st.number_input("DIC Score (선택)", value=None, step=1.0, format="%.0f")
        if cancer == "CML":
            extras["BCR-ABL_PCR"] = st.text_input("BCR-ABL PCR 결과 (선택)", placeholder="예: MR3.0, 0.1% 등")
        if cancer == "CLL":
            extras["Immunoglobulin"] = st.text_input("면역글로불린 (선택)", placeholder="예: IgG 600 mg/dL")


        if cancer == "고형암":
            st.markdown("**고형암 공통 모니터링 권장:** CBC(빈혈/혈소판), 간기능(AST/ALT/TB), 신장(Cr/BUN), 전해질(Na/K/Ca), CRP")
            solid_type = st.selectbox("고형암 세부 선택", ["폐암","유방암","대장암","위암","간암(HCC)","췌장암","난소암","전립선암","기타"])
            st.markdown("**종양표지자 (선택 입력)**")
            extras["CEA"] = st.number_input("CEA (ng/mL)", value=None, step=0.1, format="%.2f")
            extras["CA19-9"] = st.number_input("CA 19-9 (U/mL)", value=None, step=1.0, format="%.1f")
            extras["CA-125"] = st.number_input("CA-125 (U/mL)", value=None, step=1.0, format="%.1f")
            extras["AFP"] = st.number_input("AFP (ng/mL)", value=None, step=0.1, format="%.2f")
            extras["PSA"] = st.number_input("PSA (ng/mL)", value=None, step=0.1, format="%.2f")
            extras["CA15-3"] = st.number_input("CA 15-3 (U/mL)", value=None, step=0.1, format="%.2f")
            # 보호자 맞춤 Q&A (간단)
            qna_map_solid = {
                "폐암":[
                    "호흡곤란·지속 기침·혈담 발생 시 즉시 병원.",
                    "항암 중 발열·흉통·산소포화도 저하는 응급."
                ],
                "유방암":[
                    "림프부종 예방: 팔 채혈/혈압 측정은 반대측 우선.",
                    "피부변화·상처 감염 징후 관찰."
                ],
                "대장암":[
                    "설사/변비 시 수분·전해질 보충, 심하면 진료.",
                    "복통·혈변·장폐색 증상 즉시 평가."
                ],
                "위암":[
                    "구토 지속/체중 급감 시 영양평가.",
                    "출혈 의심(흑변/토혈) 시 응급."
                ],
                "간암(HCC)":[
                    "복수·황달·의식 변화는 즉시 병원.",
                    "알코올·간독성 약물 회피."
                ],
                "췌장암":[
                    "복통 악화·황달·식욕부진 지속 시 보고.",
                    "영양 관리(고열량·고단백) 중요."
                ],
                "난소암":[
                    "복부팽만·호흡곤란(복수/흉수) 발생 시 평가.",
                    "오심·구토 지속 시 탈수 주의."
                ],
                "전립선암":[
                    "뼈통증 악화·신경학적 증상(척수압박) 즉시 평가.",
                    "야뇨·요폐·혈뇨 변화 모니터."
                ],
                "기타":[
                    "발열·심한 통증·출혈·호흡곤란은 공통 응급 신호.",
                    "약물 복용 시간·부작용 기록 유지."
                ]
            }
            qna.extend(qna_map_solid.get(solid_type, []))

        qna_map = {
            "AML":[
                "집에서는 발열·출혈·호흡곤란 시 즉시 병원으로.",
                "ANC 저하 시 외출 최소화, 생음식 금지."
            ],
            "APL":[
                "미세출혈 징후(멍/코피) 관찰, 이상 시 즉시 연락.",
                "분화증후군 의심 증상(호흡곤란, 체중증가, 부종) 즉시 병원."
            ],
            "ALL":[
                "구내염 예방: 부드러운 칫솔, 자극 음식 피하기.",
                "체온·수분섭취 기록 습관화."
            ],
            "CML":[
                "약물 복용 시간 일정하게 유지.",
                "PCR 추적 결과는 주치의와 상의하여 해석."
            ],
            "CLL":[
                "반복 감염 주의, 예방접종 일정 상담.",
                "림프절 커짐·피로 악화 시 보고."
            ],
        }
        qna.extend(qna_map.get(cancer, []))

    st.subheader("💊 항암제/보조제")
    if st.checkbox("ARA-C 사용"):
        meds["ARA-C"] = {
            "form": st.selectbox("ARA-C 제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"]),
            "dose": st.number_input("ARA-C 용량/일(임의 입력)", min_value=0.0, step=0.1)
        }
    for key in ["6-MP","MTX","ATRA","G-CSF","Hydroxyurea","Daunorubicin","Idarubicin",
                "Mitoxantrone","Cyclophosphamide","Etoposide","Topotecan","Fludarabine","Vincristine"]:
        if st.checkbox(f"{key} 사용"):
            meds[key] = {"tabs_or_dose": st.number_input(f"{key} 투여량/알약 개수(소수 허용)", min_value=0.0, step=0.1)}

    st.info(FEVER_GUIDE)
    st.info(ANTIPYRETIC_TIPS)

    if st.checkbox("이뇨제 복용 중"):
        extras["diuretic"] = True

elif category == "항생제":
    st.subheader("🧪 항생제")
    abx_list = st.multiselect("사용 중인 항생제", list(ABX_GUIDE.keys()))
    if abx_list:
        extras["Antibiotics"] = abx_list

elif category == "투석 환자":
    st.subheader("🫧 투석 추가 항목")
    extras["Urine_ml"] = st.number_input("하루 소변량 (mL)", min_value=0.0, step=10.0)
    extras["HD_today"] = st.checkbox("오늘 투석 시행")
    extras["Post_HD_weight_delta"] = st.number_input("투석 후 체중 변화 (kg)", min_value=-10.0, max_value=10.0, step=0.1)
    if st.checkbox("이뇨제 복용 중"):
        extras["diuretic"] = True
    st.markdown("**투석 환자 식이 주의(요약):** 고칼륨(바나나, 오렌지, 토마토 등), 고인(콩류/견과, 유제품 일부) 과다 섭취 주의. 수분·나트륨 조절.")

elif category == "당뇨 환자":
    st.subheader("🍚 당뇨 지표")
    extras["FPG"] = st.number_input("식전 혈당 (mg/dL)", min_value=0.0, step=1.0)
    extras["PP1h"] = st.number_input("식후 1시간 혈당 (mg/dL)", min_value=0.0, step=1.0)
    extras["PP2h"] = st.number_input("식후 2시간 혈당 (mg/dL)", min_value=0.0, step=1.0)
    extras["HbA1c"] = st.number_input("HbA1c (%)", min_value=0.0, step=0.1, format="%.1f")
    st.markdown("**식이 가이드(요약):** 단순당·당분 음료 줄이고, 식사당 탄수화물 양 일정하게. 저당 간식 선택.")

st.divider()
st.header("3️⃣ 입력 방식 & 수치 입력")

mode = st.radio("입력 방법을 선택하세요", ["개별 입력", "일괄 붙여넣기"], horizontal=True)
labs: Dict[str, Optional[float]] = {k: None for k in ORDER}

if mode == "개별 입력":
    st.markdown("🧪 각 항목을 순서대로 입력하세요. (입력한 항목만 결과에 표시)")
    for k in ORDER:
        labs[k] = st.number_input(k, value=None, placeholder="값 입력", step=STEP_MAP.get(k, 0.1), format=FORMAT_MAP.get(k, "%.1f"))
else:
    st.markdown("🧾 줄바꿈 또는 쉼표로 구분하여 순서대로 붙여넣으세요.")
    st.code(", ".join(ORDER), language="text")
    raw = st.text_area("값을 순서대로 입력 (줄바꿈/쉼표 가능)", height=180, placeholder="예) 5.2, 11.8, 180, 1200, ...")
    tokens = []
    s = (raw or "").replace("，", ",").replace("\r\n", "\n").replace("\r", "\n").strip("\n ")
    if s:
        if ("," in s) and ("\n" not in s):
            tokens = [tok.strip() for tok in s.split(",")]
        else:
            tokens = [line.strip() for line in s.split("\n")]
    for i, k in enumerate(ORDER):
        try:
            v = tokens[i] if i < len(tokens) else ""
            labs[k] = float(v) if v != "" else None
        except Exception:
            labs[k] = None

# ----------------------------- Run -----------------------------
st.divider()
st.header("4️⃣ 해석 실행 및 결과")
run = st.button("🔎 해석하기", use_container_width=True)

if run:
    st.subheader("📋 해석 결과")
    summary = interpret_labs(labs)
    if summary:
        for line in summary:
            st.write(line)
    else:
        st.info("입력된 수치가 없습니다. 하나 이상 입력해주세요.")

    foods = food_suggestions(labs)
    if foods:
        st.markdown("### 🥗 음식 가이드")
        for f in foods:
            st.write("- " + f)

    if category == "항암치료" and meds:
        st.markdown("### 💊 항암제 부작용·상호작용 요약")
        for line in summarize_meds(meds):
            st.write(line)

    if category == "항생제" and extras.get("Antibiotics"):
        st.markdown("### 🧪 항생제 주의 요약")
        for a in extras["Antibiotics"]:
            st.write(f"• {a}: {', '.join(ABX_GUIDE[a])}")

    st.markdown("### 🌡️ 발열 가이드")
    st.write(FEVER_GUIDE)
    st.write(ANTIPYRETIC_TIPS)

    # 간단 ANC 500 도달일 추정
    eta_text = None
    if name and HAS_PD and st.session_state.records.get(name):
        eta = estimate_anc_500_date(st.session_state.records[name])
        if eta:
            eta_text = f"예상 ANC 500 도달일: **{eta}** (단순 추정)"
    if eta_text:
        st.success(eta_text)

    # 보고서 (md/txt/선택적 pdf)
    report_lines = []
    report_lines.append(f"# BloodMap 보고서 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    report_lines.append(f"- 카테고리: {category}")
    report_lines.append(f"- 검사일: {test_date}")
    if name: report_lines.append(f"- 별명: {name}")
    report_lines.append("\n## 입력 수치")
    for k in ORDER:
        v = labs.get(k)
        if entered(v):
            report_lines.append(f"- {k}: {v}")
    report_text = "\n".join(report_lines) + "\n\n" + "**추가 정보**\n" + "\n".join([f"- {k}: {v}" for k,v in extras.items() if v not in (None, "", False)]) + "\n\n" + FEVER_GUIDE + "\n\n" + "제작자: Hoya/GPT · 자문: Hoya/GPT\n"

    st.download_button("📥 보고서(.md) 다운로드", data=report_text.encode("utf-8"),
                       file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                       mime="text/markdown")
    st.download_button("📥 보고서(.txt) 다운로드", data=report_text.encode("utf-8"),
                       file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                       mime="text/plain")
    if HAS_PDF:
        pdf_bytes = build_report_pdf(report_text)
        st.download_button("📥 보고서(.pdf) 다운로드", data=pdf_bytes,
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                           mime="application/pdf")
    else:
        st.caption("PDF 다운로드는 reportlab 설치 시 활성화됩니다. (한글이 깨지면 시스템에 Nanum/Noto/AppleSD 고딕 폰트가 필요해요)")

    if name:
        if st.checkbox("📝 이 별명으로 저장", value=True):
            rec = {
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "category": category,
                "labs": {k: v for k, v in labs.items() if entered(v)},
                "meds": meds,
                "extras": extras
            }
            st.session_state.records.setdefault(name, []).append(rec)
            st.success("저장되었습니다. 아래 그래프에서 추이를 확인하세요.")
    else:
        st.info("별명을 입력하면 추이 그래프를 사용할 수 있어요.")

# ----------------------------- Graphs -----------------------------
st.markdown("---")
st.subheader("📈 별명별 추이 그래프 (WBC, Hb, PLT, CRP, ANC)")
if not HAS_PD:
    st.info("그래프는 pandas 설치 시 활성화됩니다. (pip install pandas)")
else:
    if st.session_state.records:
        sel = st.selectbox("별명 선택", sorted(st.session_state.records.keys()))
        rows = st.session_state.records.get(sel, [])
        if rows:
            data = [{
                "ts": r["ts"],
                **{k: r.get("labs", {}).get(k) for k in ["WBC","Hb","PLT","CRP","ANC"]}
            } for r in rows]
            df = pd.DataFrame(data).set_index("ts")
            st.line_chart(df.dropna(how="all"))
        else:
            st.info("선택한 별명의 저장 기록이 없습니다.")
    else:
        st.info("아직 저장된 기록이 없습니다.")

st.markdown("---")
st.caption(f"뷰 카운트(세션): {st.session_state.view_count} · v2.9 (카테고리 상단 이동 적용)")

