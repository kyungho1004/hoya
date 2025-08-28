
from datetime import datetime, date
import os
import streamlit as st

# ===== Optional deps =====
try:
    import pandas as pd
    HAS_PD = True
except Exception:
    HAS_PD = False

# PDF generation (required libs)
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

from xml.sax.saxutils import escape

# ===== Page config =====
st.set_page_config(page_title="피수치 가이드 by Hoya (v3.13 · 변화비교/스케줄/계절식/ANC장소)", layout="centered")
st.title("🩸 피수치 가이드  (v3.13 · 변화비교 · 스케줄표 · 계절 식재료 · ANC 장소별 가이드)")
st.markdown("👤 **제작자: Hoya / 자문: 호야/GPT** · 📅 {} 기준".format(date.today().isoformat()))
st.markdown("[📌 **피수치 가이드 공식카페 바로가기**](https://cafe.naver.com/bloodmap)")
st.caption("✅ 모바일 줄꼬임 방지 · 별명 저장/그래프 · 암별/소아/희귀암 패널 · PDF 한글 폰트 고정 · 수치 변화 비교 · 항암 스케줄표 · 계절 식재료/레시피 · ANC 병원/가정 구분")

# Ensure fonts folder exists
os.makedirs("fonts", exist_ok=True)

# ===== Label constants (Korean-friendly) =====
LBL_WBC = "WBC(백혈구)"
LBL_Hb = "Hb(적혈구)"
LBL_PLT = "PLT(혈소판)"
LBL_ANC = "ANC(호중구,면역력)"
LBL_Ca = "Ca(칼슘)"
LBL_P = "P(인)"
LBL_Na = "Na(나트륨)"
LBL_K = "K(포타슘)"
LBL_Alb = "Albumin(알부민)"
LBL_Glu = "Glucose(혈당)"
LBL_TP = "Total Protein(총단백질)"
LBL_AST = "AST(간수치)"
LBL_ALT = "ALT(간세포수치)"
LBL_LDH = "LDH(유산탈수효소)"
LBL_CRP = "CRP(염증수치)"
LBL_Cr = "Cr(신장수치)"
LBL_UA = "UA(요산수치)"
LBL_TB = "TB(총빌리루빈)"
LBL_BUN = "BUN(신장수치)"
LBL_BNP = "BNP(심장척도)"

ORDER = [
    LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K, LBL_Alb,
    LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA,
    LBL_TB, LBL_BUN, LBL_BNP
]

DISCLAIMER = (
    "※ 본 자료는 보호자의 이해를 돕기 위한 참고용 정보입니다. "
    "진단 및 처방은 하지 않으며, 모든 의학적 판단은 의료진의 권한입니다. "
    "개발자는 이에 대한 판단·조치에 일절 관여하지 않으며, 책임지지 않습니다."
)

