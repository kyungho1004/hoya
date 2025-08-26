
import math, os, json, base64, hashlib, time
from datetime import datetime, date
from io import BytesIO
import streamlit as st

# ========== Optional libraries ==========
try:
    import pandas as pd
    HAS_PD = True
except Exception:
    HAS_PD = False

try:
    import qrcode
    HAS_QR = True
except Exception:
    HAS_QR = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    HAS_PDF = True
except Exception:
    HAS_PDF = False

# ========== Page & Globals ==========
st.set_page_config(page_title="피수치 자동 해석기 by Hoya", layout="centered")
st.title("🩸 피수치 자동 해석기")
st.markdown("👤 **제작: Hoya / 자문·개발: GPT**  |  **v2.8-public (혈액암 유형별 약물 분리)**")

APP_URL = st.secrets.get("APP_URL", os.getenv("APP_URL", "https://hoya12.streamlit.app"))
CORE_SEED = st.secrets.get("CORE_SEED", os.getenv("CORE_SEED", "HoyaCoreSeed-ChangeMe"))
ADMIN_PIN = st.secrets.get("ADMIN_PIN", os.getenv("ADMIN_PIN", "2468"))  # 관리자만 내부 보기

def build_signature(name, dte, version="v2.8"):
    base = f"{name}|{dte}|{version}|{CORE_SEED}"
    return hashlib.sha256(base.encode()).hexdigest()[:12]

def _decode_table(b64txt:str, key:str)->dict:
    try:
        raw = base64.b64decode(b64txt.encode()).decode()
        mixed = "".join(chr(ord(c) ^ (ord(key[i % len(key)]) & 0x0F)) for i, c in enumerate(raw))
        return json.loads(mixed)
    except Exception:
        return {}

# Session
if "views" not in st.session_state: st.session_state.views = 0
st.session_state.views += 1
if "records" not in st.session_state: st.session_state.records = {}
if "custom_refs" not in st.session_state: st.session_state.custom_refs = {}

# Sidebar — 공개 모드 알림 + 관리자 PIN
with st.sidebar:
    st.info(f"🔓 공개 모드: 비밀번호 없이 사용 가능\n(관리자 설정/소스는 PIN 필요)\n앱 링크: {APP_URL}")
    if "admin_ok" not in st.session_state: st.session_state.admin_ok = False
    if not st.session_state.admin_ok:
        pin = st.text_input("관리자 PIN", type="password", help="관리자만 내부 규칙 열람 가능 (기본 2468)")
        if st.button("관리자 로그인"):
            if pin == ADMIN_PIN:
                st.session_state.admin_ok = True
                st.success("관리자 모드 ON")
            else:
                st.error("PIN 불일치")
    else:
        st.success("관리자 모드 ON")
        if st.button("관리자 로그아웃"): st.session_state.admin_ok = False

# ========== Easy Dictionary & Ranges ==========
EASY_DICT = {
    "WBC": "백혈구 (감염과 싸우는 군사)",
    "Hb": "혈색소 (산소 운반)",
    "PLT": "혈소판 (피 멈춤)",
    "ANC": "호중구 (감염 막는 핵심 백혈구)",
    "Na": "나트륨 (소금 성분)",
    "K": "칼륨 (심장·근육 전해질)",
    "Albumin": "알부민 (영양/컨디션 단백질)",
    "Glucose": "혈당 (피 속 당)",
    "CRP": "염증 수치",
    "AST": "간 수치(AST)",
    "ALT": "간 수치(ALT)",
    "BUN": "요소질소 (신장)",
    "Cr": "크레아티닌 (신장)",
    "HbA1c": "당화혈색소 (3개월 평균 혈당)"
}

def get_ranges(is_pediatric: bool = False):
    if is_pediatric:
        return {"WBC": (5.0,14.5),"Hb":(11.5,15.0),"PLT":(150,450),
                "ANC":(1500,8000),"Na":(135,145),"K":(3.5,5.1),
                "Albumin":(3.5,5.2),"Glucose":(70,140),"CRP":(0,0.5)}
    else:
        return {"WBC": (4.0,10.0),"Hb":(12.0,16.0),"PLT":(150,400),
                "ANC":(1500,8000),"Na":(135,145),"K":(3.5,5.1),
                "Albumin":(3.5,5.2),"Glucose":(70,199),"CRP":(0,0.5)}

def effective_range(key, is_ped):
    base = get_ranges(is_ped).get(key)
    cust = st.session_state.custom_refs.get(key)
    return cust if cust else base

def easy_label(key):
    base = EASY_DICT.get(key, key)
    return f"{key} · {base}" if base and key != base else base

