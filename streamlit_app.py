# -*- coding: utf-8 -*-
# 피수치 자동 해석기 v2.9 (모바일 최적화 · 풀버전)
# 제작: Hoya/GPT  · 자문: Hoya/GPT
# 주의: 본 앱은 의료 조언이 아닌 보조 도구입니다. 이상 증상/고열 시 즉시 주치의와 상의하세요.

import os
import json
import math
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

import streamlit as st

# --- 앱 기본 설정 (모바일 줄꼬임 방지: 단일 컬럼 · 폼 사용) ---
st.set_page_config(
    page_title="피수치 자동 해석기 v2.9",
    page_icon="🩸",
    layout="centered",
    initial_sidebar_state="collapsed",
)

VERSION = "v2.9"
APP_AUTHOR = "Hoya/GPT"
DATA_DIR = "data"
RESULTS_PATH = os.path.join(DATA_DIR, "results_store.json")
METRICS_PATH = os.path.join(DATA_DIR, "metrics.json")

os.makedirs(DATA_DIR, exist_ok=True)

# ---------- 유틸 ----------
def _now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def parse_float(s: str) -> Optional[float]:
    """빈칸 허용. 숫자가 아니면 None."""
    if s is None:
        return None
    s = str(s).strip().replace(",", "")
    if s == "":
        return None
    try:
        return float(s)
    except Exception:
        return None

@st.cache_resource(show_spinner=False)
def load_json(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path: str, obj) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

# ---------- 조회수 카운터 ----------
def bump_view_counter() -> int:
    metrics = load_json(METRICS_PATH, default={})
    metrics.setdefault("views", 0)
    session_key = "view_bumped"
    if not st.session_state.get(session_key):
        metrics["views"] += 1
        save_json(METRICS_PATH, metrics)
        st.session_state[session_key] = True
    return metrics["views"]

# ---------- 저장소 ----------
def get_store() -> Dict[str, Any]:
    return load_json(RESULTS_PATH, default={})

def save_record(nickname: str, record: Dict[str, Any]) -> None:
    store = get_store()
    store.setdefault(nickname, [])
    store[nickname].append(record)
    save_json(RESULTS_PATH, store)

def get_latest(nickname: str) -> Optional[Dict[str, Any]]:
    store = get_store()
    if nickname in store and store[nickname]:
        return store[nickname][-1]
    return None

def get_series(nickname: str, keys: List[str]) -> Dict[str, List[Tuple[str, Optional[float]]]]:
    store = get_store()
    out = {k: [] for k in keys}
    for rec in store.get(nickname, []):
        ts = rec.get("ts", "?")
        labs = rec.get("labs", {})
        for k in keys:
            out[k].append((ts, labs.get(k)))
    return out

# ---------- 권장 식품 (항목별 5개 고정) ----------
FOODS = {
    "Albumin_low": ["달걀", "연두부", "흰살 생선", "닭가슴살", "귀리죽"],
    "K_low": ["바나나", "감자", "호박죽", "고구마", "오렌지"],
    "Hb_low": ["소고기", "시금치", "두부", "달걀 노른자", "렌틸콩"],
    "Na_low": ["전해질 음료", "미역국", "바나나", "오트밀죽", "삶은 감자"],
    "Ca_low": ["연어 통조림", "두부", "케일", "브로콜리", "참깨 제외"],
    # 확장: 필요 시 키 추가 가능
}

