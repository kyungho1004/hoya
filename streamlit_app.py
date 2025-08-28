from datetime import datetime, date
import os
import streamlit as st

# ===== Optional deps =====
try:
    import pandas as pd
    HAS_PD = True
except Exception:
    HAS_PD = False

# PDF generation (optional)
try:
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.units import mm
    HAS_PDF = True
except Exception:
    HAS_PDF = False

# For safe text escaping in PDF
from xml.sax.saxutils import escape

# ===== Page config =====
st.set_page_config(page_title="피수치 해석 가이드 by Hoya", layout="centered")
st.title("🩸 피수치 자동 해석기 (v3.7 / Direct Input + 암별·소아·희귀암 패널)")
st.markdown("👤 **제작자: Hoya / 자문: GPT** · 📅 {} 기준".format(date.today().isoformat()))
st.markdown("[📌 **피수치 가이드 공식카페 바로가기**](https://cafe.naver.com/bloodmap)")
st.caption("✅ +버튼 없이 **직접 타이핑 입력** · 모바일 줄꼬임 방지 · PC 표 모드 · **암별/소아/희귀암 패널 지원**")

if "records" not in st.session_state:
    st.session_state.records = {}

ORDER = ["WBC","Hb","PLT","ANC","Ca","P","Na","K","Albumin","Glucose","Total Protein",
         "AST","ALT","LDH","CRP","Cr","UA","TB","BUN","BNP"]

DISCLAIMER = ("※ 본 자료는 보호자의 이해를 돕기 위한 참고용 정보입니다. "
              "진단 및 처방은 하지 않으며, 모든 의학적 판단은 의료진의 권한입니다. "
              "개발자는 이에 대한 판단·조치에 일절 관여하지 않으며, 책임지지 않습니다.")