# ========== Med Dictionaries (defaults) ==========
ANTICANCER = {
    # heme baseline
    "6-MP":{"alias":"6-머캅토퓨린","aes":["골수억제","간수치 상승","구내염","오심"],"warn":["황달/진한 소변 시 진료","감염 징후 즉시 연락"],"ix":["알로푸리놀 감량 필요","와파린 효과 변동"]},
    "MTX":{"alias":"메토트렉세이트","aes":["골수억제","간독성","신독성","구내염","광과민"],"warn":["탈수 시 독성↑","고용량 후 류코보린"],"ix":["NSAIDs/TMP-SMX 독성↑","일부 PPI 상호작용"]},
    "ATRA":{"alias":"트레티노인","aes":["분화증후군","발열","피부/점막 건조","두통"],"warn":["분화증후군 의심 시 즉시 병원"],"ix":["테트라사이클린계/가성뇌종양"]},
    "ARA-C":{"alias":"시타라빈","aes":["골수억제","발열","구내염","(HDAC) 신경독성"],"warn":["HDAC 시 신경증상 즉시 보고"],"ix":[]},
    "G-CSF":{"alias":"그라신","aes":["골통/근육통","주사부위 반응","드물게 비장비대"],"warn":["좌상복부 통증 시 평가"],"ix":[]},
    "Hydroxyurea":{"alias":"하이드록시우레아","aes":["골수억제","피부색소침착","궤양"],"warn":["임신 회피"],"ix":[]},
    "Daunorubicin":{"alias":"도우노루비신","aes":["골수억제","심독성","점막염"],"warn":["누적용량 심기능"],"ix":[]},
    "Idarubicin":{"alias":"이달루비신","aes":["골수억제","심독성","점막염"],"warn":["심기능"],"ix":[]},
    "Mitoxantrone":{"alias":"미토잔트론","aes":["골수억제","심독성","청록색 소변"],"warn":["심기능"],"ix":[]},
    "Cyclophosphamide":{"alias":"사이클로포스파미드","aes":["골수억제","출혈성 방광염","탈모"],"warn":["수분섭취·메스나"],"ix":[]},
    "Etoposide":{"alias":"에토포사이드","aes":["골수억제","저혈압(주입)"],"warn":[],"ix":[]},
    "Topotecan":{"alias":"토포테칸","aes":["골수억제","설사"],"warn":[],"ix":[]},
    "Fludarabine":{"alias":"플루다라빈","aes":["면역억제","감염 위험↑","혈구감소"],"warn":["PCP 예방 고려"],"ix":[]},
    "Vincristine":{"alias":"빈크리스틴","aes":["말초신경병증","변비/장폐색"],"warn":["IT 투여 금지"],"ix":[]},
    # solid tumor common
    "Cisplatin":{"alias":"시스플라틴","aes":["신독성","오심/구토","신경병증"],"warn":["수액 충분+신기능 모니터"],"ix":[]},
    "Carboplatin":{"alias":"카보플라틴","aes":["골수억제","혈소판감소"],"warn":["신기능·용량계산(AUC)"],"ix":[]},
    "Paclitaxel":{"alias":"파클리탁셀","aes":["말초신경병증","과민반응","탈모"],"warn":["프리메디케이션"],"ix":[]},
    "Nab-Paclitaxel":{"alias":"나노입자 파클리","aes":["말초신경병증","골수억제"],"warn":[],"ix":[]},
    "Docetaxel":{"alias":"도세탁셀","aes":["부종","점막염","무과립구열"],"warn":["스테로이드 전처치"],"ix":[]},
    "Doxorubicin":{"alias":"독소루비신","aes":["심독성","골수억제"],"warn":["누적용량·심기능"],"ix":[]},
    "5-FU":{"alias":"플루오로우라실","aes":["구내염","설사","수족증후군"],"warn":["DPD 결핍 시 중증독성"],"ix":[]},
    "Leucovorin":{"alias":"류코보린","aes":["드물게 알레르기"],"warn":["5-FU 보조로 사용"],"ix":[]},
    "Capecitabine":{"alias":"카페시타빈","aes":["수족증후군","설사"],"warn":["신기능에 따라 감량"],"ix":[]},
    "Irinotecan":{"alias":"이리노테칸","aes":["설사(급성/지연)","골수억제"],"warn":["아트로핀·지사제"],"ix":[]},
    "Oxaliplatin":{"alias":"옥살리플라틴","aes":["말초감각이상","급성 한랭유발"],"warn":["찬음식/공기 주의"],"ix":[]},
    "Gemcitabine":{"alias":"젬시타빈","aes":["골수억제","발열/오한","간효소 상승"],"warn":["감염 증상 모니터"],"ix":[]},
    "Pemetrexed":{"alias":"페메트렉시드","aes":["골수억제","피부발진"],"warn":["엽산/비타민B12 보충","스테로이드 전처치"],"ix":[]},
    "Temozolomide":{"alias":"테모졸로마이드","aes":["골수억제","오심/구토"],"warn":["PCP 예방 고려(스테로이드 병용 시)"],"ix":[]},
    "Ifosfamide":{"alias":"이포스파미드","aes":["신경독성","신독성","출혈성 방광염"],"warn":["메틸렌블루 고려(신경독성)","메스나·수분"],"ix":[]},
    "Bleomycin":{"alias":"블레오마이신","aes":["폐독성","피부반응"],"warn":["누적용량·폐기능 모니터"],"ix":[]},
    "Melphalan":{"alias":"멜팔란","aes":["골수억제","구내염"],"warn":[],"ix":[]},
    "Busulfan":{"alias":"부설판","aes":["골수억제","폐섬유화"],"warn":["치료적약물농도(TDM) 고려"],"ix":[]},
    "Procarbazine":{"alias":"프로카바진","aes":["MAO 억제작용","오심/구토"],"warn":["티라민 음식 주의"],"ix":[]},
    "S-1":{"alias":"에스원","aes":["구내염","설사","수족증후군"],"warn":["신기능에 따라 감량"],"ix":[]},
    # heme expansion
    "Cladribine":{"alias":"클라드리빈","aes":["골수억제","감염 위험"],"warn":["열/기침 즉시 연락"],"ix":[]},
    "Clofarabine":{"alias":"클로파라빈","aes":["골수억제","간효소 상승","발열"],"warn":["소아 ALL salvage 독성 모니터"],"ix":[]},
    "Nelarabine":{"alias":"넬라라빈","aes":["신경독성","골수억제"],"warn":["저림/힘빠짐 즉시 보고"],"ix":[]},
    "Asparaginase":{"alias":"엘-아스파라기나제","aes":["간독성","췌장염","혈전"],"warn":["복통/황달/흉통 시 진료"],"ix":[]},
    "Thioguanine":{"alias":"6-TG","aes":["골수억제","간독성","구내염"],"warn":["TPMT/NUDT15 변이 주의"],"ix":[]},
    "Bortezomib":{"alias":"보르테조밉","aes":["말초신경병증","혈소판감소"],"warn":["대상포진 예방 고려"],"ix":[]},
    "Lenalidomide":{"alias":"레날리도마이드","aes":["혈전","혈구감소"],"warn":["임신 금기·항응고 고려"],"ix":[]},
    "Thalidomide":{"alias":"탈리도마이드","aes":["기형유발","진정","혈전"],"warn":["임신 절대 금기"],"ix":[]},
    "Carfilzomib":{"alias":"카르필조밉","aes":["심부전","호흡곤란","혈소판감소"],"warn":["심기능 모니터"],"ix":[]},
    "Venetoclax":{"alias":"베네토클락스","aes":["종양융해","호중구감소"],"warn":["시작 시 TLS 예방"],"ix":[]},
    "Azacitidine":{"alias":"아자시티딘","aes":["골수억제","주사부위 반응"],"warn":["감염 모니터"],"ix":[]},
    "Decitabine":{"alias":"데시타빈","aes":["골수억제","발열"],"warn":["감염 모니터"],"ix":[]},
    "Dexamethasone":{"alias":"덱사메타손","aes":["혈당상승","불면","기분변화"],"warn":["감염 주의·식후 복용"],"ix":[]},
}