# ---------- 약물 경고 (요약: 화면 / 상세: 보고서) ----------
CHEMO = {
    "6-MP(메르캅토퓨린)": {
        "screen": ["간독성(ALT/AST↑)", "골수억제(빈혈·호중구감소)", "구역/구토"],
        "detail": [
            "간수치 상승 및 황달 가능, 정기 간기능 추적 필요",
            "골수억제(감염·출혈 위험 ↑), 발열 시 즉시 연락",
            "푸린 대사 관련 약물/음식 주의, 생백신 금지",
        ],
    },
    "MTX(메토트렉세이트)": {
        "screen": ["구내염", "간독성", "신독성(고용량)", "광과민"],
        "detail": [
            "구내염 예방: 미지근한 물가글, 자극 음식 피하기",
            "간독성: AST/ALT 상승 시 용량 조정/중단 고려",
            "고용량 시 알칼리화·수액·요중 MTX 모니터",
            "상호작용: NSAIDs·TMP/SMX·프로톤펌프억제제 주의",
        ],
    },
    "베사노이드(ATRA, 트레티노인)": {
        "screen": ["분화증후군(DS)", "두통/피부건조/광과민", "간수치 이상", "설사"],
        "detail": [
            "분화증후군(발열·호흡곤란·부종·저혈압): 즉시 병원 연락",
            "피부·점막 건조, 광과민 — 자외선 차단·보습제",
            "간수치 상승 가능, 정기 추적",
            "설사 발생 시 수분·전해질 보충, 지속 시 진료",
        ],
    },
    "ARA-C(시타라빈)": {
        "screen": ["골수억제", "발열반응", "결막염", "신경독성(HDAC)"],
        "detail": [
            "정맥(IV)/피하(SC)/고용량(HDAC) 제형별 주의 다름",
            "결막염 예방 위해 점안제 병용 권장(프로토콜 따름)",
            "HDAC: 소뇌실조·언어장애 등 신경학적 부작용 모니터",
            "발열/오한 시 감염 평가",
        ],
    },
    "G-CSF(그라신·필그라스팀)": {
        "screen": ["골통/근육통", "일시적 발열", "백혈구↑ 관찰"],
        "detail": [
            "투여 후 뼈 통증 흔함 — 필요 시 진통제",
            "발열 시 감염 여부 우선 평가",
            "WBC/ANC 추세 확인, 과도한 상승 시 일정 조정",
        ],
    },
    # 추가 9종 (간략 키워드 요약)
    "하이드록시우레아": {
        "screen": ["골수억제", "피부색소 변화", "구역"],
        "detail": ["용량-반응성 골수억제, 피부·손발톱 변화"],
    },
    "비크라빈(빈크리스틴 계열)": {
        "screen": ["말초신경병증", "변비", "탈모"],
        "detail": ["말초신경독성 — 감각저하/저림·변비 예방"],
    },
    "도우노루비신": {
        "screen": ["심독성", "점막염", "골수억제"],
        "detail": ["누적용량에 따른 심근독성 — 심기능 추적"],
    },
    "이달루비신": {
        "screen": ["심독성", "골수억제", "탈모"],
        "detail": ["심초음파/BNP 추적 고려"],
    },
    "미토잔트론": {
        "screen": ["심독성", "청록색 소변", "골수억제"],
        "detail": ["색소성 변색 가능, 심독성 모니터"],
    },
    "사이클로포스파마이드": {
        "screen": ["출혈성 방광염", "오심/구토", "골수억제"],
        "detail": ["MESNA·수액으로 방광 보호, 혈뇨 시 즉시 연락"],
    },
    "에토포사이드": {
        "screen": ["저혈압(주입)", "탈모", "골수억제"],
        "detail": ["주입 관련 저혈압 — 투여 속도 조절"],
    },
    "토포테칸": {
        "screen": ["골수억제", "설사", "점막염"],
        "detail": ["호중구감소·설사 시 지연/감량 고려"],
    },
    "플루다라빈": {
        "screen": ["면역억제", "기회감염", "골수억제"],
        "detail": ["PJP 등 감염 예방 요법 고려"],
    },
}

ANTIBIOTICS_INFO = {
    # 세대·분류 구분 없이 일반인 친화 설명
    "레보플록사신": ["광범위 항균제", "힘줄통증 드물게", "광과민 주의"],
    "세프트리악손": ["병원·외래 감염에 흔용", "주사부위 통증"],
    "피페라실린/타조박탐": ["중증 감염에 흔용", "설사·발진"],
    "아목시/클라불란산": ["상기도/치과 감염 흔용", "위장관 부작용"],
    "메트로니다졸": ["혐기성 커버", "음주 금지(섭취 시 반응)"],
}

ANTIPYRETIC_GUIDE = [
    "🔺 38.0~38.5℃: 해열제 복용 후 경과 관찰",
    "🔺 38.5℃ 이상: 병원 연락 권장",
    "🔺 39.0℃ 이상: 즉시 병원 방문",
    "아세트아미노펜/이부프로펜 교차 투여 시 간/신장 부담, 투여 간격-총량 준수",
]