# ===== Drug dictionaries (trimmed) =====
ANTICANCER = {
    "6-MP":{"alias":"6-머캅토퓨린","aes":["골수억제","간수치 상승","구내염","오심"]},
    "MTX":{"alias":"메토트렉세이트","aes":["골수억제","간독성","신독성","구내염","광과민"]},
    "ATRA":{"alias":"트레티노인(베사노이드)","aes":["분화증후군","발열","피부/점막 건조","두통"]},
    "ARA-C":{"alias":"시타라빈","aes":["골수억제","발열","구내염","(HDAC) 신경독성"]},
    "G-CSF":{"alias":"그라신","aes":["골통/근육통","주사부위 반응","드물게 비장비대"]},
    "Hydroxyurea":{"alias":"하이드록시우레아","aes":["골수억제","피부색소침착","궤양"]},
    "Daunorubicin":{"alias":"도우노루비신","aes":["골수억제","심독성","오심/구토","점막염"]},
    "Idarubicin":{"alias":"이달루비신","aes":["골수억제","심독성","점막염"]},
    "Cyclophosphamide":{"alias":"사이클로포스파미드","aes":["골수억제","출혈성 방광염","탈모"]},
    "Etoposide":{"alias":"에토포사이드","aes":["골수억제","저혈압(주입)"]},
    "Topotecan":{"alias":"토포테칸","aes":["골수억제","설사"]},
    "Fludarabine":{"alias":"플루다라빈","aes":["면역억제","감염 위험↑","혈구감소"]},
    "Vincristine":{"alias":"빈크리스틴","aes":["말초신경병증","변비/장폐색"]},
    "Imatinib":{"alias":"이마티닙(TKI)","aes":["부종","근육통","피로","간수치 상승"]},
    "Dasatinib":{"alias":"다사티닙(TKI)","aes":["혈소판감소","흉막/심막 삼출","설사"]},
    "Nilotinib":{"alias":"닐로티닙(TKI)","aes":["QT 연장","고혈당","간수치 상승"]},
    "Rituximab":{"alias":"리툭시맙","aes":["주입반응","감염 위험","HBV 재활성"]},

    # Solid-tumor common (발췌)
    "Paclitaxel":{"alias":"파클리탁셀","aes":["말초신경병증","호중구감소"]},
    "Docetaxel":{"alias":"도세탁셀","aes":["체액저류","호중구감소"]},
    "Doxorubicin":{"alias":"독소루비신","aes":["심독성","탈모","구내염"]},
    "Carboplatin":{"alias":"카보플라틴","aes":["혈구감소","신독성(경미)"]},
    "Cisplatin":{"alias":"시스플라틴","aes":["신독성","오심/구토","이독성"]},
    "Oxaliplatin":{"alias":"옥살리플라틴","aes":["말초신경병증(냉감 유발)"]},
    "5-FU":{"alias":"플루오로우라실","aes":["점막염","설사","수족증후군"]},
    "Capecitabine":{"alias":"카페시타빈","aes":["수족증후군","설사"]},
    "Gemcitabine":{"alias":"젬시타빈","aes":["혈구감소","발열"]},
    "Pemetrexed":{"alias":"페메트렉시드","aes":["골수억제","피부발진"]},
    "Irinotecan":{"alias":"이리노테칸","aes":["급성/지연성 설사"]},
    "Trastuzumab":{"alias":"트라스투주맙","aes":["심기능저하"]},
    "Bevacizumab":{"alias":"베바시주맙","aes":["고혈압","단백뇨","출혈/천공(드묾)"]},
    "Pembrolizumab":{"alias":"펨브롤리주맙(PD-1)","aes":["면역관련 이상반응"]},
    "Nivolumab":{"alias":"니볼루맙(PD-1)","aes":["면역관련 이상반응"]},
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

# 계절 식재료 + 간단 레시피 링크(예시 링크; 병원/가정 모두 참고용)
FOODS_SEASONAL = {
    "봄": ["두릅", "봄동", "주꾸미", "달래", "쑥"],
    "여름": ["오이", "토마토", "옥수수", "참외", "수박"],
    "가을": ["버섯", "고등어", "전어", "배", "단호박"],
    "겨울": ["무", "배추", "굴", "귤", "시금치"],
}
RECIPE_LINKS = {
    "달걀": "https://recipe1.ezmember.co.kr/",
    "연두부": "https://www.10000recipe.com/",
    "흰살 생선": "https://www.10000recipe.com/",
    "닭가슴살": "https://www.10000recipe.com/",
    "귀리죽": "https://www.10000recipe.com/",
    "바나나": "https://www.10000recipe.com/",
    "감자": "https://www.10000recipe.com/",
    "호박죽": "https://www.10000recipe.com/",
    "고구마": "https://www.10000recipe.com/",
    "오렌지": "https://www.10000recipe.com/",
    "소고기": "https://www.10000recipe.com/",
    "시금치": "https://www.10000recipe.com/",
    "두부": "https://www.10000recipe.com/",
    "달걀 노른자": "https://www.10000recipe.com/",
    "렌틸콩": "https://www.10000recipe.com/",
    "전해질 음료": "https://www.10000recipe.com/",
    "미역국": "https://www.10000recipe.com/",
    "오트밀죽": "https://www.10000recipe.com/",
    "삶은 감자": "https://www.10000recipe.com/",
    "연어 통조림": "https://www.10000recipe.com/",
    "두릅": "https://www.10000recipe.com/",
    "봄동": "https://www.10000recipe.com/",
    "주꾸미": "https://www.10000recipe.com/",
    "달래": "https://www.10000recipe.com/",
    "쑥": "https://www.10000recipe.com/",
    "오이": "https://www.10000recipe.com/",
    "토마토": "https://www.10000recipe.com/",
    "옥수수": "https://www.10000recipe.com/",
    "참외": "https://www.10000recipe.com/",
    "수박": "https://www.10000recipe.com/",
    "버섯": "https://www.10000recipe.com/",
    "고등어": "https://www.10000recipe.com/",
    "전어": "https://www.10000recipe.com/",
    "배": "https://www.10000recipe.com/",
    "단호박": "https://www.10000recipe.com/",
    "무": "https://www.10000recipe.com/",
    "배추": "https://www.10000recipe.com/",
    "굴": "https://www.10000recipe.com/",
    "귤": "https://www.10000recipe.com/",
}

FEVER_GUIDE = "🌡️ 38.0~38.5℃ 해열제/경과, 38.5℃↑ 병원 연락, 39.0℃↑ 즉시 병원. (ANC<500 동반 발열=응급)"

PED_TOPICS = ["RSV/모세기관지염","영아 중이염","크룹","구토·설사(탈수)","열경련"]
PED_INPUTS_INFO = (
    "다음 공통 입력은 위험도 배너 산출에 사용됩니다.\n"
    "- 나이(개월), 체온(℃), 호흡수(/분), 산소포화도(%), 24시간 소변 횟수, "
    "함몰/견흔(0/1), 콧벌렁임(0/1), 무호흡(0/1)"
)

PED_INFECT = {
    "RSV(세포융합바이러스)": {"핵심":"기침, 쌕쌕거림, 발열","진단":"항원검사 또는 PCR","특징":"모세기관지염 흔함, 겨울철 유행"},
    "Adenovirus(아데노바이러스)": {"핵심":"고열, 결막염, 설사","진단":"PCR","특징":"장염 + 눈충혈 동반 많음"},
    "Rotavirus(로타바이러스)": {"핵심":"구토, 물설사","진단":"항원검사","특징":"탈수 위험 가장 큼"},
    "Parainfluenza (파라인플루엔자)": {"핵심":"크룹, 쉰목소리","진단":"PCR","특징":"개짖는 기침 특징적"},
    "HFMD (수족구병)": {"핵심":"입안 궤양, 손발 수포","진단":"임상진단","특징":"전염성 매우 강함"},
    "Influenza (독감)": {"핵심":"고열, 근육통","진단":"신속검사 또는 PCR","특징":"해열제 효과 적음"},
    "COVID-19 (코로나)": {"핵심":"발열, 기침, 무증상도 흔함","진단":"PCR","특징":"지속적 산발 유행 가능"},
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
    if name == LBL_CRP:
        return f"{v:.2f}"
    if name in (LBL_WBC, LBL_ANC, LBL_AST, LBL_ALT, LBL_LDH, LBL_BNP, LBL_Glu):
        return f"{int(v)}" if v.is_integer() else f"{v:.1f}"
    return f"{v:.1f}"

def interpret_labs(l, extras):
    out=[]
    def add(s): out.append("- " + s)
    if entered(l.get(LBL_WBC)):
        v=l[LBL_WBC]; add(f"{LBL_WBC} {_fmt(LBL_WBC, v)}: " + ("낮음 → 감염 위험↑" if v<4 else "높음 → 감염/염증 가능" if v>10 else "정상"))
    if entered(l.get(LBL_Hb)):
        v=l[LBL_Hb]; add(f"{LBL_Hb} {_fmt(LBL_Hb, v)}: " + ("낮음 → 빈혈" if v<12 else "정상"))
    if entered(l.get(LBL_PLT)):
        v=l[LBL_PLT]; add(f"{LBL_PLT} {_fmt(LBL_PLT, v)}: " + ("낮음 → 출혈 위험" if v<150 else "정상"))
    if entered(l.get(LBL_ANC)):
        v=l[LBL_ANC]; add(f"{LBL_ANC} {_fmt(LBL_ANC, v)}: " + ("중증 감소(<500)" if v<500 else "감소(<1500)" if v<1500 else "정상"))
    if entered(l.get(LBL_Alb)):
        v=l[LBL_Alb]; add(f"{LBL_Alb} {_fmt(LBL_Alb, v)}: " + ("낮음 → 영양/염증/간질환 가능" if v<3.5 else "정상"))
    if entered(l.get(LBL_Glu)):
        v=l[LBL_Glu]; add(f"{LBL_Glu} {_fmt(LBL_Glu, v)}: " + ("고혈당(≥200)" if v>=200 else "저혈당(<70)" if v<70 else "정상"))
    if entered(l.get(LBL_CRP)):
        v=l[LBL_CRP]; add(f"{LBL_CRP} {_fmt(LBL_CRP, v)}: " + ("상승 → 염증/감염 의심" if v>0.5 else "정상"))
    if entered(l.get(LBL_BUN)) and entered(l.get(LBL_Cr)) and l[LBL_Cr]>0:
        ratio=l[LBL_BUN]/l[LBL_Cr]
        if ratio>20: add(f"BUN/Cr {ratio:.1f}: 탈수 의심")
        elif ratio<10: add(f"BUN/Cr {ratio:.1f}: 간질환/영양 고려")
    if extras.get("diuretic_amt", 0) and extras["diuretic_amt"]>0:
        if entered(l.get(LBL_Na)) and l[LBL_Na]<135: add("🧂 이뇨제 복용 중 저나트륨 → 어지럼/탈수 주의, 의사와 상의")
        if entered(l.get(LBL_K)) and l[LBL_K]<3.5: add("🥔 이뇨제 복용 중 저칼륨 → 심전도/근력저하 주의, 칼륨 보충 식이 고려")
        if entered(l.get(LBL_Ca)) and l[LBL_Ca]<8.5: add("🦴 이뇨제 복용 중 저칼슘 → 손저림/경련 주의")
    return out

def _arrow(delta):
    if delta > 0: return "↑"
    if delta < 0: return "↓"
    return "→"

def compare_with_previous(nickname, new_labs):
    """Return list of comparison strings vs previous saved record for this nickname."""
    rows = st.session_state.records.get(nickname, []) if "records" in st.session_state else []
    if not rows:
        return []
    # previous record = last saved
    prev = rows[-1].get("labs", {})
    out = []
    for k in ORDER:
        if entered(new_labs.get(k)) and entered(prev.get(k)):
            try:
                cur = float(new_labs[k])
                old = float(prev[k])
                delta = cur - old
                sign = _arrow(delta)
                # format delta
                if k == LBL_CRP:
                    dtxt = f"{delta:+.2f}"
                elif k in (LBL_WBC, LBL_ANC, LBL_AST, LBL_ALT, LBL_LDH, LBL_BNP, LBL_Glu):
                    dtxt = f"{delta:+.1f}"
                else:
                    dtxt = f"{delta:+.1f}"
                out.append(f"- {k}: {_fmt(k, cur)} ({sign} {dtxt} vs { _fmt(k, old) })")
            except Exception:
                pass
    return out

def seasonal_food_section():
    # Detect season by month (KST)
    m = date.today().month
    if m in (3,4,5): season="봄"
    elif m in (6,7,8): season="여름"
    elif m in (9,10,11): season="가을"
    else: season="겨울"
    st.markdown(f"#### 🥗 계절 식재료 ({season})")
    items = FOODS_SEASONAL.get(season, [])
    if items:
        st.write("· " + ", ".join(items))
    st.caption("간단 레시피는 아래 추천 목록의 각 식재료 링크를 눌러 참고하세요.")

def food_suggestions(l, anc_place):
    foods=[]
    # 계절 섹션 먼저
    seasonal_food_section()

    if entered(l.get(LBL_Alb)) and l[LBL_Alb]<3.5: foods.append(("알부민 낮음", FOODS["Albumin_low"]))
    if entered(l.get(LBL_K)) and l[LBL_K]<3.5: foods.append(("칼륨 낮음", FOODS["K_low"]))
    if entered(l.get(LBL_Hb)) and l[LBL_Hb]<12: foods.append(("Hb 낮음", FOODS["Hb_low"]))
    if entered(l.get(LBL_Na)) and l[LBL_Na]<135: foods.append(("나트륨 낮음", FOODS["Na_low"]))
    if entered(l.get(LBL_Ca)) and l[LBL_Ca]<8.5: foods.append(("칼슘 낮음", FOODS["Ca_low"]))

    # ANC 기반 장소 구분 가이드
    if entered(l.get(LBL_ANC)) and l[LBL_ANC]<500:
        if anc_place == "병원":
            anc_line = "🧼 (병원) 호중구 감소: 멸균/살균 처리식 권장, 외부 음식 반입 제한, 병원 조리식 우선."
        else:
            anc_line = "🧼 (가정) 호중구 감소: 생채소 금지, 모든 음식 완전가열(전자레인지 30초+), 조리 후 2시간 경과 음식 금지, 껍질 과일은 의료진과 상의."
    else:
        anc_line = None

    # Build markdown bullets with recipe links
    lines = []
    for title, lst in foods:
        linked = []
        for x in lst:
            url = RECIPE_LINKS.get(x, "https://www.10000recipe.com/")
            linked.append(f"[{x}]({url})")
        lines.append(f"- {title} → " + ", ".join(linked))
    # add ANC line at the end if exists
    if anc_line:
        lines.append("- " + anc_line)

    # Common warning
    lines.append("- ⚠️ 항암/백혈병 환자는 철분제는 반드시 주치의와 상의(비타민C 병용 시 흡수↑).")
    return lines

def summarize_meds(meds: dict):
    out=[]
    for k, v in meds.items():
        info=ANTICANCER.get(k)
        if not info:
            continue
        line=f"• {k} ({info['alias']}): AE {', '.join(info['aes'])}"
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

# ===== Session stores =====
if "records" not in st.session_state:
    st.session_state.records = {}
if "schedules" not in st.session_state:
    st.session_state.schedules = {}

# ===== UI 1) Patient / Mode =====
st.divider()
st.header("1️⃣ 환자/암·소아 정보")

c1, c2 = st.columns(2)
with c1:
    nickname = st.text_input("별명(저장/그래프/스케줄용)", placeholder="예: 홍길동")
with c2:
    test_date = st.date_input("검사 날짜", value=date.today())

# ANC 장소 선택 (병원/가정)
anc_place = st.radio("현재 식사 장소(ANC 가이드용)", ["가정", "병원"], horizontal=True)

mode = st.selectbox("모드 선택", ["일반/암", "소아(일상/호흡기)", "소아(감염질환)"])

group = None
cancer = None
infect_sel = None
if mode == "일반/암":
    group = st.selectbox("암 그룹 선택", ["미선택/일반", "혈액암", "고형암", "소아암", "희귀암"])
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
        st.info("암 그룹을 선택하면 해당 암종에 맞는 **항암제 목록과 추가 수치 패널**이 자동 노출됩니다.")
elif mode == "소아(일상/호흡기)":
    st.markdown("### 🧒 소아 일상 주제 선택")
    st.caption(PED_INPUTS_INFO)
    ped_topic = st.selectbox("소아 주제", PED_TOPICS)
else:
    st.markdown("### 🧫 소아·영유아 감염질환")
    infect_sel = st.selectbox("질환 선택", list(PED_INFECT.keys()))
    if HAS_PD:
        _df = pd.DataFrame([{
            "핵심": PED_INFECT[infect_sel].get("핵심",""),
            "진단": PED_INFECT[infect_sel].get("진단",""),
            "특징": PED_INFECT[infect_sel].get("특징",""),
        }], index=[infect_sel])
        st.table(_df)
    else:
        st.markdown(f"**{infect_sel}**")
        st.write(f"- 핵심: {PED_INFECT[infect_sel].get('핵심','')}")
        st.write(f"- 진단: {PED_INFECT[infect_sel].get('진단','')}")
        st.write(f"- 특징: {PED_INFECT[infect_sel].get('특징','')}")

table_mode = st.checkbox("⚙️ PC용 표 모드(가로형)", help="모바일은 세로형 고정 → 줄꼬임 없음.")


# ===== Drugs & extras =====
meds = {}
extras = {}

if mode == "일반/암" and group and group != "미선택/일반" and cancer:
    st.markdown("### 💊 항암제 선택 및 입력")

    heme_by_cancer = {
        "AML": ["ARA-C","Daunorubicin","Idarubicin","Cyclophosphamide",
                "Etoposide","Fludarabine","Hydroxyurea","MTX","ATRA","G-CSF"],
        "APL": ["ATRA","Idarubicin","Daunorubicin","ARA-C","G-CSF"],
        "ALL": ["Vincristine","Asparaginase","Daunorubicin","Cyclophosphamide","MTX","ARA-C","Topotecan","Etoposide"],
        "CML": ["Imatinib","Dasatinib","Nilotinib","Hydroxyurea"],
        "CLL": ["Fludarabine","Cyclophosphamide","Rituximab"],
    }
    solid_by_cancer = {
        "폐암(Lung cancer)": ["Cisplatin","Carboplatin","Paclitaxel","Docetaxel","Gemcitabine","Pemetrexed",
                           "Gefitinib","Erlotinib","Osimertinib","Alectinib","Bevacizumab","Pembrolizumab","Nivolumab"],
        "유방암(Breast cancer)": ["Doxorubicin","Cyclophosphamide","Paclitaxel","Docetaxel","Trastuzumab","Bevacizumab"],
        "위암(Gastric cancer)": ["Cisplatin","Oxaliplatin","5-FU","Capecitabine","Paclitaxel","Trastuzumab","Pembrolizumab"],
        "대장암(Cololoractal cancer)": ["5-FU","Capecitabine","Oxaliplatin","Irinotecan","Bevacizumab"],
        "간암(HCC)": ["Sorafenib","Lenvatinib","Bevacizumab","Pembrolizumab","Nivolumab"],
        "췌장암(Pancreatic cancer)": ["Gemcitabine","Oxaliplatin","Irinotecan","5-FU"],
        "담도암(Cholangiocarcinoma)": ["Gemcitabine","Cisplatin","Bevacizumab"],
        "자궁내막암(Endometrial cancer)": ["Carboplatin","Paclitaxel"],
        "구강암/후두암": ["Cisplatin","5-FU","Docetaxel"],
        "피부암(흑색종)": ["Dacarbazine","Paclitaxel","Nivolumab","Pembrolizumab"],
        "육종(Sarcoma)": ["Doxorubicin","Ifosfamide","Pazopanib"],
        "신장암(RCC)": ["Sunitinib","Pazopanib","Bevacizumab","Nivolumab","Pembrolizumab"],
        "갑상선암": ["Lenvatinib","Sorafenib"],
        "난소암": ["Carboplatin","Paclitaxel","Bevacizumab"],
        "자궁경부암": ["Cisplatin","Paclitaxel","Bevacizumab"],
        "전립선암": ["Docetaxel","Cabazitaxel"],
        "뇌종양(Glioma)": ["Temozolomide","Bevacizumab"],
        "식도암": ["Cisplatin","5-FU","Paclitaxel","Nivolumab","Pembrolizumab"],
        "방광암": ["Cisplatin","Gemcitabine","Bevacizumab","Pembrolizumab","Nivolumab"],
    }
    rare_by_cancer = {
        "담낭암(Gallbladder cancer)": ["Gemcitabine","Cisplatin"],
        "부신암(Adrenal cancer)": ["Mitotane","Etoposide","Doxorubicin","Cisplatin"],
        "망막모세포종(Retinoblastoma)": ["Vincristine","Etoposide","Carboplatin"],
        "흉선종/흉선암(Thymoma/Thymic carcinoma)": ["Cyclophosphamide","Doxorubicin","Cisplatin"],
        "신경내분비종양(NET)": ["Etoposide","Cisplatin","Sunitinib"],
        "간모세포종(Hepatoblastoma)": ["Cisplatin","Doxorubicin"],
        "비인두암(NPC)": ["Cisplatin","5-FU","Gemcitabine","Bevacizumab","Nivolumab","Pembrolizumab"],
        "GIST": ["Imatinib","Sunitinib","Regorafenib"],
    }
    default_drugs_by_group = {
        "혈액암": heme_by_cancer.get(cancer, []),
        "고형암": solid_by_cancer.get(cancer, []),
        "소아암": ["Cyclophosphamide","Ifosfamide","Doxorubicin","Vincristine","Etoposide","Carboplatin","Cisplatin","Topotecan","Irinotecan"],
        "희귀암": rare_by_cancer.get(cancer, []),
    }
    drug_list = list(dict.fromkeys(default_drugs_by_group.get(group, [])))

    
drug_list = locals().get('drug_list', [])
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
            if amt>0:
                meds[d] = {"form": ara_form, "dose": amt}
            continue
        else:
            amt = num_input_generic(f"{d} ({alias}) - 용량/알약", key=f"med_{d}", decimals=1, placeholder="예: 1.5")
        if amt and float(amt)>0:
            meds[d] = {"dose_or_tabs": amt}

# 항생제 드롭다운
st.markdown("### 🧪 항생제 선택 및 입력")
extras["abx"] = {}

abx_search = st.text_input("🔍 항생제 검색", key="abx_search")
abx_choices = [a for a in ABX_GUIDE.keys() if not abx_search or abx_search.lower() in a.lower() or any(abx_search.lower() in tip.lower() for tip in ABX_GUIDE[a])]
selected_abx = st.multiselect("항생제 계열 선택", abx_choices, default=[])

for abx in selected_abx:
    extras["abx"][abx] = num_input_generic(f"{abx} - 복용/주입량", key=f"abx_{abx}", decimals=1, placeholder="예: 1")

st.markdown("### 💧 동반 약물/상태")
extras["diuretic_amt"] = num_input_generic("이뇨제(복용량/회/일)", key="diuretic_amt", decimals=1, placeholder="예: 1")

# ===== UI 2) Inputs =====

st.divider()
if mode == "일반/암":
    st.header("2️⃣ 기본 혈액 검사 수치 (입력한 값만 해석)")
elif mode == "소아(일상/호흡기)":
    st.header("2️⃣ 소아 공통 입력")
else:
    st.header("2️⃣ (감염질환은 별도 수치 입력 없음)")

vals = {}

def render_inputs_vertical():
    st.markdown("**기본 패널**")
    for name in ORDER:
        if name == LBL_CRP:
            vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=2, placeholder="예: 0.12")
        elif name in (LBL_WBC, LBL_ANC, LBL_AST, LBL_ALT, LBL_LDH, LBL_BNP, LBL_Glu):
            vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=1, placeholder="예: 1200")
        else:
            vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=1, placeholder="예: 3.5")