IMMUNO_TARGET = {
    "Pembrolizumab":{"alias":"펨브롤리주맙","aes":["면역관련 이상반응(피부, 장, 간, 폐)","갑상선 이상"],"warn":["지속 발열/기침/설사 시 즉시 연락"]},
    "Nivolumab":{"alias":"니볼루맙","aes":["면역관련 이상반응","피부발진","간질성 폐렴"],"warn":["호흡곤란/산소저하 평가"]},
    "Atezolizumab":{"alias":"아테졸리주맙","aes":["면역관련 이상반응","피로","발열"],"warn":["iRAE 의심 시 스테로이드 고려"]},
    "Durvalumab":{"alias":"더발루맙","aes":["면역관련 이상반응","기침/호흡곤란"],"warn":["방사선 폐렴과 감별"]},
    "Osimertinib":{"alias":"오시머티닙(EGFR)","aes":["피부발진","설사","QT 연장","간효소 상승"],"warn":["흉통/부정맥/설사 지속 시 진료"]},
    "Alectinib":{"alias":"알렉티닙(ALK)","aes":["변비","근육통","간효소 상승"],"warn":["CK/간수치 모니터"]},
    "Bevacizumab":{"alias":"베바시주맙","aes":["출혈/혈전","고혈압","단백뇨","상처치유 지연"],"warn":["수술 전후 투여간격 준수"]},
    "Trastuzumab":{"alias":"트라스투주맙(HER2)","aes":["심기능 저하"],"warn":["좌심실 기능 정기 평가"]},
    # heme-related targets
    "Rituximab":{"alias":"리툭시맙(anti‑CD20)","aes":["주입 반응","감염 위험","HBV 재활성"],"warn":["투여 전 HBV 검사·감염 예방"]},
    "Imatinib":{"alias":"이미티닙(BCR‑ABL)","aes":["부종","근육통","피로"],"warn":["간효소/심장 모니터"]},
    "Dasatinib":{"alias":"다사티닙(BCR‑ABL)","aes":["흉막삼출","혈소판감소"],"warn":["호흡곤란 시 평가"]},
    "Nilotinib":{"alias":"닐로티닙(BCR‑ABL)","aes":["QT 연장","고혈당"],"warn":["심전도·전해질 모니터"]},
    "Bosutinib":{"alias":"보수티닙(BCR‑ABL)","aes":["설사","간효소 상승"],"warn":["간기능 모니터"]},
}

# === Hematologic subtype-specific med display ===
HEME_GROUPS = {
    "AML": ["ARA-C","Daunorubicin","Idarubicin","Mitoxantrone","Venetoclax","Azacitidine","Decitabine","6-MP","Thioguanine","G-CSF","Hydroxyurea"],
    "ALL": ["Vincristine","Asparaginase","Dexamethasone","MTX","6-MP","Nelarabine","Clofarabine","Thioguanine"],
    "CML": ["Imatinib","Dasatinib","Nilotinib","Bosutinib","Hydroxyurea"],
    "CLL": ["Fludarabine","Cyclophosphamide","Rituximab","Venetoclax"],
    "MDS": ["Azacitidine","Decitabine","Lenalidomide"],
    "MM":  ["Bortezomib","Lenalidomide","Thalidomide","Carfilzomib","Dexamethasone"]
}

# External overrides (optional obfuscated)
OBF_ANTICANCER = st.secrets.get("OBF_ANTICANCER", os.getenv("OBF_ANTICANCER", ""))
OBF_IMMUNO = st.secrets.get("OBF_IMMUNO", os.getenv("OBF_IMMUNO", ""))
OBF_GUARD = st.secrets.get("OBF_GUARDRAILS", os.getenv("OBF_GUARDRAILS", ""))

if OBF_ANTICANCER:
    ANTICANCER = _decode_table(OBF_ANTICANCER, CORE_SEED) or ANTICANCER
if OBF_IMMUNO:
    IMMUNO_TARGET = _decode_table(OBF_IMMUNO, CORE_SEED) or IMMUNO_TARGET

GUARD_THRESH = {
    "Cisplatin": {"CrCl_min": 60},
    "Capecitabine": {"CrCl_min": 30, "CrCl_reduce": 50},
    "Pemetrexed": {"CrCl_min": 45}
}
if OBF_GUARD:
    GUARD_THRESH = _decode_table(OBF_GUARD, CORE_SEED) or GUARD_THRESH

# ========== Helpers & Converters ==========
def mgdl_to_mmol_glucose(v): return round(v/18.0, 2)
def entered(v):
    try: return v is not None and float(v) > 0
    except Exception: return False
def risk_tag(is_risky: bool): return "🟥" if is_risky else "🟩"
def make_easy_sentence(line: str):
    try:
        txt = line.replace("- ","").strip()
        for k, v in EASY_DICT.items():
            txt = txt.replace(f"{k} ", f"{v} ")
            txt = txt.replace(f"{k}:", f"{v}:")
        txt = txt.replace("→", "—").replace("중증 감소","아주 많이 낮음").replace("감소","낮음").replace("상승","높음")
        return "∙ " + txt
    except Exception:
        return line
def mask_name(name: str):
    if not name: return "(미입력)"
    if len(name) == 1: return name + "O"
    return name[0] + "O"*(len(name)-2) + name[-1]

# ========== Calculators ==========
def bsa_mosteller(cm, kg):
    try: return round(math.sqrt((cm*kg)/3600.0), 2)
    except Exception: return None
def bmi_calc(cm, kg):
    try: m = cm/100.0; return round(kg/(m*m), 1)
    except Exception: return None
def crcl_cg(age, kg, scr_mgdl, female=False):
    try:
        val = ((140 - age) * kg) / (72 * scr_mgdl)
        if female: val *= 0.85
        return round(val, 1)
    except Exception: return None
def egfr_ckd_epi_2021(age, female, scr_mgdl):
    try:
        kappa = 0.7 if female else 0.9
        alpha = -0.241 if female else -0.302
        min_scr = min(scr_mgdl/kappa, 1)
        max_scr = max(scr_mgdl/kappa, 1)
        val = 142 * (min_scr**alpha) * (max_scr**(-1.200)) * (0.9938**age)
        if female: val *= 1.012
        return round(val, 1)
    except Exception: return None
def iv_rate_ml_hr(volume_ml, hours):
    try: return round(volume_ml / hours, 1) if hours > 0 else None
    except Exception: return None