ANC_FOOD_SAFETY = [
    "호중구 낮음: 생채소/생과일(껍질 있는 과일) 피하기",
    "모든 음식은 충분히 가열하거나 전자레인지 30초 이상",
    "멸균·살균식품 권장",
    "조리 후 2시간 지난 음식 섭취 지양",
    "껍질 있는 과일은 주치의와 상의 후 섭취 결정",
]

IRON_WARNINGS = [
    "항암 치료 중이거나 백혈병 환자는 철분제를 복용하지 않는 것이 좋습니다.",
    "철분제와 비타민C를 함께 복용하면 흡수가 촉진됩니다. 하지만 항암 치료 중이거나 백혈병 환자는 반드시 주치의와 상담 후 복용 여부를 결정해야 합니다.",
]

# ---------- 해석 로직 ----------
NORMALS = {
    # 참고범위(일반적 범례), 실제 해석은 경향/상태 기반
    "WBC": (4.0, 10.0),
    "Hb": (12.0, 16.0),
    "PLT": (150.0, 400.0),
    "ANC": (1.5, 7.0),
    "Ca": (8.6, 10.2),
    "P": (2.5, 4.5),
    "Na": (135.0, 145.0),
    "K": (3.5, 5.1),
    "Albumin": (3.5, 5.2),
    "Glucose": (70.0, 140.0),
    "Total Protein": (6.0, 8.3),
    "AST": (0.0, 40.0),
    "ALT": (0.0, 41.0),
    "LDH": (140.0, 280.0),
    "CRP": (0.0, 0.5),
    "Creatinine": (0.5, 1.2),
    "UA": (2.6, 7.2),
    "TB": (0.2, 1.2),
    "BUN": (7.0, 20.0),
    "BNP": (0.0, 100.0),
}

def interpret_value(name: str, val: float) -> Optional[str]:
    lo, hi = NORMALS.get(name, (None, None))
    if lo is None:
        return None
    if val < lo:
        return f"{name} ↓ (정상 {lo}~{hi})"
    if val > hi:
        return f"{name} ↑ (정상 {lo}~{hi})"
    return f"{name} 정상 범위"

def dehydration_flag(bun: Optional[float], cr: Optional[float]) -> Optional[str]:
    if bun is None or cr is None or cr == 0:
        return None
    ratio = bun / cr
    if ratio >= 20:
        return f"탈수 의심 (BUN/Cr={ratio:.1f} ≥ 20) — 수분/전해질 보충 필요"
    return None

def kidney_caution(bun: Optional[float], cr: Optional[float]) -> List[str]:
    msgs = []
    if bun and bun > NORMALS["BUN"][1]:
        msgs.append("BUN 상승 — 단백질 과다 섭취/탈수 점검")
    if cr and cr > NORMALS["Creatinine"][1]:
        msgs.append("Cr 상승 — 신장 기능 저하 가능, 수분·약물 용량 확인")
    return msgs

def liver_caution(ast: Optional[float], alt: Optional[float], ldh: Optional[float]) -> List[str]:
    msgs = []
    if ast and ast > NORMALS["AST"][1]:
        msgs.append("AST 상승 — 간세포 손상 가능")
    if alt and alt > NORMALS["ALT"][1]:
        msgs.append("ALT 상승 — 간독성/염증 가능")
    if ldh and ldh > NORMALS["LDH"][1]:
        msgs.append("LDH 상승 — 조직 손상/용혈 가능")
    return msgs

def build_food_suggestions(labs: Dict[str, Optional[float]]) -> List[str]:
    out = []
    def add(title, key):
        foods = FOODS.get(key, [])
        if foods:
            out.append(f"• {title}: " + ", ".join(foods))
    if labs.get("Albumin") is not None and labs["Albumin"] < NORMALS["Albumin"][0]:
        add("알부민 낮음 — 고단백 식단 권장", "Albumin_low")
    if labs.get("K") is not None and labs["K"] < NORMALS["K"][0]:
        add("칼륨 낮음", "K_low")
    if labs.get("Hb") is not None and labs["Hb"] < NORMALS["Hb"][0]:
        add("Hb 낮음 — 철분 식품 위주 (철분제는 금지)", "Hb_low")
    if labs.get("Na") is not None and labs["Na"] < NORMALS["Na"][0]:
        add("나트륨 낮음 — 저나트륨 교정", "Na_low")
    if labs.get("Ca") is not None and labs["Ca"] < NORMALS["Ca"][0]:
        add("칼슘 낮음 — 뼈 건강 식단", "Ca_low")
    # 확장(혈당/간/신장): 화면 요약에 간략 문장
    if labs.get("Glucose") is not None and labs["Glucose"] > NORMALS["Glucose"][1]:
        out.append("• 혈당 높음 — 저당 식이·식사 기록 권장")
    if (labs.get("BUN") and labs["BUN"] > NORMALS["BUN"][1]) or (labs.get("Creatinine") and labs["Creatinine"] > NORMALS["Creatinine"][1]):
        out.append("• 신장 수치 이상 — 단백질 조절·충분한 수분 섭취")
    if (labs.get("AST") and labs["AST"] > NORMALS["AST"][1]) or (labs.get("ALT") and labs["ALT"] > NORMALS["ALT"][1]):
        out.append("• 간수치 상승 — 기름진 음식/술 회피, 휴식")
    return out