def render_inputs_table():
    st.markdown("**기본 패널 (표 모드)**")
    left, right = st.columns(2)
    half = (len(ORDER)+1)//2
    with left:
        for name in ORDER[:half]:
            if name == LBL_CRP:
                vals[name] = num_input_generic(f"{name}", key=f"l_{name}", decimals=2, placeholder="예: 0.12")
            elif name in (LBL_WBC, LBL_ANC, LBL_AST, LBL_ALT, LBL_LDH, LBL_BNP, LBL_Glu):
                vals[name] = num_input_generic(f"{name}", key=f"l_{name}", decimals=1, placeholder="예: 1200")
            else:
                vals[name] = num_input_generic(f"{name}", key=f"l_{name}", decimals=1, placeholder="예: 3.5")
    with right:
        for name in ORDER[half:]:
            if name == LBL_CRP:
                vals[name] = num_input_generic(f"{name}", key=f"r_{name}", decimals=2, placeholder="예: 0.12")
            elif name in (LBL_WBC, LBL_ANC, LBL_AST, LBL_ALT, LBL_LDH, LBL_BNP, LBL_Glu):
                vals[name] = num_input_generic(f"{name}", key=f"r_{name}", decimals=1, placeholder="예: 1200")
            else:
                vals[name] = num_input_generic(f"{name}", key=f"r_{name}", decimals=1, placeholder="예: 3.5")