def calvert_carboplatin_dose(target_auc: float, gfr: float):
    try: return round(float(target_auc) * (float(gfr) + 25), 1)
    except Exception: return None

# ========== Presets ==========
def preset_apply(preset_name: str):
    if preset_name == "AML":
        st.session_state["main_cat"] = "혈액암"; st.session_state["blood_sub"] = "AML"
        for k in ["ARA-C","Daunorubicin","G-CSF"]: st.session_state[f"med_{k}"] = True
        for s in ["fever","chills"]: st.session_state[f"sym_{s}"] = True
    elif preset_name == "Breast_Paclitaxel":
        st.session_state["main_cat"] = "고형암"; st.session_state["solid_sub"] = "유방암"
        for k in ["Paclitaxel","Doxorubicin","Trastuzumab"]: st.session_state[f"med_{k}"] = True
    elif preset_name == "FOLFOX":
        st.session_state["main_cat"] = "고형암"; st.session_state["solid_sub"] = "대장암"
        for k in ["Oxaliplatin","5-FU","Leucovorin"]: st.session_state[f"med_{k}"] = True
    elif preset_name == "Osimertinib_Lung":
        st.session_state["main_cat"] = "고형암"; st.session_state["solid_sub"] = "폐암"; st.session_state["med_Osimertinib"] = True

# ========== Top Controls ==========
top_left, _, top_right = st.columns([2,1,2])
with top_left:
    st.caption("프리셋: 기본 선택/약물 자동 설정")
    c1,c2,c3,c4 = st.columns(4)
    if c1.button("🧬 AML"): preset_apply("AML"); st.experimental_rerun()
    if c2.button("🎗️ 유방암+Paclitaxel"): preset_apply("Breast_Paclitaxel"); st.experimental_rerun()
    if c3.button("🟦 FOLFOX"): preset_apply("FOLFOX"); st.experimental_rerun()
    if c4.button("🫁 폐암 Osimertinib"): preset_apply("Osimertinib_Lung"); st.experimental_rerun()

with top_right:
    t1,t2,t3,t4,t5 = st.columns(5)
    big = t1.toggle("👀 큰글자", value=False, key="opt_big")
    is_ped = t2.toggle("👶 소아 기준", value=False, key="opt_ped")
    colorblind = t3.toggle("👁️ 색각친화", value=True, key="opt_cb")
    easy_mode = t4.toggle("🧒 쉬운말 모드", value=True, key="opt_easy")
    dark = t5.toggle("🖤 다크모드", value=False, key="opt_dark")

st.markdown("""
<style>
.stMarkdown, .stText, .stDownloadButton, .stButton button {
    font-size:1.08rem;
    line-height:1.7;
}
</style>
""", unsafe_allow_html=True)