def anc_assessment(anc: Optional[float]) -> List[str]:
    msgs = []
    if anc is None:
        return msgs
    if anc < 0.5:
        msgs.append("중증 호중구감소(ANC < 500): 외출 자제·발열 시 즉시 병원")
        msgs.extend(ANC_FOOD_SAFETY)
    elif anc < 1.0:
        msgs.append("중등도 호중구감소(ANC < 1000): 감염 주의·위생 관리 강화")
        msgs.extend(ANC_FOOD_SAFETY)
    elif anc < 1.5:
        msgs.append("경증 호중구감소(ANC < 1500): 경과 관찰")
    else:
        msgs.append("ANC 정상 범위 내")
    return msgs

def build_med_messages(selected: List[str], ara_c_form: Optional[str], diuretic_on: bool, antibiotic_name: Optional[str]) -> Tuple[List[str], List[str]]:
    screen, detail = [], []
    for drug in selected:
        info = CHEMO.get(drug)
        if info:
            screen.extend([f"• {drug}: {x}" for x in info["screen"]])
            detail.append(f"▶ {drug}")
            detail.extend([f"  - {x}" for x in info["detail"]])
    if "ARA-C(시타라빈)" in selected and ara_c_form:
        screen.append(f"• ARA-C 제형: {ara_c_form}")

    if antibiotic_name and antibiotic_name in ANTIBIOTICS_INFO:
        screen.append(f"• 항생제: {antibiotic_name} — " + ", ".join(ANTIBIOTICS_INFO[antibiotic_name]))

    if diuretic_on:
        screen.append("• 이뇨제 복용: 탈수·저K/Na·저Ca 주의")
        detail.append("▶ 이뇨제 주의")
        detail.extend([
            "  - 탈수·전해질 이상 위험: BUN/Cr, Na/K/Ca 추적",
            "  - 어지럼·혈압저하 시 의료진 상의",
        ])
    return screen, detail

def estimate_anc_recovery(nickname: str) -> Optional[str]:
    """최근 2회 ANC로 단순 선형 추정(500 도달 일자)."""
    series = get_series(nickname, ["ANC"])["ANC"]
    vals = []
    for ts, v in series[-5:]:  # 최근 5개 중 유효값
        if v is not None:
            # ts -> datetime
            try:
                t = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            except Exception:
                continue
            vals.append((t, float(v)))
    if len(vals) < 2:
        return None
    vals = sorted(vals, key=lambda x: x[0])
    (t1, v1), (t2, v2) = vals[-2], vals[-1]
    dt_days = (t2 - t1).total_seconds() / 86400.0
    if dt_days <= 0:
        return None
    slope = (v2 - v1) / dt_days
    if slope <= 0:
        return "최근 ANC 상승 기울기 없음(또는 하락) — 경과관찰"
    need = 500.0 - v2
    if need <= 0:
        return "ANC 500 이상 도달"
    days = need / slope if slope > 0 else None
    if days is None or days > 30:
        return "ANC 500 도달 예측 불가(기울기 낮음)"
    eta = datetime.now() + timedelta(days=days)
    return f"ANC 500 도달 추정: {eta.strftime('%Y-%m-%d')} (단순 추정)"