if mode == "일반/암":
    if table_mode:
        render_inputs_table()
    else:
        render_inputs_vertical()
elif mode == "소아(일상/호흡기)":
    def _parse_num_ped(label, key, decimals=1, placeholder=""):
        raw = st.text_input(label, key=key, placeholder=placeholder)
        return _parse_numeric(raw, decimals=decimals)

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

if mode == "일반/암" and group and group != "미선택/일반" and cancer:
    items = {
        "AML": [("PT","PT","sec",1),("aPTT","aPTT","sec",1),("Fibrinogen","Fibrinogen","mg/dL",1),("D-dimer","D-dimer","µg/mL FEU",2)],
        "APL": [("PT","PT","sec",1),("aPTT","aPTT","sec",1),("Fibrinogen","Fibrinogen","mg/dL",1),("D-dimer","D-dimer","µg/mL FEU",2),("DIC Score","DIC Score","pt",0)],
        "ALL": [("PT","PT","sec",1),("aPTT","aPTT","sec",1),("CNS Sx","CNS 증상 여부(0/1)","",0)],
        "CML": [("BCR-ABL PCR","BCR-ABL PCR","%IS",2),("Basophil%","기저호염기구(Baso) 비율","%",1)],
        "CLL": [("IgG","면역글로불린 IgG","mg/dL",0),("IgA","면역글로불린 IgA","mg/dL",0),("IgM","면역글로불린 IgM","mg/dL",0)],
        "폐암(Lung cancer)": [("CEA","CEA","ng/mL",1),("CYFRA 21-1","CYFRA 21-1","ng/mL",1),("NSE","Neuron-specific enolase","ng/mL",1)],
        "유방암(Breast cancer)": [("CA15-3","CA15-3","U/mL",1),("CEA","CEA","ng/mL",1),("HER2","HER2","IHC/FISH",0),("ER/PR","ER/PR","%",0)],
        "위암(Gastric cancer)": [("CEA","CEA","ng/mL",1),("CA72-4","CA72-4","U/mL",1),("CA19-9","CA19-9","U/mL",1)],
        "대장암(Cololoractal cancer)": [("CEA","CEA","ng/mL",1),("CA19-9","CA19-9","U/mL",1)],
        "간암(HCC)": [("AFP","AFP","ng/mL",1),("PIVKA-II","PIVKA-II(DCP)","mAU/mL",0)],
        "피부암(흑색종)": [("S100","S100","µg/L",1),("LDH","LDH","U/L",0)],
        "육종(Sarcoma)": [("ALP","ALP","U/L",0),("CK","CK","U/L",0)],
        "신장암(RCC)": [("CEA","CEA","ng/mL",1),("LDH","LDH","U/L",0)],
        "식도암": [("SCC Ag","SCC antigen","ng/mL",1),("CEA","CEA","ng/mL",1)],
        "방광암": [("NMP22","NMP22","U/mL",1),("UBC","UBC","µg/L",1)],
    }.get(cancer, [])
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
    ped_risk_banner(age_m, temp_c, rr, spo2, urine_24h, retraction, nasal_flaring, apnea)