# ===== Drug dictionaries =====
ANTICANCER = {
    "6-MP":{"alias":"6-머캅토퓨린","aes":["골수억제","간수치 상승","구내염","오심"],
            "warn":["황달/진한 소변 시 진료","감염 징후 즉시 연락"],
            "ix":["알로푸리놀 병용 감량 가능","와파린 효과 변동"]},
    "MTX":{"alias":"메토트렉세이트","aes":["골수억제","간독성","신독성","구내염","광과민"],
           "warn":["탈수 시 독성↑","고용량 후 류코보린"],
           "ix":["NSAIDs/TMP-SMX 병용 독성↑","일부 PPI 상호작용"]},
    "ATRA":{"alias":"트레티노인(베사노이드)","aes":["분화증후군","발열","피부/점막 건조","두통"],
            "warn":["분화증후군 의심 시 즉시 병원"],
            "ix":["테트라사이클린계와 가성뇌종양"]},
    "ARA-C":{"alias":"시타라빈","aes":["골수억제","발열","구내염","(HDAC) 신경독성"],
             "warn":["HDAC 시 신경증상 즉시 보고"],"ix":["효소유도제 상호작용"]},
    "G-CSF":{"alias":"그라신","aes":["골통/근육통","주사부위 반응","드물게 비장비대"],
             "warn":["좌상복부 통증 시 평가"],"ix":[]},
    "Hydroxyurea":{"alias":"하이드록시우레아","aes":["골수억제","피부색소침착","궤양"],
                   "warn":["임신 회피"],"ix":[]},
    "Daunorubicin":{"alias":"도우노루비신","aes":["골수억제","심독성","오심/구토","점막염"],
                    "warn":["누적용량 심기능"],"ix":["심독성↑ 병용 주의"]},
    "Idarubicin":{"alias":"이달루비신","aes":["골수억제","심독성","점막염"],
                  "warn":["심기능"],"ix":[]},
    "Mitoxantrone":{"alias":"미토잔트론","aes":["골수억제","심독성","청록색 소변"],
                    "warn":["심기능"],"ix":[]},
    "Cyclophosphamide":{"alias":"사이클로포스파미드","aes":["골수억제","출혈성 방광염","탈모"],
                        "warn":["수분섭취·메스나"],"ix":["CYP 상호작용"]},
    "Etoposide":{"alias":"에토포사이드","aes":["골수억제","저혈압(주입)"],"warn":[],"ix":[]},
    "Topotecan":{"alias":"토포테칸","aes":["골수억제","설사"],"warn":[],"ix":[]},
    "Fludarabine":{"alias":"플루다라빈","aes":["면역억제","감염 위험↑","혈구감소"],
                   "warn":["PCP 예방 고려"],"ix":[]},
    "Vincristine":{"alias":"빈크리스틴","aes":["말초신경병증","변비/장폐색"],
                   "warn":["IT 투여 금지"],"ix":["CYP3A 상호작용"]},
    # Solid-tumor common
    "Paclitaxel":{"alias":"파클리탁셀","aes":["말초신경병증","호중구감소"],
                  "warn":["과민반응 예방(스테로이드 등)"],"ix":[]},
    "Docetaxel":{"alias":"도세탁셀","aes":["체액저류","호중구감소"],
                 "warn":["전처치 스테로이드"],"ix":[]},
    "Doxorubicin":{"alias":"독소루비신","aes":["심독성","탈모","구내염"],
                   "warn":["누적용량 주의"],"ix":[]},
    "Carboplatin":{"alias":"카보플라틴","aes":["혈구감소","신독성(경미)"],
                   "warn":["Calvert 공식"],"ix":[]},
    "Cisplatin":{"alias":"시스플라틴","aes":["신독성","오심/구토","이독성"],
                 "warn":["수분/항구토제"],"ix":[]},
    "Oxaliplatin":{"alias":"옥살리플라틴","aes":["말초신경병증(냉감 유발)"],
                   "warn":["찬음식/찬바람 주의"],"ix":[]},
    "5-FU":{"alias":"플루오로우라실","aes":["점막염","설사","수족증후군"],
            "warn":["DPD 결핍 주의"],"ix":[]},
    "Capecitabine":{"alias":"카페시타빈","aes":["수족증후군","설사"],
                    "warn":["신기능 따라 감량"],"ix":[]},
    "Gemcitabine":{"alias":"젬시타빈","aes":["혈구감소","발열"],"warn":[],"ix":[]},
    "Pemetrexed":{"alias":"페메트렉시드","aes":["골수억제","피부발진"],
                   "warn":["엽산/비타민B12 보충"],"ix":[]},
    "Irinotecan":{"alias":"이리노테칸","aes":["급성/지연성 설사"],
                  "warn":["로페라미드 지침"],"ix":[]},
    "Trastuzumab":{"alias":"트라스투주맙","aes":["심기능저하"],
                   "warn":["좌심실 기능 모니터"],"ix":[]},
    "Ifosfamide":{"alias":"이포스파미드","aes":["골수억제","신경독성","출혈성 방광염"],
                  "warn":["메스나 병용/수분섭취"],"ix":[]},
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
FEVER_GUIDE = "🌡️ 38.0~38.5℃ 해열제/경과, 38.5℃↑ 병원 연락, 39.0℃↑ 즉시 병원. (ANC<500 동반 발열=응급)"

# ===== Cancer-specific panels =====
CANCER_SPECIFIC = {
    # Blood cancers (labels only; inputs captured as custom extras)
    "AML": [("PT","PT","sec",1),("aPTT","aPTT","sec",1),("Fibrinogen","Fibrinogen","mg/dL",1),
            ("D-dimer","D-dimer","µg/mL FEU",2),("Blasts%","말초 혈액 blasts","%",0)],
    "APL": [("PT","PT","sec",1),("aPTT","aPTT","sec",1),("Fibrinogen","Fibrinogen","mg/dL",1),
            ("D-dimer","D-dimer","µg/mL FEU",2),("DIC Score","DIC Score","pt",0)],
    "ALL": [("PT","PT","sec",1),("aPTT","aPTT","sec",1),("CNS Sx","CNS 증상 여부(0/1)","",0)],
    "CML": [("BCR-ABL PCR","BCR-ABL PCR","%IS",2),("Basophil%","기저호산구(Baso) 비율","%",1)],
    "CLL": [("IgG","면역글로불린 IgG","mg/dL",0),("IgA","면역글로불린 IgA","mg/dL",0),
            ("IgM","면역글로불린 IgM","mg/dL",0)],

    # Pediatric cancers
    "Neuroblastoma": [("VMA","요 VMA","mg/gCr",2),("HVA","요 HVA","mg/gCr",2),("MYCN","MYCN 증폭(0/1)","",0)],
    "Wilms tumor": [("Abd U/S","복부초음파 소견 점수","pt",0),("BP","혈압 백분위수(%)","%",0)],

    # Solid cancers (common)
    "폐암(Lung cancer)": [("CEA","CEA","ng/mL",1),("CYFRA 21-1","CYFRA 21-1","ng/mL",1),("NSE","Neuron-specific enolase","ng/mL",1)],
    "유방암(Breast cancer)": [("CA15-3","CA15-3","U/mL",1),("CEA","CEA","ng/mL",1),("HER2","HER2","IHC/FISH",0),("ER/PR","ER/PR","%",0)],
    "위암(Gastric cancer)": [("CEA","CEA","ng/mL",1),("CA72-4","CA72-4","U/mL",1),("CA19-9","CA19-9","U/mL",1)],
    "대장암(Colorectal cancer)": [("CEA","CEA","ng/mL",1),("CA19-9","CA19-9","U/mL",1)],
    "간암(HCC)": [("AFP","AFP","ng/mL",1),("PIVKA-II","PIVKA-II(DCP)","mAU/mL",0)],
    "췌장암(Pancreatic cancer)": [("CA19-9","CA19-9","U/mL",1),("CEA","CEA","ng/mL",1)],
    "담도암(Cholangiocarcinoma)": [("CA19-9","CA19-9","U/mL",1),("CEA","CEA","ng/mL",1)],
    "자궁내막암(Endometrial cancer)": [("CA125","CA125","U/mL",1),("HE4","HE4","pmol/L",1)],
    "구강암/후두암": [("SCC Ag","SCC antigen","ng/mL",1),("CYFRA 21-1","CYFRA 21-1","ng/mL",1)],
    "피부암(흑색종)": [("S100","S100","µg/L",1),("LDH","LDH","U/L",0)],
    "육종(Sarcoma)": [("ALP","ALP","U/L",0),("CK","CK","U/L",0)],
    "신장암(RCC)": [("CEA","CEA","ng/mL",1),("LDH","LDH","U/L",0)],
    "갑상선암": [("Tg","Thyroglobulin","ng/mL",1),("Anti-Tg Ab","Anti-Tg Ab","IU/mL",1)],
    "난소암": [("CA125","CA125","U/mL",1),("HE4","HE4","pmol/L",1)],
    "자궁경부암": [("SCC Ag","SCC antigen","ng/mL",1)],
    "전립선암": [("PSA","PSA","ng/mL",1)],
    "뇌종양(Glioma)": [("IDH1/2","IDH1/2 mutation","0/1",0),("MGMT","MGMT methylation","0/1",0)],
    "식도암": [("SCC Ag","SCC antigen","ng/mL",1),("CEA","CEA","ng/mL",1)],
    "방광암": [("NMP22","NMP22","U/mL",1),("UBC","UBC","µg/L",1)],

    # Rare cancers
    "담낭암(Gallbladder cancer)": [("CA19-9","CA19-9","U/mL",1),("CEA","CEA","ng/mL",1)],
    "부신암(Adrenal cancer)": [("Cortisol","Cortisol","µg/dL",1),("DHEA-S","DHEA-S","µg/dL",1)],
    "망막모세포종(Retinoblastoma)": [("RB1 mutation","RB1 mutation","0/1",0),("Fundus exam","망막검사 점수","pt",0)],
    "흉선종/흉선암(Thymoma/Thymic carcinoma)": [("AChR Ab","AChR 항체","titer",1),("LDH","LDH","U/L",0)],
    "신경내분비종양(NET)": [("Chromogranin A","CgA","ng/mL",1),("5-HIAA(urine)","5-HIAA(소변)","mg/24h",2)],
    "간모세포종(Hepatoblastoma)": [("AFP","AFP","ng/mL",1)],
    "비인두암(NPC)": [("EBV DNA","EBV DNA","IU/mL",0),("VCA IgA","VCA IgA","titer",1)],
    "GIST": [("KIT mutation","KIT mutation","0/1",0),("PDGFRA mutation","PDGFRA mutation","0/1",0)],
}

# ===== Helpers =====
def _parse_numeric(text, default=0.0, as_int=False, decimals=None):
    if text is None:
        return default
    s = str(text).strip()
    if s == "":
        return default
    s = s.replace(",", "")
    try:
        v = float(s)
        if as_int:
            return int(v)
        if decimals is not None:
            return float(f"{v:.{decimals}f}")
        return v
    except Exception:
        return default

def num_input_generic(label, key, placeholder="", as_int=False, decimals=None):
    raw = st.text_input(label, key=key, placeholder=placeholder, label_visibility="visible")
    return _parse_numeric(raw, as_int=as_int, decimals=decimals)

def entered(v):
    try:
        return v is not None and float(v) != 0
    except Exception:
        return False

def _fmt(name, val):
    try:
        v = float(val)
    except Exception:
        return str(val)
    if name == "CRP":
        return f"{v:.2f}"
    if name in ("WBC","ANC","AST","ALT","LDH","BNP","Glucose"):
        return f"{int(v)}" if v.is_integer() else f"{v:.1f}"
    return f"{v:.1f}"

def interpret_labs(l, extras):
    out=[]
    def add(s): out.append("- " + s)
    if entered(l.get("WBC")):
        v=l["WBC"]; add(f"WBC {_fmt('WBC', v)}: " + ("낮음 → 감염 위험↑" if v<4 else "높음 → 감염/염증 가능" if v>10 else "정상"))
    if entered(l.get("Hb")):
        v=l["Hb"]; add(f"Hb {_fmt('Hb', v)}: " + ("낮음 → 빈혈" if v<12 else "정상"))
    if entered(l.get("PLT")):
        v=l["PLT"]; add(f"혈소판 {_fmt('PLT', v)}: " + ("낮음 → 출혈 위험" if v<150 else "정상"))
    if entered(l.get("ANC")):
        v=l["ANC"]; add(f"ANC {_fmt('ANC', v)}: " + ("중증 감소(<500)" if v<500 else "감소(<1500)" if v<1500 else "정상"))
    if entered(l.get("Albumin")):
        v=l["Albumin"]; add(f"Albumin {_fmt('Albumin', v)}: " + ("낮음 → 영양/염증/간질환 가능" if v<3.5 else "정상"))
    if entered(l.get("Glucose")):
        v=l["Glucose"]; add(f"Glucose {_fmt('Glucose', v)}: " + ("고혈당(≥200)" if v>=200 else "저혈당(<70)" if v<70 else "정상"))
    if entered(l.get("CRP")):
        v=l["CRP"]; add(f"CRP {_fmt('CRP', v)}: " + ("상승 → 염증/감염 의심" if v>0.5 else "정상"))
    if entered(l.get("BUN")) and entered(l.get("Cr")) and l["Cr"]>0:
        ratio=l["BUN"]/l["Cr"]
        if ratio>20: add(f"BUN/Cr {ratio:.1f}: 탈수 의심")
        elif ratio<10: add(f"BUN/Cr {ratio:.1f}: 간질환/영양 고려")
    if extras.get("diuretic_amt", 0) and extras["diuretic_amt"]>0:
        if entered(l.get("Na")) and l["Na"]<135: add("🧂 이뇨제 복용 중 저나트륨 → 어지럼/탈수 주의, 의사와 상의")
        if entered(l.get("K")) and l["K"]<3.5: add("🥔 이뇨제 복용 중 저칼륨 → 심전도/근력저하 주의, 칼륨 보충 식이 고려")
        if entered(l.get("Ca")) and l["Ca"]<8.5: add("🦴 이뇨제 복용 중 저칼슘 → 손저림/경련 주의")
    return out

def food_suggestions(l):
    foods=[]
    if entered(l.get("Albumin")) and l["Albumin"]<3.5: foods.append("알부민 낮음 → " + ", ".join(FOODS["Albumin_low"]))
    if entered(l.get("K")) and l["K"]<3.5: foods.append("칼륨 낮음 → " + ", ".join(FOODS["K_low"]))
    if entered(l.get("Hb")) and l["Hb"]<12: foods.append("Hb 낮음 → " + ", ".join(FOODS["Hb_low"]))
    if entered(l.get("Na")) and l["Na"]<135: foods.append("나트륨 낮음 → " + ", ".join(FOODS["Na_low"]))
    if entered(l.get("Ca")) and l["Ca"]<8.5: foods.append("칼슘 낮음 → " + ", ".join(FOODS["Ca_low"]))
    if entered(l.get("ANC")) and l["ANC"]<500:
        foods.append("🧼 호중구 감소: 생채소 금지, 익혀 섭취, 2시간 지난 음식 금지, 껍질 과일은 의사 상의.")
    foods.append("⚠️ 항암/백혈병 환자는 철분제는 반드시 주치의와 상의(비타민C 병용 시 흡수↑).")
    return foods

def summarize_meds(meds: dict):
    out=[]
    for k, v in meds.items():
        info=ANTICANCER.get(k)
        if not info: 
            continue
        line=f"• {k} ({info['alias']}): AE {', '.join(info['aes'])}"
        if info.get("warn"): line += f" | 주의: {', '.join(info['warn'])}"
        if info.get("ix"): line += f" | 상호작용: {', '.join(info['ix'])}"
        if k == "ARA-C" and isinstance(v, dict) and v.get("form"):
            line += f" | 제형: {v['form']}"
        out.append(line)
    return out

def abx_summary(abx_dict):
    lines=[]
    for k, amt in abx_dict.items():
        try: use=float(amt)
        except Exception: use=0.0
        if use>0:
            tip=", ".join(ABX_GUIDE.get(k, []))
            shown=f"{int(use)}" if float(use).is_integer() else f"{use:.1f}"
            lines.append(f"• {k}: {shown}  — 주의: {tip}")
    return lines

# ===== Pediatrics (everyday/respiratory) =====
PED_TOPICS = ["RSV/모세기관지염","영아 중이염","크룹","구토·설사(탈수)","열경련"]
PED_INPUTS_INFO = (
    "다음 공통 입력은 위험도 배너 산출에 사용됩니다.\n"
    "- 나이(개월), 체온(℃), 호흡수(/분), 산소포화도(%), 24시간 소변 횟수, "
    "함몰/견흔(0/1), 콧벌렁임(0/1), 무호흡(0/1)"
)

def _parse_num_ped(label, key, decimals=1, placeholder=""):
    raw = st.text_input(label, key=key, placeholder=placeholder)
    return _parse_numeric(raw, decimals=decimals)

def ped_risk_banner(age_m, temp_c, rr, spo2, urine_24h, retraction, nasal_flaring, apnea):
    danger=False; urgent=False; notes=[]
    if spo2 and spo2<92: danger=True; notes.append("SpO₂<92%")
    if apnea and apnea>=1: danger=True; notes.append("무호흡")
    if rr and ((age_m and age_m<=12 and rr>60) or (age_m and age_m>12 and rr>50)): urgent=True; notes.append("호흡수 상승")
    if temp_c and temp_c>=39.0: urgent=True; notes.append("고열")
    if retraction and retraction>=1: urgent=True; notes.append("흉곽 함몰")
    if nasal_flaring and nasal_flaring>=1: urgent=True; notes.append("콧벌렁임")
    if urine_24h and urine_24h < max(3, int(24*0.25)): urgent=True; notes.append("소변 감소")
    if danger: st.error("🚑 위급 신호: 즉시 병원/응급실 평가 권고 — " + ", ".join(notes))
    elif urgent: st.warning("⚠️ 주의: 빠른 진료 필요 — " + ", ".join(notes))
    else: st.success("🙂 가정관리 가능 신호(경과관찰). 상태 변화 시 즉시 의료진과 상의")

def ped_topic_tips(topic):
    if topic == "RSV/모세기관지염":
        st.markdown("""**가정관리 핵심**
- 비강흡인/가습, 수분 조금씩 자주. 수유량 ½ 이하로 떨어지면 진료 고려.
- 해열제는 체중기반으로, 과다복용 금지. 기침약은 영아에서 권장되지 않음.
**즉시 진료 신호**: 청색증, 무호흡, SpO₂<92%, 분당 RR>60(12개월 이하), 심한 함몰/콧벌렁임.
""")
    elif topic == "영아 중이염":
        st.markdown("""**가정관리**: 진통·해열, 24–48시간 경과관찰 가능(나이·중증도에 따라).
**경고**: 6개월 미만 고열, 심한 통증/고열 지속, 반복 구토 → 진료.
""")
    elif topic == "크룹":
        st.markdown("""**특징**: 개짖는소리 기침, 흡기때 쌕쌕.
**가정관리**: 안심시키기, 수분, 찬 공기 노출 단시간 도움이 될 수 있음.
**경고**: 휴식 시 흉곽 함몰, 침흘림/삼킴곤란, 청색증 → 응급.
""")
    elif topic == "구토·설사(탈수)":
        st.markdown("""**수분**: ORS 소량·자주(5–10분마다), 우유 일시 감량 고려.
**탈수 신호**: 소변 감소, 눈물 없음, 입 마름, 처짐.
**경고**: 피 섞인 변, 지속 구토로 수분 섭취 불가, 무기력/의식저하 → 진료.
""")
    elif topic == "열경련":
        st.markdown("""**대처**: 측위, 주위 치우기, 시간 측정. 억지로 입에 것 넣지 않기.
**진료 필요**: 5분 이상 지속, 반복, 국소신경학적 징후, 6개월 미만/5세 초과 첫 발생.
""")

# ===== UI 1) Patient / Mode =====
st.divider()
st.header("1️⃣ 환자/암·소아 정보")

c1, c2 = st.columns(2)
with c1:
    nickname = st.text_input("별명(저장/그래프용)", placeholder="예: 홍길동")
with c2:
    test_date = st.date_input("검사 날짜", value=date.today())

mode = st.selectbox("모드 선택", ["일반/암", "소아(일상/호흡기)"])

group = None
cancer = None
if mode == "일반/암":
    group = st.selectbox("암 그룹 선택", ["미선택/일반", "혈액암", "고형암", "소아암", "희귀암"])
    if group == "혈액암":
        cancer = st.selectbox("혈액암 종류", ["AML","APL","ALL","CML","CLL"])
    elif group == "고형암":
        cancer = st.selectbox("고형암 종류", [
            "폐암(Lung cancer)","유방암(Breast cancer)","위암(Gastric cancer)",
            "대장암(Colorectal cancer)","간암(HCC)","췌장암(Pancreatic cancer)",
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
        st.info("암 그룹을 선택하면 해당 암종에 맞는 **항암제 목록과 추가 수치 패널**이 자동 노출됩니다.")
else:
    st.markdown("### 🧒 소아 일상 주제 선택")
    st.caption(PED_INPUTS_INFO)
    ped_topic = st.selectbox("소아 주제", PED_TOPICS)

table_mode = st.checkbox("⚙️ PC용 표 모드(가로형)", help="모바일은 세로형 고정 → 줄꼬임 없음.")

# ===== Drugs & extras =====
meds = {}
extras = {}

if mode == "일반/암" and group and group != "미선택/일반" and cancer:
    st.markdown("### 💊 항암제 입력 (0=미사용, ATRA는 정수)")
    default_drugs_by_group = {
        "혈액암": ["ARA-C","Daunorubicin","Idarubicin","Mitoxantrone","G-CSF","Cyclophosphamide",
                 "Etoposide","Fludarabine","Hydroxyurea","Vincristine","MTX","ATRA"],
        "고형암": ["Carboplatin","Cisplatin","Paclitaxel","Docetaxel","Pemetrexed","Gemcitabine",
                 "5-FU","Doxorubicin","Cyclophosphamide","Trastuzumab","Oxaliplatin","Capecitabine",
                 "Irinotecan","Ifosfamide","Docetaxel","Paclitaxel"],
        "소아암": ["Cyclophosphamide","Ifosfamide","Doxorubicin","Vincristine","Etoposide","Carboplatin",
                 "Cisplatin","Topotecan","Irinotecan"],
        "희귀암": ["Carboplatin","Cisplatin","Paclitaxel","Docetaxel","Gemcitabine","Ifosfamide","Doxorubicin"]
    }
    drug_list = list(dict.fromkeys(default_drugs_by_group.get(group, [])))

    if "ARA-C" in drug_list:
        st.markdown("**ARA-C (시타라빈)**")
        ara_form = st.selectbox("제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"], key="ara_form")
        ara_dose = num_input_generic("용량/일(임의 입력, 0=미사용)", key="ara_dose", decimals=1, placeholder="예: 100")
        if ara_dose > 0:
            meds["ARA-C"] = {"form": ara_form, "dose": ara_dose}
        st.divider()
        drug_list.remove("ARA-C")

    for d in drug_list:
        alias = ANTICANCER.get(d,{}).get("alias","")
        if d == "ATRA":
            amt = num_input_generic(f"{d} ({alias}) - 캡슐 개수(정수, 0=미사용)", key=f"med_{d}", as_int=True, placeholder="예: 2")
        else:
            amt = num_input_generic(f"{d} ({alias}) - 용량/알약 개수(0=미사용)", key=f"med_{d}", decimals=1, placeholder="예: 1.5")
        try:
            if amt and float(amt)>0:
                meds[d] = {"dose_or_tabs": amt}
        except Exception:
            pass

st.markdown("### 🧪 항생제 입력 (0=미사용)")
extras["abx"] = {}
for abx in ["페니실린계","세팔로스포린계","마크롤라이드","플루오로퀴놀론",
            "카바페넴","TMP-SMX","메트로니다졸","반코마이신"]:
    extras["abx"][abx] = num_input_generic(f"{abx} - 복용/주입량 또는 횟수(0=미사용)", key=f"abx_{abx}", decimals=1, placeholder="예: 1")

st.markdown("### 💧 동반 약물/상태")
extras["diuretic_amt"] = num_input_generic("이뇨제(복용량/회/일, 0=미복용)", key="diuretic_amt", decimals=1, placeholder="예: 1")

# ===== UI 2) Inputs =====
st.divider()
if mode == "일반/암":
    st.header("2️⃣ 기본 혈액 검사 수치 (입력한 값만 해석)")
else:
    st.header("2️⃣ 소아 공통 입력")

vals = {}

def render_inputs_vertical():
    st.markdown("**기본 패널**")
    for name in ORDER:
        if name == "CRP":
            vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=2, placeholder="예: 0.12")
        elif name in ("WBC","ANC","AST","ALT","LDH","BNP","Glucose"):
            vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=1, placeholder="예: 1200")
        else:
            vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=1, placeholder="예: 3.5")