# ---------- 보고서 생성 ----------
def build_report(nickname: str, cancer_type: str, category: str, labs: Dict[str, Optional[float]], screen_msgs: List[str], detail_msgs: List[str]) -> str:
    lines = []
    lines.append(f"# 피수치 자동 해석 보고서 ({VERSION})")
    lines.append("제작: Hoya/GPT · 자문: Hoya/GPT")
    lines.append(f"닉네임: {nickname}")
    lines.append(f"카테고리: {category} / 암종류: {cancer_type}")
    lines.append(f"생성시각: {_now_ts()}")
    lines.append("")
    lines.append("## 입력 수치")
    order_keys = [
        "WBC","Hb","PLT","ANC","Ca","P","Na","K","Albumin","Glucose",
        "Total Protein","AST","ALT","LDH","CRP","Creatinine","UA","TB","BUN","BNP"
    ]
    for k in order_keys:
        v = labs.get(k)
        if v is not None:
            lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 화면 요약")
    for s in screen_msgs:
        lines.append(f"- {s}")
    lines.append("")
    if detail_msgs:
        lines.append("## 상세 해설")
        lines.extend(detail_msgs)
        lines.append("")
    lines.append("## 발열/응급 가이드")
    for g in ANTIPYRETIC_GUIDE:
        lines.append(f"- {g}")
    lines.append("")
    lines.append("※ 본 보고서는 참고용이며, 의학적 의사결정을 대체하지 않습니다.")
    return "\n".join(lines)

def to_txt_bytes(s: str) -> bytes:
    return s.encode("utf-8")

def try_build_pdf(s: str) -> Optional[bytes]:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        width, height = A4
        x, y = 15*mm, height - 15*mm
        for line in s.splitlines():
            if y < 15*mm:
                c.showPage()
                y = height - 15*mm
            c.drawString(x, y, line[:120])  # 줄 단순 절단
            y -= 6*mm
        c.save()
        return buf.getvalue()
    except Exception:
        return None

# ---------- UI ----------
st.markdown(f"### 🔬 피수치 자동 해석기 {VERSION}")
st.caption("모바일 최적화 · 입력한 수치만 결과에 표시 · 별명 저장/그래프 · 보고서 다운로드(TXT/PDF)")

views = bump_view_counter()
st.write(f"👀 누적 조회수: **{views}**")

with st.expander("ℹ️ 안내 / 고지", expanded=False):
    st.write(
        "- 본 앱은 교육·정보 제공용입니다. 위험 신호나 고열(≥38.5℃) 시 즉시 병원에 연락하세요.\n"
        "- 결과 저장 시 닉네임별로 추세 그래프를 볼 수 있습니다.\n"
        "- 입력하지 않은 항목은 결과에서 자동으로 숨겨집니다."
    )

# --- 기본 선택 ---
category = st.selectbox("카테고리 선택", ["일반 해석", "항암치료", "투석환자", "당뇨"])
cancer_type = st.selectbox("암 종류 선택", ["해당없음", "AML", "APL", "ALL", "CML", "CLL", "고형암(폐/유방 등)"])

nickname = st.text_input("별명(닉네임)", placeholder="예: 홍길동", max_chars=20)

# 추가 옵션
with st.expander("💊 약물/증상 옵션", expanded=(category == "항암치료")):
    chemo_list = list(CHEMO.keys())
    selected_chemo = st.multiselect("항암제 선택(요약은 화면, 자세한 내용은 보고서에 표시)", chemo_list)
    ara_c_form = None
    if "ARA-C(시타라빈)" in selected_chemo:
        ara_c_form = st.selectbox("ARA-C 제형", ["정맥(IV)", "피하(SC)", "고용량(HDAC)"])
    antibiotic_name = st.selectbox("항생제(선택)", ["선택안함"] + list(ANTIBIOTICS_INFO.keys()))
    antibiotic_name = None if antibiotic_name == "선택안함" else antibiotic_name
    diuretic_on = st.checkbox("이뇨제 복용 중", value=False)
    st.markdown("—")
    st.markdown("**발열 가이드(요약)**")
    for g in ANTIPYRETIC_GUIDE:
        st.write("• " + g)

# 투석 옵션
urine_ml = None
salinity = None
if category == "투석환자":
    with st.expander("🚰 투석 관련 입력(선택)", expanded=True):
        urine_ml = parse_float(st.text_input("하루 소변량(ml)", placeholder="예: 500"))
        salinity = parse_float(st.text_input("염도 측정값(%)", placeholder="예: 0.2"))