else:
    st.divider()
    st.header("3️⃣ 감염질환 요약")
    st.info("표는 위 선택창에서 자동 생성됩니다.")

# ===== NEW: 항암 스케줄표 (별명 기반) =====
st.divider()
st.header("📆 항암 스케줄표 (별명별 관리)")
if nickname and nickname.strip():
    # init schedule list
    st.session_state.schedules.setdefault(nickname, [])
    colA, colB, colC = st.columns([1,1,2])
    with colA:
        sch_date = st.date_input("날짜 선택", value=date.today(), key="sch_date")
    with colB:
        sch_drug = st.text_input("항암제/치료명", key="sch_drug", placeholder="예: ARA-C, MTX, 외래채혈")
    with colC:
        sch_note = st.text_input("비고(용량/주기 등)", key="sch_note", placeholder="예: HDAC Day1, 100mg/m2")

    if st.button("➕ 일정 추가", use_container_width=True):
        st.session_state.schedules[nickname].append({
            "date": sch_date.isoformat(),
            "drug": sch_drug.strip(),
            "note": sch_note.strip()
        })
        st.success("스케줄이 추가되었습니다.")

    rows = st.session_state.schedules.get(nickname, [])
    if rows:
        if HAS_PD:
            df = pd.DataFrame(rows)
            df = df.sort_values("date")
            st.table(df)
            # CSV download
            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📥 스케줄(.csv) 다운로드", data=csv, file_name=f"{nickname}_schedule.csv", mime="text/csv")
        else:
            for r in sorted(rows, key=lambda x: x["date"]):
                st.write(f"- {r['date']} · {r['drug']} · {r['note']}")
    else:
        st.info("일정을 추가해 관리하세요. (별명 기준으로 저장됩니다)")