def render_inputs_table():
    st.markdown("**기본 패널 (표 모드)**")
    left, right = st.columns(2)
    half = (len(ORDER)+1)//2
    with left:
        for name in ORDER[:half]:
            if name == "CRP":
                vals[name] = num_input_generic(f"{name}", key=f"l_{name}", decimals=2, placeholder="예: 0.12")
            elif name in ("WBC","ANC","AST","ALT","LDH","BNP","Glucose"):
                vals[name] = num_input_generic(f"{name}", key=f"l_{name}", decimals=1, placeholder="예: 1200")
            else:
                vals[name] = num_input_generic(f"{name}", key=f"l_{name}", decimals=1, placeholder="예: 3.5")
    with right:
        for name in ORDER[half:]:
            if name == "CRP":
                vals[name] = num_input_generic(f"{name}", key=f"r_{name}", decimals=2, placeholder="예: 0.12")
            elif name in ("WBC","ANC","AST","ALT","LDH","BNP","Glucose"):
                vals[name] = num_input_generic(f"{name}", key=f"r_{name}", decimals=1, placeholder="예: 1200")
            else:
                vals[name] = num_input_generic(f"{name}", key=f"r_{name}", decimals=1, placeholder="예: 3.5")

if mode == "일반/암":
    if table_mode:
        render_inputs_table()
    else:
        render_inputs_vertical()