if dark:
    st.markdown(\"\"\"<style>body,.stApp {background:#0f1115;color:#e6e6e6}
    .stButton button,.stDownloadButton button {background:#1f2430;color:#e6e6e6;border:1px solid #30364a}
    .stAlert{background:#1b1f2a;border:1px solid #30364a}</style>\"\"\", unsafe_allow_html=True)

mode = st.radio("표시 모드", ["👪 보호자용","🩺 의사용"], horizontal=True, key="mode")

# ========== Patient Info ==========
st.divider(); st.header("1️⃣ 환자 정보")
c1,c2,c3 = st.columns(3)
with c1: nickname = st.text_input("별명(저장/그래프용)", placeholder="예: 홍길동", key="nickname")
with c2: test_date = st.date_input("검사 날짜", value=date.today(), key="test_date")
with c3: temp = st.number_input("체온(℃)", min_value=30.0, max_value=43.0, step=0.1, format="%.1f", key="temp")
bg_note = st.text_input("🧾 Background 메모(선택)", placeholder="예) 2차 항암 D8, 어제부터 설사", key="bg_note")

colp1, colp2, colp3 = st.columns(3)
with colp1: privacy = st.checkbox("🔒 비공개 모드(저장X)", value=False, key="privacy")
with colp2: anon_share = st.checkbox("🫥 익명 공유(별명 마스킹)", value=False, key="anon")
with colp3: unit_toggle = st.selectbox("단위 표시", ["기본", "Glucose mmol/L"], index=0, key="unit")

# ========== Category & Meds ==========
st.divider(); st.header("2️⃣ 카테고리 / 약물")
main_cat = st.radio("질환 카테고리", ["일반 해석","혈액암","고형암","항생제","투석 환자","당뇨 환자"], horizontal=True, key="main_cat")
blood_sub = solid_sub = None
if main_cat == "혈액암":
    blood_sub = st.selectbox("혈액암 유형", ["AML","ALL","CML","CLL","MDS","MM","기타"], index=0, key="blood_sub")
elif main_cat == "고형암":
    solid_sub = st.selectbox("고형암 유형", ["유방암","폐암","대장암","위암","간암","췌장암","난소암","자궁경부암","전립선암","기타"], index=0, key="solid_sub")

meds = {}
if main_cat in ("혈액암","고형암"):
    st.subheader("💊 항암제/면역·표적치료제")
    cols = st.columns(3)
    if main_cat == "혈액암":
        heme_list = HEME_GROUPS.get(blood_sub or "", [])
        if heme_list:
            st.caption(f"혈액암 유형: **{blood_sub}** 전용 약물만 표시합니다.")
            for i, key in enumerate(heme_list):
                with cols[i % 3]:
                    if st.checkbox(f"{key} 사용", key=f"med_{key}"):
                        meds[key] = True
        else:
            st.caption("혈액암 유형을 선택하면 해당 약물만 표시됩니다.")
    else:
        # 고형암: 주요 항암제 전체 표시
        for i, key in enumerate(list(ANTICANCER.keys())):
            with cols[i % 3]:
                if st.checkbox(f"{key} 사용", key=f"med_{key}"):
                    meds[key] = True

    st.markdown("**면역/표적**")
    cols2 = st.columns(3)
    heme_targets = {"Rituximab","Imatinib","Dasatinib","Nilotinib","Bosutinib"}
    for i, key in enumerate(list(IMMUNO_TARGET.keys())):
        if main_cat == "혈액암" and key not in heme_targets:
            continue
        with cols2[i % 3]:
            if st.checkbox(f"{key} 사용", key=f"med_{key}"):
                meds[key] = True

# ========== Lab Inputs ==========
st.divider(); st.header("3️⃣ 혈액 수치 입력")
lc1, lc2 = st.columns(2)
with lc1:
    WBC = st.number_input(easy_label("WBC"), step=0.1, key="lab_WBC")
    Hb = st.number_input(easy_label("Hb"), step=0.1, key="lab_Hb")
    PLT = st.number_input(easy_label("PLT"), step=0.1, key="lab_PLT")
    ANC = st.number_input(easy_label("ANC"), step=1.0, key="lab_ANC")
    Na = st.number_input(easy_label("Na"), step=0.1, key="lab_Na")
    K = st.number_input(easy_label("K"), step=0.1, key="lab_K")
    Albumin = st.number_input(easy_label("Albumin"), step=0.1, key="lab_Albumin")
with lc2:
    Glucose = st.number_input(easy_label("Glucose")+" (mg/dL)", step=1.0, key="lab_Glu")
    AST = st.number_input(easy_label("AST"), step=1.0, key="lab_AST")
    ALT = st.number_input(easy_label("ALT"), step=1.0, key="lab_ALT")
    CRP = st.number_input(easy_label("CRP"), step=0.1, key="lab_CRP")
    Cr = st.number_input(easy_label("Cr"), step=0.1, key="lab_Cr")
    BUN = st.number_input(easy_label("BUN"), step=0.1, key="lab_BUN")
A1c = st.number_input(easy_label("HbA1c")+" (%)", step=0.1, format="%.1f", key="lab_A1c")

labs = {"WBC": WBC,"Hb": Hb,"PLT": PLT,"ANC": ANC,"Na": Na,"K": K,"Albumin": Albumin,
        "Glucose": Glucose,"AST": AST,"ALT": ALT,"CRP": CRP,"Cr": Cr,"BUN": BUN,"HbA1c": A1c}

# ========== Custom refs ==========
with st.expander("⚙️ 참고범위 커스텀 (선택)"):
    st.caption("입력하면 이 세션 동안 우선 적용됩니다.")
    for key in ["WBC","Hb","PLT","ANC","Na","K","Albumin","Glucose","CRP"]:
        cols = st.columns(3)
        with cols[0]: st.write(f"**{easy_label(key)}**")
        default_lo, default_hi = get_ranges(is_pediatric=st.session_state.get("opt_ped", False)).get(key, (0,0))
        with cols[1]:
            lo = st.number_input(f"{key} 하한", value=float(default_lo), key=f"ref_lo_{key}")
        with cols[2]:
            hi = st.number_input(f"{key} 상한", value=float(default_hi), key=f"ref_hi_{key}")
        st.session_state.custom_refs[key] = (st.session_state[f"ref_lo_{key}"], st.session_state[f"ref_hi_{key}"])

# ========== Symptoms ==========
st.subheader("🧩 증상 체크")
sym_cols = st.columns(8)
symptoms = {
    "fever": sym_cols[0].checkbox("발열(지속)", key="sym_fever"),
    "chills": sym_cols[1].checkbox("오한/떨림", key="sym_chills"),
    "hypotension": sym_cols[2].checkbox("저혈압/어지럼", key="sym_hypo"),
    "confusion": sym_cols[3].checkbox("의식저하/혼돈", key="sym_conf"),
    "dyspnea": sym_cols[4].checkbox("호흡곤란", key="sym_dysp"),
    "diarrhea": sym_cols[5].checkbox("설사/탈수", key="sym_diarr"),
    "mucositis": sym_cols[6].checkbox("구내염/통증", key="sym_mucositis"),
    "rash": sym_cols[7].checkbox("피부발진/가려움", key="sym_rash"),
}
extra_cols = st.columns(2)
symptoms["neuropathy"] = extra_cols[0].checkbox("손발저림/감각이상", key="sym_neuro")
symptoms["nausea"] = extra_cols[1].checkbox("오심/구토", key="sym_nv")

# ========== Interpret Core ==========
def interpret_labs(l, is_ped=False):
    out = []; risky_count = 0
    R = {
        "WBC": effective_range("WBC", is_ped) or (4.0,10.0),
        "Hb": effective_range("Hb", is_ped) or (12.0,16.0),
        "PLT": effective_range("PLT", is_ped) or (150,400),
        "ANC": effective_range("ANC", is_ped) or (1500,8000),
        "Na": effective_range("Na", is_ped) or (135,145),
        "K": effective_range("K", is_ped) or (3.5,5.1),
        "Albumin": effective_range("Albumin", is_ped) or (3.5,5.2),
        "Glucose": effective_range("Glucose", is_ped) or (70,199),
        "CRP": effective_range("CRP", is_ped) or (0,0.5)
    }
    def add(label, txt, risky=False, val=None):
        nonlocal risky_count
        badge = risk_tag(risky)
        out.append(f"- {badge} {label}{(' ' + str(val)) if val is not None else ''}: {txt}")
        if risky: risky_count += 1

    if entered(l.get("WBC")):
        v = l["WBC"]; lo, hi = R["WBC"]
        if v < lo: add("WBC","낮음 → 감염 위험↑",True,v)
        elif v > hi: add("WBC","높음 → 감염/염증 가능",True,v)
        else: add("WBC","정상",False,v)
    if entered(l.get("Hb")):
        v = l["Hb"]; lo, hi = R["Hb"]
        if v < lo: add("Hb","낮음 → 빈혈",True,v)
        elif v > hi: add("Hb","높음",True,v)
        else: add("Hb","정상",False,v)
    if entered(l.get("PLT")):
        v = l["PLT"]; lo, hi = R["PLT"]
        if v < lo: add("혈소판","낮음 → 출혈 위험",True,v)
        elif v > hi: add("혈소판","높음",True,v)
        else: add("혈소판","정상",False,v)
    if entered(l.get("ANC")):
        a = l["ANC"]; lo, _ = R["ANC"]
        if a < 500: add("ANC","중증 감소(<500)",True,a)
        elif a < lo: add("ANC","감소(<1500)",True,a)
        else: add("ANC","정상",False,a)
    if entered(l.get("Albumin")):
        v = l["Albumin"]; lo, hi = R["Albumin"]
        if v < lo: add("Albumin","낮음 → 영양/염증/간질환 가능",True,v)
        elif v > hi: add("Albumin","높음",True,v)
        else: add("Albumin","정상",False,v)
    if entered(l.get("Glucose")):
        g = l["Glucose"]
        if g >= 200: add("Glucose","고혈당(≥200)",True,g)
        elif g < 70: add("Glucose","저혈당(<70)",True,g)
        else: add("Glucose","정상",False,g)
    if entered(l.get("CRP")):
        c = l["CRP"]
        if c > 0.5: add("CRP","상승 → 염증/감염 의심",True,c)
        else: add("CRP","정상",False,c)
    if entered(l.get("Na")) and l["Na"] < 125:
        out.append(f"- 🟥 Na {l['Na']}: 심한 저나트륨 → 신경학적 증상 주의"); risky_count += 1
    if entered(l.get("K")):
        kv = l["K"]
        if kv < 3.0:
            out.append(f"- 🟥 K {kv}: 저칼륨혈증 → 부정맥/근경련 주의"); risky_count += 1
        elif kv > 5.5:
            out.append(f"- 🟥 K {kv}: 고칼륨혈증 → 부정맥 위험"); risky_count += 1
    if entered(l.get("BUN")) and entered(l.get("Cr")) and l["Cr"]>0:
        ratio = l["BUN"]/l["Cr"]
        if ratio > 20: out.append(f"- 🟥 BUN/Cr {ratio:.1f}: 탈수 의심"); risky_count += 1
        elif ratio < 10: out.append(f"- 🟥 BUN/Cr {ratio:.1f}: 간질환/영양 고려"); risky_count += 1
        else: out.append(f"- 🟩 BUN/Cr {ratio:.1f}: 범위 내")
    if entered(l.get("HbA1c")):
        a1c = l["HbA1c"]
        if a1c >= 9.0: out.append(f"- 🟥 HbA1c {a1c}%: 심한 조절 불량, 합병증 위험"); risky_count += 1
        elif a1c >= 8.0: out.append(f"- 🟥 HbA1c {a1c}%: 조절 불량"); risky_count += 1
        elif a1c >= 6.5: out.append(f"- 🟥 HbA1c {a1c}%: 당뇨 범위"); risky_count += 1
        else: out.append(f"- 🟩 HbA1c {a1c}%: 목표 범위에 근접")
    return out, risky_count

def today_actions(l, temp=None):
    tips = []
    if entered(l.get("ANC")) and l["ANC"] < 500:
        if temp is not None and temp >= 38.0:
            tips += ["ANC<500 + 발열: 패혈증 응급, 즉시 병원 연락",
                     "🚨 오한/호흡곤란/저혈압/의식저하 동반 시 즉시 응급실"]
        else:
            tips.append("ANC<500: 외출 자제·마스크 착용, 발열 시 즉시 연락")
    if temp is not None and temp >= 38.5: tips.append("체온 ≥38.5℃: 병원 연락 권고")
    if entered(l.get("Hb")) and l["Hb"] < 8: tips.append("Hb<8: 무리 금지, 어지럼 시 앉거나 눕기")
    if entered(l.get("K")) and l["K"] < 3.0: tips.append("K<3.0: 두근거림/근경련 시 즉시 진료")
    if entered(l.get("K")) and l["K"] > 5.5: tips.append("K>5.5: 심전 이상 위험, 즉시 진료")
    if entered(l.get("Na")) and l["Na"] < 125: tips.append("Na<125: 의식/경련 위험, 즉시 내원")
    if entered(l.get("BUN")) and entered(l.get("Cr")) and l["Cr"]>0 and (l["BUN"]/l["Cr"])>20: tips.append("BUN/Cr>20: 탈수 의심, 물/전해질 보충")
    if entered(l.get("HbA1c")) and l["HbA1c"] >= 8.0: tips.append("A1c↑: 저당 식이·운동·약 조절 상담")
    return tips

def summarize_meds(meds: dict):
    out = []
    for k in meds.keys():
        src = ANTICANCER.get(k) or IMMUNO_TARGET.get(k)
        if not src: continue
        line = f"• {k} ({src['alias']}): AE {', '.join(src.get('aes', []))}"
        if src.get("warn"): line += f" | 주의: {', '.join(src['warn'])}"
        if src.get("ix"): line += f" | 상호작용: {', '.join(src['ix'])}"
        out.append(line)
    return out

def guardrails(meds, crcl, egfr, ast, alt):
    notes = []
    if meds.get("Cisplatin"):
        thr = GUARD_THRESH.get('Cisplatin', {}).get('CrCl_min', 60)
        if crcl is not None and crcl < thr: notes.append("Cisplatin: CrCl 낮음 → **금기/대체 고려** (신독성 위험)")
    if meds.get("Capecitabine"):
        thr_min = GUARD_THRESH.get('Capecitabine', {}).get('CrCl_min', 30)
        thr_reduce = GUARD_THRESH.get('Capecitabine', {}).get('CrCl_reduce', 50)
        if crcl is not None and crcl < thr_min: notes.append("Capecitabine: CrCl <30 → **금기**")
        elif crcl is not None and crcl < thr_reduce: notes.append("Capecitabine: CrCl 30–50 → **감량 고려**")
    if meds.get("Pemetrexed"):
        thr_pem = GUARD_THRESH.get('Pemetrexed', {}).get('CrCl_min', 45)
        if crcl is not None and crcl < thr_pem: notes.append("Pemetrexed: CrCl <45 → **금기**")
        if (ast and ast>3) or (alt and alt>3): notes.append("Pemetrexed: 간효소 상승 시 **독성↑** 주의")
    if (ast and ast>5) or (alt and alt>5): notes.append("간효소(AST/ALT) 매우 높음 → **용량/연기 검토**")
    return notes

# ========== Run Button ==========
st.divider(); st.header("4️⃣ 해석")
run = st.button("🔎 해석하기", use_container_width=True)

if run:
    # Core
    lines, risky_count = interpret_labs(labs, is_ped=st.session_state.get("opt_ped", False))
    severe_by_rules = any(("ANC" in l and "<500" in l) or ("심한 저나트륨" in l) or ("고칼륨" in l) or ("저칼륨" in l) for l in lines)
    severe_by_symptoms = symptoms.get("chills") or symptoms.get("hypotension") or symptoms.get("confusion") or symptoms.get("dyspnea")
    if severe_by_rules or severe_by_symptoms:
        st.error("🚨 응급 주의: 패혈증 의심 증상 또는 중증 수치 이상이 있습니다. 즉시 의료기관과 상의하세요.", icon="🚨")
    elif risky_count > 0:
        st.warning(f"주의: 위험 항목 {risky_count}개 발견. 아래 결과를 확인하세요.")

    actions = today_actions(labs, temp=temp)

    # Core summary card
    st.markdown("### ✅ 핵심 요약")
    core = []
    if actions: core.append(f"🧭 오늘의 조치: {', '.join(actions[:2])}" + (" …" if len(actions)>2 else ""))
    risky_tags = [l.split(':')[0].replace('- ','').strip() for l in lines if '🟥' in l]
    if risky_tags: core.append("위험 항목: " + ", ".join(risky_tags[:3]) + (" …" if len(risky_tags)>3 else ""))
    if labs.get("HbA1c") and labs["HbA1c"] >= 7.0: core.append("🥗 A1c 높음 → 저당 식이 권장")
    st.success("  \n".join(core) if core else "특별한 위험 없음")

    # Layperson vs Pro view
    if st.session_state.get("opt_easy", True):
        st.subheader("📋 결과 (쉬운말)")
        for l in lines: st.write(make_easy_sentence(l))
        st.markdown("### 🧭 오늘 해야 할 일 TOP3")
        todo = actions[:3] if actions else ["특별한 조치 없음"]
        for t in todo: st.write("• " + t)
        fg = []
        if labs.get("Albumin") and labs["Albumin"] < 3.5: fg.append("알부민 낮음 → 달걀·연두부·흰살생선·닭가슴살·귀리죽")
        if labs.get("K") and labs["K"] < 3.5: fg.append("칼륨 낮음 → 바나나·감자·호박죽·고구마·오렌지")
        if labs.get("Hb") and labs["Hb"] < 12: fg.append("Hb 낮음 → 소고기·시금치·두부·달걀 노른자·렌틸콩")
        if labs.get("Na") and labs["Na"] < 135: fg.append("나트륨 낮음 → 전해질 음료·미역국·오트밀")
        if labs.get("HbA1c") and labs["HbA1c"] >= 7.0: fg.append("당화혈색소 높음 → 저당 식이·단 음료 제한")
        if labs.get("ANC") and labs["ANC"] < 500: fg.append("호중구 낮음 → 생식 금지, 완전가열, 2시간 지난 음식 금지")
        if fg:
            st.markdown("### 🥗 음식 가이드 (간단)")
            for f in fg: st.write("• " + f)
    else:
        st.subheader("📋 해석 결과(의사용)")
        for l in lines: st.write(l)

    # Units
    if st.session_state.get("unit") == "Glucose mmol/L" and labs.get("Glucose"):
        st.info(f"Glucose 변환: **{mgdl_to_mmol_glucose(labs['Glucose'])} mmol/L** (입력 {labs['Glucose']} mg/dL)")

    # Abnormality Index
    total_rules = 12
    index_pct = int(min(100, max(0, 100 * (risky_count / total_rules))))
    st.markdown("### 📊 이상치 지수")
    st.progress(index_pct/100.0, text=f"{index_pct}%")

    # SBAR
    st.markdown("### 🧾 SBAR 5줄 요약")
    share_name = mask_name(nickname)
    bkg_auto = main_cat + (f"/{blood_sub}" if blood_sub else "") + (f"/{solid_sub}" if solid_sub else "")
    bkg_text = (bg_note or bkg_auto).strip()
    sbar = [
        f"S) {share_name}, {test_date}, 체온 {temp}℃",
        f"B) 배경: {bkg_text}",
        f"A) 평가: "+("; ".join([l.replace('- ','').split(':')[0] for l in lines[:3]]) if lines else "특이소견 없음"),
        f"R) 권고: "+(("; ".join(actions[:3])) if actions else "경과 관찰")
    ]
    st.code("\n".join(sbar), language="markdown")

    # Guardrails (전문가용)
    st.markdown("### 🧷 약물 가드레일")
    with st.expander("신·간기능 기반 경고 보기 (전문가용)"):
        g1,g2,g3,g4 = st.columns(4)
        age = g1.number_input("나이", min_value=1, max_value=120, value=60)
        weight = g2.number_input("체중(kg)", min_value=20.0, max_value=200.0, value=60.0, step=0.1)
        female = g3.checkbox("여성", value=False)
        scr_v = g4.number_input("혈청 Cr (mg/dL)", min_value=0.1, max_value=10.0, value=float(labs.get("Cr") or 1.0), step=0.1)
        crcl = crcl_cg(age, weight, scr_v, female=female)
        egfr = egfr_ckd_epi_2021(age, female, scr_v)
        st.write(f"- CrCl(Cockcroft–Gault): **{crcl} mL/min** | eGFR(CKD-EPI 2021): **{egfr} mL/min/1.73㎡**")
        notes = guardrails(meds, crcl, egfr, labs.get("AST"), labs.get("ALT"))
        if meds and notes:
            for n in notes: st.write("⚠️ " + n)
        elif meds and not notes:
            st.write("선택된 약물에서 특이 경고 없음 (입력값 기준).")
        else:
            st.write("선택된 항암/면역·표적 약물이 없습니다.")

    # Save record for graphs
    if not privacy and (nickname or "").strip():
        rec = {
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "category": main_cat, "sub": blood_sub if blood_sub else solid_sub,
            "labs": {k: v for k, v in labs.items() if v not in (None, 0, "")},
            "meds": list(meds.keys()), "temp": temp, "date": str(test_date)
        }
        st.session_state.records.setdefault(nickname, []).append(rec)
        st.success("저장되었습니다. 아래 그래프/공유에서 활용하세요.")
    elif privacy:
        st.info("비공개 모드: 저장하지 않았습니다.")

    # Slim summary + QR (+ app link)
    st.markdown("### 🧾 슬림 요약 & 공유")
    core1 = ("🚨 " + actions[0]) if actions else "특별한 위험 없음"
    slim_lines = [
        f"{share_name}",
        f"[{test_date}] {main_cat}{('/'+blood_sub) if blood_sub else (('/'+solid_sub) if solid_sub else '')}",
        f"{core1}",
        f"앱 바로가기: {APP_URL}"
    ]
    st.text_area("3줄 요약 (복사용)", value="\n".join(slim_lines), height=120)
    signature = build_signature(share_name, test_date)
    qr_bytes = None
    if HAS_QR:
        img = qrcode.make("\n".join(slim_lines) + f"\nSIG:{signature}")
        buf = BytesIO(); img.save(buf, format="PNG"); qr_bytes = buf.getvalue()
        st.download_button("📥 QR(PNG) 다운로드", data=qr_bytes, file_name="bloodmap_summary_qr.png", mime="image/png")
    else:
        st.info("QR 이미지를 만들 도구가 없어 텍스트만 제공합니다.")

    # PDF export with watermark + link + SIG
    st.markdown("### 📥 PDF 보고서")
    if HAS_PDF:
        pdf_buf = BytesIO()
        title = "BloodMap Report (v2.8-public)"
        summary_lines = [
            f"Name: {share_name}",
            f"Date: {test_date}",
            f"Category: {main_cat}{('/'+blood_sub) if blood_sub else (('/'+solid_sub) if solid_sub else '')}",
            f"Temperature: {temp}°C",
            "-"*40,
            "Key findings:",
        ] + [l.replace("- ","") for l in lines[:12]] + [
            "-"*40,
            "Today's actions: " + (", ".join(actions) if actions else "None"),
        ]

        c = rl_canvas.Canvas(pdf_buf, pagesize=A4)
        W, H = A4
        x_margin, y_margin = 20*mm, 20*mm
        y = H - y_margin
        c.setFont("Helvetica-Bold", 16)
        c.drawString(x_margin, y, title); y -= 10*mm
        c.setFont("Helvetica", 10)
        for line in summary_lines:
            for chunk in [line[i:i+90] for i in range(0, len(line), 90)]:
                c.drawString(x_margin, y, chunk); y -= 6*mm
                if y < 40*mm: c.showPage(); y = H - y_margin; c.setFont("Helvetica", 10)
        y -= 4*mm
        c.setFont("Helvetica-Bold", 12); c.drawString(x_margin, y, "SBAR"); y -= 8*mm
        c.setFont("Helvetica", 10)
        for line in sbar:
            c.drawString(x_margin, y, line); y -= 6*mm
            if y < 40*mm: c.showPage(); y = H - y_margin; c.setFont("Helvetica", 10)
        # QR
        if qr_bytes:
            try:
                img = ImageReader(BytesIO(qr_bytes))
                c.drawImage(img, W - 45*mm, 20*mm, 35*mm, 35*mm, preserveAspectRatio=True, mask='auto')
                c.setFont("Helvetica", 8)
                c.drawRightString(W - 10*mm, 18*mm, "Slim summary (QR)")
            except Exception:
                pass
        # Footer watermark & link & SIG
        c.setFont("Helvetica", 8)
        c.drawString(20*mm, 15*mm, "© Hoya – Private Use Only")
        c.drawRightString(W - 20*mm, 15*mm, f"SIG:{signature}")
        c.drawString(20*mm, 12*mm, f"App: {APP_URL}")
        c.showPage(); c.save()

        st.download_button("PDF 다운로드", data=pdf_buf.getvalue(),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                           mime="application/pdf")
    else:
        st.info("PDF 모듈(reportlab)을 사용할 수 없어 텍스트·QR만 제공됩니다.")

# ========== Glossary & Graphs ==========
st.markdown("---")
st.subheader("📘 쉬운말 용어 사전")
with st.expander("용어 펼치기"):
    for k, v in EASY_DICT.items():
        st.write(f"- **{k}**: {v}")

st.subheader("📈 별명별 추이 그래프 (WBC, Hb, PLT, CRP, ANC)")
if not HAS_PD:
    st.info("그래프/CSV 기능은 pandas 설치 시 활성화됩니다.")
else:
    if st.session_state.records:
        sel = st.selectbox("별명 선택", sorted(st.session_state.records.keys()), key="sel_name")
        rows = st.session_state.records.get(sel, [])
        if rows:
            data = [{"ts": r["ts"], **{k: r["labs"].get(k) for k in ["WBC","Hb","PLT","CRP","ANC"]}} for r in rows]
            df = pd.DataFrame(data).set_index("ts")
            st.line_chart(df.dropna(how="all"))
        else:
            st.info("선택한 별명의 저장 기록이 없습니다.")

# ========== CSV Import/Export ==========
st.markdown("---")
st.subheader("🗂️ 기록 CSV 내보내기/불러오기")
if HAS_PD and st.session_state.records:
    rows = []
    for who, recs in st.session_state.records.items():
        for r in recs:
            flat = {"별명": who, "ts": r["ts"], "category": r.get("category",""),
                    "sub": r.get("sub",""), "date": r.get("date","")}
            flat.update(r.get("labs", {}))
            rows.append(flat)
    df_all = pd.DataFrame(rows)
    st.download_button("📤 기록 CSV 다운로드", df_all.to_csv(index=False).encode("utf-8"),
                       "bloodmap_records.csv", "text/csv")
uploaded = st.file_uploader("📥 기록 CSV 불러오기", type=["csv"], key="csv_up")
if uploaded is not None and HAS_PD:
    try:
        df_up = pd.read_csv(uploaded)
        cnt = 0
        for _, row in df_up.iterrows():
            who = str(row.get("별명",""))
            if not who: continue
            labs_row = {k: row[k] for k in ["WBC","Hb","PLT","ANC","Na","K","Albumin","Glucose","CRP","AST","ALT","BUN","Cr","HbA1c"] if k in row and pd.notna(row[k])}
            rec = {
                "ts": str(row.get("ts", "")),
                "category": row.get("category",""),
                "sub": row.get("sub",""),
                "labs": labs_row,
                "meds": [],
                "date": str(row.get("date",""))
            }
            st.session_state.records.setdefault(who, []).append(rec)
            cnt += 1
        st.success(f"CSV 가져오기 완료: {cnt}개 레코드 추가")
    except Exception as e:
        st.warning(f"CSV 파싱 중 오류: {e}")

# ========== Admin-only Internals View ==========
if st.session_state.get("admin_ok", False):
    with st.expander("🧩 내부 규칙/임계값/프리셋 (ADMIN)"):
        st.write("• Guardrail thresholds:", GUARD_THRESH)
        st.write("• 항암제 개수:", len(ANTICANCER), " / 면역·표적:", len(IMMUNO_TARGET))
        st.write("• 참고범위(현재 세션 사용치):", st.session_state.custom_refs)
else:
    st.caption("ⓘ 내부 규칙과 임계값은 비공개 처리되었습니다.")

# Footer
st.caption("✅ 모바일 줄꼬임 방지 / 위→아래 고정 배열.  |  방문 카운트(세션): " + str(st.session_state["views"]))
st.caption("🔏 © Hoya – 무단 복제·재배포 금지 | 관리자 PIN 필요 (내부 규칙 전용)")