else:
    st.info("별명을 입력하면 스케줄표를 사용할 수 있어요.")

# ===== Run =====
st.divider()
run = st.button("🔎 해석하기", use_container_width=True)

if run:
    st.subheader("📋 해석 결과")

    if mode == "일반/암":
        lines = interpret_labs(vals, extras)
        for line in lines: st.write(line)

        # NEW: 수치 변화 비교 (이전 기록과)
        if nickname and "records" in st.session_state and st.session_state.records.get(nickname):
            st.markdown("### 🔍 수치 변화 비교 (이전 기록 대비)")
            cmp_lines = compare_with_previous(nickname, {k: vals.get(k) for k in ORDER if entered(vals.get(k))})
            if cmp_lines:
                for l in cmp_lines: st.write(l)
            else:
                st.info("비교할 이전 기록이 없거나 값이 부족합니다.")

        shown = [ (k, v) for k, v in (extra_vals or {}).items() if entered(v) ]
        if shown:
            st.markdown("### 🧬 암별 디테일 수치")
            for k, v in shown:
                st.write(f"- {k}: {v}")

        fs = food_suggestions(vals, anc_place)
        if fs:
            st.markdown("### 🥗 음식 가이드 (계절/레시피 포함)")
            for f in fs: st.markdown(f)
    elif mode == "소아(일상/호흡기)":
        st.info("위 위험도 배너를 참고하세요.")
    else:
        st.success("선택한 감염질환 요약을 보고서에 포함했습니다.")

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
    elif mode == "소아(일상/호흡기)":
        buf.append(f"- 소아 주제: {ped_topic}\n")
        def _ent(x):
            try: return x is not None and float(x)!=0
            except: return False
        buf.append("\n## 소아 공통 입력\n")
        if _ent(age_m): buf.append(f"- 나이(개월): {int(age_m)}\n")
        if _ent(temp_c): buf.append(f"- 체온: {float(temp_c):1.1f}℃\n")
        if _ent(rr): buf.append(f"- 호흡수: {int(rr)}/분\n")
        if _ent(spo2): buf.append(f"- SpO₂: {int(spo2)}%\n")
        if _ent(urine_24h): buf.append(f"- 24시간 소변 횟수: {int(urine_24h)}\n")
        if _ent(retraction): buf.append(f"- 흉곽 함몰: {int(retraction)}\n")
        if _ent(nasal_flaring): buf.append(f"- 콧벌렁임: {int(nasal_flaring)}\n")
        if _ent(apnea): buf.append(f"- 무호흡: {int(apnea)}\n")
    else:
        buf.append(f"- 소아 감염질환: {infect_sel}\n")
        info = PED_INFECT.get(infect_sel, {})
        buf.append("  - 핵심: " + info.get("핵심","") + "\n")
        buf.append("  - 진단: " + info.get("진단","") + "\n")
        buf.append("  - 특징: " + info.get("특징","") + "\n")

    if mode == "일반/암":
        buf.append("\n## 입력 수치(기본)\n")
        for k in ORDER:
            v = vals.get(k)
            if entered(v):
                if k == LBL_CRP: buf.append(f"- {k}: {float(v):.2f}\n")
                else: buf.append(f"- {k}: {_fmt(k, v)}\n")

        # 변화 비교 요약
        if nickname and "records" in st.session_state and st.session_state.records.get(nickname):
            cmp_lines = compare_with_previous(nickname, {k: vals.get(k) for k in ORDER if entered(vals.get(k))})
            if cmp_lines:
                buf.append("\n## 수치 변화 비교(이전 대비)\n")
                for l in cmp_lines: buf.append(l + "\n")

        if extra_vals:
            buf.append("\n## 암별 디테일 수치\n")
            for k, v in extra_vals.items():
                if entered(v): buf.append(f"- {k}: {v}\n")
        if meds:
            buf.append("\n## 항암제 요약\n")
            for line in summarize_meds(meds): buf.append(line + "\n")

        _foods_for_report = food_suggestions(vals, anc_place)
        if _foods_for_report:
            buf.append("\n## 음식 가이드(계절/레시피 포함)\n")
            for f in _foods_for_report:
                # strip markdown links for txt/pdf readability? keep as is
                buf.append(f + "\n")

    if extras.get("abx"):
        buf.append("\n## 항생제\n")
        for l in abx_summary(extras["abx"]): buf.append(l + "\n")

    buf.append(f"\n- ANC 장소: {anc_place}\n")
    buf.append("\n> " + DISCLAIMER + "\n")
    report_md = "".join(buf)

    # Downloads
    st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"),
                       file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                       mime="text/markdown")

    st.download_button("📄 보고서(.txt) 다운로드", data=report_md.encode("utf-8"),
                       file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                       mime="text/plain")

    # ===== PDF (font-locked) =====
    FONT_PATH_REG = os.path.join("fonts", "NanumGothic-Regular.ttf")
    FONT_PATH_B   = os.path.join("fonts", "NanumGothic-Bold.ttf")
    FONT_PATH_XB  = os.path.join("fonts", "NanumGothic-ExtraBold.ttf")

    def md_to_pdf_bytes_fontlocked(md_text: str) -> bytes:
        if not os.path.exists(FONT_PATH_REG):
            raise FileNotFoundError("fonts/NanumGothic-Regular.ttf 가 없습니다. 폰트를 넣어주세요.")
        font_name = "NanumGothic"
        pdfmetrics.registerFont(TTFont(font_name, FONT_PATH_REG))
        bold_name = None
        if os.path.exists(FONT_PATH_XB):
            try:
                pdfmetrics.registerFont(TTFont("NanumGothic-ExtraBold", FONT_PATH_XB))
                bold_name = "NanumGothic-ExtraBold"
            except Exception:
                pass
        if not bold_name and os.path.exists(FONT_PATH_B):
            try:
                pdfmetrics.registerFont(TTFont("NanumGothic-Bold", FONT_PATH_B))
                bold_name = "NanumGothic-Bold"
            except Exception:
                pass

        buf_pdf = BytesIO()
        doc = SimpleDocTemplate(buf_pdf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                                topMargin=15*mm, bottomMargin=15*mm)
        styles = getSampleStyleSheet()
        # force fonts
        for s in ['Title','Heading1','Heading2','BodyText']:
            if s in styles.byName:
                styles[s].fontName = bold_name or font_name if s != 'BodyText' else font_name
        story = []
        for line in md_text.splitlines():
            line = line.rstrip("\n")
            if not line.strip():
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

    if HAS_PDF:
        try:
            pdf_bytes = md_to_pdf_bytes_fontlocked(report_md)
            st.info("PDF 생성 시 사용한 폰트: NanumGothic-Regular.ttf (제목은 Bold/ExtraBold가 있으면 자동 적용)")
            st.download_button("🖨️ 보고서(.pdf) 다운로드", data=pdf_bytes,
                               file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                               mime="application/pdf")
        except FileNotFoundError as e:
            st.warning(str(e))
        except Exception as e:
            st.error(f"PDF 생성 중 오류: {e}")
    else:
        st.info("PDF 모듈(reportlab)이 없어 .pdf 버튼이 숨겨졌습니다. (pip install reportlab)")

    # Save session record
    if nickname and nickname.strip():
        rec = {
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": mode,
            "group": group,
            "cancer": cancer,
            "infect": infect_sel,
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
    if "records" in st.session_state and st.session_state.records:
        sel = st.selectbox("별명 선택", sorted(st.session_state.records.keys()))
        rows = st.session_state.records.get(sel, [])
        if rows:
            data = [ {"ts": r["ts"], **{k: r["labs"].get(k) for k in [LBL_WBC, LBL_Hb, LBL_PLT, LBL_CRP, LBL_ANC]}} for r in rows ]
            import pandas as pd  # local import
            df = pd.DataFrame(data).set_index("ts")
            st.line_chart(df.dropna(how="all"))
        else:
            st.info("선택한 별명의 저장 기록이 없습니다.")
    else:
        st.info("아직 저장된 기록이 없습니다.")


# ===== Compact Drug Encyclopedia (Search + Paged) =====
st.markdown("---")
st.header("📚 약물 사전 (스크롤 최소화 뷰어)")

with st.expander("열기 / 닫기", expanded=False):
    st.caption("빠르게 찾아보고 싶은 약을 검색하세요. 결과는 페이지로 나눠서 보여줍니다.")
    view_tab1, view_tab2 = st.tabs(["항암제 사전", "항생제 사전"])

    # ---- 항암제 사전 ----
    with view_tab1:
        # Build searchable rows from ANTICANCER
        ac_rows = []
        for k, v in ANTICANCER.items():
            alias = v.get("alias","")
            aes = ", ".join(v.get("aes", []))
            # 간단 태그 추정
            tags = []
            key = k.lower()
            if any(x in key for x in ["mab","nib","pembro","nivo","tuzu","zumab"]):
                tags.append("표적/면역")
            if k in ["Imatinib","Dasatinib","Nilotinib","Sunitinib","Pazopanib","Regorafenib","Lenvatinib","Sorafenib"]:
                tags.append("TKI")
            if k in ["Pembrolizumab","Nivolumab","Trastuzumab","Bevacizumab"]:
                tags.append("면역/항체")
            ac_rows.append({
                "약물": k, "한글명": alias, "부작용": aes, "태그": ", ".join(tags)
            })

        if HAS_PD:
            import pandas as pd
            ac_df = pd.DataFrame(ac_rows)
        else:
            ac_df = None

        q = st.text_input("🔎 약물명/한글명/부작용/태그 검색", key="drug_search_ac", placeholder="예: MTX, 간독성, 면역, TKI ...")
        page_size = st.selectbox("페이지 크기", [5, 10, 15, 20], index=1, key="ac_page_size")
        if HAS_PD and ac_df is not None:
            fdf = ac_df.copy()
            if q:
                ql = q.strip().lower()
                mask = (
                    fdf["약물"].str.lower().str.contains(ql) |
                    fdf["한글명"].str.lower().str.contains(ql) |
                    fdf["부작용"].str.lower().str.contains(ql) |
                    fdf["태그"].str.lower().str.contains(ql)
                )
                fdf = fdf[mask]
            total = len(fdf)
            st.caption(f"검색 결과: {total}건")
            if total == 0:
                st.info("검색 결과가 없습니다.")
            else:
                # pagination
                max_page = (total - 1) // page_size + 1
                cur_page = st.number_input("페이지", min_value=1, max_value=max_page, value=1, step=1, key="ac_page")
                start = (cur_page - 1) * page_size
                end = start + page_size
                show_df = fdf.iloc[start:end]
                # Render compact cards
                for _, row in show_df.iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{row['약물']}** · {row['한글명']}")
                        st.caption(f"태그: {row['태그'] if row['태그'] else '—'}")
                        st.write("부작용: " + (row["부작용"] if row["부작용"] else "—"))
        else:
            st.info("pandas 설치 시 검색/페이지 기능이 활성화됩니다.")

    # ---- 항생제 사전 ----
    with view_tab2:
        abx_rows = []
        for cat, tips in ABX_GUIDE.items():
            abx_rows.append({
                "계열": cat, "주의사항": ", ".join(tips)
            })
        if HAS_PD:
            import pandas as pd
            abx_df = pd.DataFrame(abx_rows)
        else:
            abx_df = None

        q2 = st.text_input("🔎 계열/주의사항 검색", key="drug_search_abx", placeholder="예: QT, 광과민, 와파린 ...")
        page_size2 = st.selectbox("페이지 크기", [5, 10, 15, 20], index=1, key="abx_page_size")
        if HAS_PD and abx_df is not None:
            fdf2 = abx_df.copy()
            if q2:
                ql2 = q2.strip().lower()
                mask2 = (
                    fdf2["계열"].str.lower().str.contains(ql2) |
                    fdf2["주의사항"].str.lower().str.contains(ql2)
                )
                fdf2 = fdf2[mask2]
            total2 = len(fdf2)
            st.caption(f"검색 결과: {total2}건")
            if total2 == 0:
                st.info("검색 결과가 없습니다.")
            else:
                max_page2 = (total2 - 1) // page_size2 + 1
                cur_page2 = st.number_input("페이지", min_value=1, max_value=max_page2, value=1, step=1, key="abx_page")
                start2 = (cur_page2 - 1) * page_size2
                end2 = start2 + page_size2
                show_df2 = fdf2.iloc[start2:end2]
                for _, row in show_df2.iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{row['계열']}**")
                        st.write("주의사항: " + (row["주의사항"] if row["주의사항"] else "—"))
        else:
            st.info("pandas 설치 시 검색/페이지 기능이 활성화됩니다.")

# ===== Sticky disclaimer =====
st.caption("📱 직접 타이핑 입력 / 모바일 줄꼬임 방지 / 암별·소아·희귀암 패널 + 감염질환 표 포함. 공식카페: https://cafe.naver.com/bloodmap")
st.markdown("> " + DISCLAIMER)