else:
    age_m        = _parse_num_ped("나이(개월)", key="ped_age", decimals=0, placeholder="예: 18")
    temp_c       = _parse_num_ped("체온(℃)", key="ped_temp", decimals=1, placeholder="예: 38.2")
    rr           = _parse_num_ped("호흡수(/분)", key="ped_rr", decimals=0, placeholder="예: 42")
    spo2         = _parse_num_ped("산소포화도(%)", key="ped_spo2", decimals=0, placeholder="예: 96")
    urine_24h    = _parse_num_ped("24시간 소변 횟수", key="ped_u", decimals=0, placeholder="예: 6")
    retraction   = _parse_num_ped("흉곽 함몰(0/1)", key="ped_ret", decimals=0, placeholder="0 또는 1")
    nasal_flaring= _parse_num_ped("콧벌렁임(0/1)", key="ped_nf", decimals=0, placeholder="0 또는 1")
    apnea        = _parse_num_ped("무호흡(0/1)", key="ped_ap", decimals=0, placeholder="0 또는 1")

# ===== UI 3) Cancer-specific extras or Pediatric tips =====
extra_vals = {}
if mode == "일반/암" and group and group != "미선택/일반" and cancer:
    items = CANCER_SPECIFIC.get(cancer, [])
    if items:
        st.divider()
        st.header("3️⃣ 암별 디테일 수치")
        st.caption("해석은 주치의 판단을 따르며, 값 기록/공유를 돕기 위한 입력 영역입니다.")
        for key, label, unit, decs in items:
            ph = f"예: {('0' if decs==0 else '0.'+('0'*decs))}" if decs is not None else ""
            val = num_input_generic(f"{label}" + (f" ({unit})" if unit else ""), key=f"extra_{key}", decimals=decs, placeholder=ph)
            extra_vals[key] = val