# 당뇨 옵션
if category == "당뇨":
    with st.expander("🍚 당뇨 전용 입력(선택)", expanded=True):
        fpg = parse_float(st.text_input("식전 혈당 (mg/dL)", placeholder="예: 100"))
        ppg = parse_float(st.text_input("식후 혈당 (mg/dL)", placeholder="예: 180"))
        hba1c = parse_float(st.text_input("HbA1c (%)", placeholder="예: 8.4"))
        st.caption("※ 당화혈색소(HbA1c)가 높을수록 최근 2~3개월 평균 혈당이 높습니다.")

st.markdown("---")

# --- 메인 입력(단일 컬럼 · 고정 순서) ---
st.markdown("#### 🧪 수치 입력 (입력한 항목만 해석)")

field_order = [
    ("WBC", "WBC (백혈구)"),
    ("Hb", "Hb (혈색소)"),
    ("PLT", "PLT (혈소판)"),
    ("ANC", "ANC (절대 호중구 수)"),
    ("Ca", "Ca (칼슘)"),
    ("P", "P (인)"),
    ("Na", "Na (소디움)"),
    ("K", "K (포타슘)"),
    ("Albumin", "Albumin (알부민)"),
    ("Glucose", "Glucose (혈당)"),
    ("Total Protein", "Total Protein (총단백)"),
    ("AST", "AST"),
    ("ALT", "ALT"),
    ("LDH", "LDH"),
    ("CRP", "CRP"),
    ("Creatinine", "Creatinine (Cr)"),
    ("UA", "Uric Acid (UA)"),
    ("TB", "Total Bilirubin (TB)"),
    ("BUN", "BUN"),
    ("BNP", "BNP (선택)"),
]

with st.form("main_form", clear_on_submit=False):
    inputs = {}
    for key, label in field_order:
        val = st.text_input(label, key=f"input_{key}", placeholder="숫자만 입력", help=None)
        inputs[key] = parse_float(val)

    submitted = st.form_submit_button("🔍 해석하기", use_container_width=True)