elif mode == "소아(일상/호흡기)":
    st.divider()
    st.header("3️⃣ 소아 생활 가이드")
    ped_topic_tips(ped_topic)

# ===== Run =====
st.divider()
run = st.button("🔎 해석하기", use_container_width=True)

if run:
    st.subheader("📋 해석 결과")

    if mode == "일반/암":
        lines = interpret_labs(vals, extras)
        for line in lines: st.write(line)

        shown = [ (k, v) for k, v in (extra_vals or {}).items() if entered(v) ]
        if shown:
            st.markdown("### 🧬 암별 디테일 수치")
            for k, v in shown:
                st.write(f"- {k}: {v}")

        fs = food_suggestions(vals)
        if fs:
            st.markdown("### 🥗 음식 가이드")
            for f in fs: st.write("- " + f)
    else:
        ped_risk_banner(age_m, temp_c, rr, spo2, urine_24h, retraction, nasal_flaring, apnea)

    # 항암제 요약
    if meds:
        st.markdown("### 💊 항암제 부작용·상호작용 요약")
        for line in summarize_meds(meds): st.write(line)

    # 항생제 요약
    if extras.get("abx"):
        abx_lines = abx_summary(extras["abx"])
        if abx_lines:
            st.markdown("### 🧪 항생제 주의 요약")
            for l in abx_lines: st.write(l)

    # 발열 가이드
    st.markdown("### 🌡️ 발열 가이드")
    st.write(FEVER_GUIDE)

    # Report build (MD base)
    buf = [f"# BloodMap 보고서 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n",
           f"- 제작자/자문: Hoya / GPT\n",
           "[피수치 가이드 공식카페](https://cafe.naver.com/bloodmap)\n"]
    if mode == "일반/암":
        if group != "미선택/일반":
            buf.append(f"- 암 그룹/종류: {group} / {cancer}\n")
        else:
            buf.append(f"- 암 그룹/종류: 미선택\n")
    else:
        buf.append(f"- 소아 주제: {ped_topic}\n")
    buf.append("- 검사일: {}\n".format(test_date.isoformat()))

    if mode == "일반/암":
        buf.append("\n## 입력 수치(기본)\n")
        for k in ORDER:
            v = vals.get(k)
            if entered(v):
                if k == "CRP": buf.append(f"- {k}: {float(v):.2f}\n")
                else: buf.append(f"- {k}: {_fmt(k, v)}\n")
        if extra_vals:
            buf.append("\n## 암별 디테일 수치\n")
            for k, v in extra_vals.items():
                if entered(v): buf.append(f"- {k}: {v}\n")
        if meds:
            buf.append("\n## 항암제 요약\n")
            for line in summarize_meds(meds): buf.append(line + "\n")
    else:
        buf.append("\n## 소아 공통 입력\n")
        def _ent(x):
            try: return x is not None and float(x)!=0
            except: return False
        if _ent(age_m): buf.append(f"- 나이(개월): {int(age_m)}\n")
        if _ent(temp_c): buf.append(f"- 체온: {float(temp_c):.1f}℃\n")
        if _ent(rr): buf.append(f"- 호흡수: {int(rr)}/분\n")
        if _ent(spo2): buf.append(f"- SpO₂: {int(spo2)}%\n")
        if _ent(urine_24h): buf.append(f"- 24시간 소변 횟수: {int(urine_24h)}\n")
        if _ent(retraction): buf.append(f"- 흉곽 함몰: {int(retraction)}\n")
        if _ent(nasal_flaring): buf.append(f"- 콧벌렁임: {int(nasal_flaring)}\n")
        if _ent(apnea): buf.append(f"- 무호흡: {int(apnea)}\n")

    if extras.get("abx"):
        buf.append("\n## 항생제\n")
        for l in abx_summary(extras["abx"]): buf.append(l + "\n")

    buf.append("\n> " + DISCLAIMER + "\n")
    report_md = "".join(buf)

    # Downloads
    st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"),
                       file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                       mime="text/markdown")

    st.download_button("📄 보고서(.txt) 다운로드", data=report_md.encode("utf-8"),
                       file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                       mime="text/plain")

    if HAS_PDF:
        def md_to_pdf_bytes(md_text: str) -> bytes:
            # Try to register a Korean font if present
            font_registered = False
            font_name = 'NanumGothic'
            for candidate in ['NanumGothic.ttf', 'NotoSansKR-Regular.otf', 'NanumGothic.otf']:
                if os.path.exists(candidate):
                    try:
                        pdfmetrics.registerFont(TTFont(font_name, candidate))
                        font_registered = True
                        break
                    except Exception:
                        pass

            buf_pdf = BytesIO()
            doc = SimpleDocTemplate(buf_pdf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                                    topMargin=15*mm, bottomMargin=15*mm)
            styles = getSampleStyleSheet()
            # Force styles to use Korean-capable font if available
            target_font = font_name if font_registered else styles['BodyText'].fontName
            for s in ['Title','Heading1','Heading2','BodyText']:
                if s in styles.byName:
                    styles[s].fontName = target_font

            story = []
            for line in md_text.splitlines():
                line = line.strip()
                if not line:
                    story.append(Spacer(1, 4*mm))
                    continue
                if line.startswith("# "):
                    p = Paragraph(f"<b>{escape(line[2:])}</b>", styles['Title'])
                elif line.startswith("## "):
                    p = Paragraph(f"<b>{escape(line[3:])}</b>", styles['Heading2'])
                elif line.startswith("- "):
                    p = Paragraph("• " + escape(line[2:]), styles['BodyText'])
                elif line.startswith("> "):
                    p = Paragraph(f"<i>{escape(line[2:])}</i>", styles['BodyText'])
                else:
                    p = Paragraph(escape(line), styles['BodyText'])
                story.append(p)
            doc.build(story)
            return buf_pdf.getvalue()

        pdf_bytes = md_to_pdf_bytes(report_md)
        st.download_button("🖨️ 보고서(.pdf) 다운로드", data=pdf_bytes,
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                           mime="application/pdf")
    else:
        st.info("PDF 변환 모듈(reportlab)을 찾을 수 없어 .pdf 다운로드를 숨겼습니다. 'pip install reportlab' 후 사용 가능합니다.")

    # Save session record
    if nickname and nickname.strip():
        rec = {
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": mode,
            "group": group,
            "cancer": cancer,
            "labs": {k: vals.get(k) for k in ORDER if entered(vals.get(k))},
            "extra": {k: v for k, v in (extra_vals or {}).items() if entered(v)},
            "meds": meds,
            "extras": extras,
        }
        st.session_state.records.setdefault(nickname, []).append(rec)
        st.success("저장되었습니다. 아래 그래프에서 추이를 확인하세요.")
    else:
        st.info("별명을 입력하면 추이 그래프를 사용할 수 있어요.")

# ===== Graphs =====
st.markdown("---")
st.subheader("📈 별명별 추이 그래프 (WBC, Hb, PLT, CRP, ANC)")
if not HAS_PD:
    st.info("그래프는 pandas 설치 시 활성화됩니다. (pip install pandas)")
else:
    if st.session_state.records:
        sel = st.selectbox("별명 선택", sorted(st.session_state.records.keys()))
        rows = st.session_state.records.get(sel, [])
        if rows:
            data = [ {"ts": r["ts"], **{k: r["labs"].get(k) for k in ["WBC","Hb","PLT","CRP","ANC"]}} for r in rows ]
            import pandas as pd  # local import for safety
            df = pd.DataFrame(data).set_index("ts")
            st.line_chart(df.dropna(how="all"))
        else:
            st.info("선택한 별명의 저장 기록이 없습니다.")
    else:
        st.info("아직 저장된 기록이 없습니다.")

# ===== Sticky disclaimer =====
st.caption("📱 직접 타이핑 입력 / 모바일 줄꼬임 방지 / 암별·소아·희귀암 패널 포함. 공식카페: https://cafe.naver.com/bloodmap")
st.markdown("> " + DISCLAIMER)