# --- 해석 출력 ---
if submitted:
    # 입력값 정리(빈칸 제외)
    labs = {k: (v if v is not None else None) for k, v in inputs.items()}
    labs = {k: v for k, v in labs.items() if v is not None}

    screen_msgs: List[str] = []
    detail_msgs: List[str] = []

    # 기본 해석
    for k, v in labs.items():
        tip = interpret_value(k, v)
        if tip:
            screen_msgs.append(f"{k}: {tip}")

    # 신장/간/탈수
    bun = inputs.get("BUN")
    cr = inputs.get("Creatinine")
    ast = inputs.get("AST")
    alt = inputs.get("ALT")
    ldh = inputs.get("LDH")

    dmsg = dehydration_flag(bun, cr)
    if dmsg:
        screen_msgs.append(dmsg)

    for m in kidney_caution(bun, cr):
        detail_msgs.append(f"- {m}")
    for m in liver_caution(ast, alt, ldh):
        detail_msgs.append(f"- {m}")

    # ANC
    anc_msg = anc_assessment(inputs.get("ANC"))
    screen_msgs.extend(anc_msg)

    # 식품 추천
    foods = build_food_suggestions(inputs)
    if foods:
        screen_msgs.append("🥗 **추천 음식(자동)**")
        screen_msgs.extend(foods)

    # 약물 메시지
    s, d = build_med_messages(selected_chemo, ara_c_form, diuretic_on, antibiotic_name)
    screen_msgs.extend(s)
    detail_msgs.extend(d)

    # 철분제 경고 고정 출력
    screen_msgs.append("⚠️ 영양제 주의")
    for w in IRON_WARNINGS:
        screen_msgs.append("• " + w)

    # 투석·당뇨 보조 문구
    if category == "투석환자":
        if urine_ml is not None:
            screen_msgs.append(f"투석: 소변량 {urine_ml:.0f} ml/일")
        if salinity is not None:
            screen_msgs.append(f"투석: 염도 측정 {salinity} %")
    if category == "당뇨":
        # 당뇨 입력이 있을 때 간단 코멘트
        if 'fpg' in locals() and fpg is not None and fpg >= 126:
            screen_msgs.append("당뇨: 공복혈당 높음 — 식사·운동·약물 점검")
        if 'ppg' in locals() and ppg is not None and ppg >= 180:
            screen_msgs.append("당뇨: 식후혈당 높음 — 탄수화물 분배/식후 활동")
        if 'hba1c' in locals() and hba1c is not None and hba1c >= 6.5:
            screen_msgs.append("당뇨: HbA1c 높음 — 최근 2~3개월 평균 혈당 상승")

    # 결과 표시 (입력 항목만)
    st.markdown("### ✅ 해석 결과 (요약)")
    if labs:
        cols = []
        for k in [
            "WBC","Hb","PLT","ANC","CRP","AST","ALT","BUN","Creatinine","Glucose","Albumin","Na","K","Ca"
        ]:
            if k in labs:
                cols.append(f"- **{k}**: {labs[k]}")
        if cols:
            st.markdown("\n".join(cols))
    for m in screen_msgs:
        st.write("• " + m)

    # 보고서 만들기
    report_txt = build_report(nickname or "무명", cancer_type, category, inputs, screen_msgs, detail_msgs)

    # 저장 유도
    st.markdown("---")
    st.subheader("💾 저장 / 다운로드")
    save_choice = st.checkbox("결과를 저장하시겠습니까?", value=True)
    if st.button("저장", use_container_width=True):
        if not nickname.strip():
            st.error("닉네임을 입력해주세요.")
        else:
            record = {
                "ts": _now_ts(),
                "version": VERSION,
                "nickname": nickname.strip(),
                "category": category,
                "cancer_type": cancer_type,
                "labs": inputs,
                "screen": screen_msgs,
            }
            save_record(nickname.strip(), record)
            st.success("저장 완료!")

    st.download_button(
        "📄 보고서(.txt) 다운로드",
        data=to_txt_bytes(report_txt),
        file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
        use_container_width=True,
    )

    pdf_bytes = try_build_pdf(report_txt)
    if pdf_bytes:
        st.download_button(
            "🧾 보고서(.pdf) 다운로드",
            data=pdf_bytes,
            file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    else:
        st.info("PDF 모듈이 없거나 생성 실패 시 TXT만 제공됩니다. (reportlab 필요)")

st.markdown("---")
# 그래프
st.markdown("### 📈 추세 그래프 (WBC, Hb, PLT, CRP, ANC)")
store = get_store()
names = ["(선택)"] + sorted(store.keys())
pick = st.selectbox("닉네임 선택", names, index=0)
if pick != "(선택)":
    series = get_series(pick, ["WBC","Hb","PLT","CRP","ANC"])
    # 표 형태로 먼저 노출(모바일 안정성)
    import pandas as pd
    df = pd.DataFrame({
        "ts": [t for t,_ in series["WBC"]] if series["WBC"] else [],
        "WBC": [v for _,v in series["WBC"]],
        "Hb": [v for _,v in series["Hb"]],
        "PLT": [v for _,v in series["PLT"]],
        "CRP": [v for _,v in series["CRP"]],
        "ANC": [v for _,v in series["ANC"]],
    })
    st.dataframe(df, use_container_width=True, height=260)

    # 간단 라인차트(값 없는 구간은 자동 스킵)
    st.line_chart(df.set_index("ts")[["WBC","Hb","PLT","CRP","ANC"]])

    # 간단한 ANC 500 도달 추정(참고용)
    try:
        from datetime import timedelta
        msg = estimate_anc_recovery(pick)
        if msg:
            st.caption("🧭 " + msg)
    except Exception:
        pass

# 보호자 Q&A (간단 템플릿)
with st.expander("🙋 보호자 맞춤 Q&A", expanded=False):
    st.markdown("**Q. 열이 나요, 어떻게 할까요?**")
    st.write("A. 38.5℃ 이상이면 병원에 연락, 39℃ 이상이면 즉시 방문. 해열제 복용 간격을 지키고, 호중구가 낮다면 외출을 자제하세요.")
    st.markdown("**Q. 구내염이 심해요.**")
    st.write("A. 자극적·산성 음식은 피하고 미지근한 물가글. MTX/ATRA 복용 중이면 증상·용량을 의료진과 상의하세요.")
    st.markdown("**Q. 피부가 건조하고 트러블이 생겨요.**")
    st.write("A. 보습제는 보조, 치료는 처방 연고가 주 역할입니다(필요 시 진료). 광과민 유발 약물 복용 시 자외선 차단을 생활화하세요.")

st.caption("© Hoya/GPT — 보호자들의 울타리가 되겠습니다.")
