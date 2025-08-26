
import json
from datetime import datetime
import streamlit as st

# Optional pandas for charts (app works without it)
try:
    import pandas as pd
    HAS_PD = True
except Exception:
    HAS_PD = False

# ========= PAGE / MOBILE TWEAKS =========
st.set_page_config(page_title="피수치 자동 해석기 by Hoya", layout="centered")
st.markdown(
    """
    <style>
    /* Mobile-friendly tweaks */
    .stTextArea textarea, .stNumberInput input, .stTextInput input {
        font-size: 16px !important;
    }
    .stButton>button { width: 100%; height: 48px; }
    .stDownloadButton>button { width: 100%; height: 44px; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🩸 피수치 자동 해석기")
st.markdown("👤 **제작자: Hoya / 자문: GPT**")

# ========= CONSTANTS =========
# Order fixed (2025-08-25 확정 순서)
ORDER = [
    "WBC","Hb","PLT","ANC","Ca","P","Na","K","Albumin","Glucose",
    "Total Protein","AST","ALT","LDH","CRP","Cr","UA","TB","BUN","BNP"
]

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

# 음식 가이드 (5개씩)
FOODS = {
    "Albumin_low": ["달걀","연두부","흰살 생선","닭가슴살","귀리죽"],
    "K_low": ["바나나","감자","호박죽","고구마","오렌지"],
    "Hb_low": ["소고기","시금치","두부","달걀 노른자","렌틸콩"],
    "Na_low": ["전해질 음료","미역국","바나나","오트밀죽","삶은 감자"],
    "Ca_low": ["연어 통조림","두부","케일","브로콜리","(참깨 제외)"],
}

FEVER_GUIDE = "🌡️ 38.0~38.5℃ 해열제/경과, 38.5℃↑ 병원 연락, 39.0℃↑ 즉시 병원. (ANC<500 동반 발열=응급)"
IRON_WARNING = "⚠️ 항암/백혈병 환자는 철분제 복용을 피하세요. 철분제+비타민C 병용 시 흡수↑ → 반드시 주치의와 상의."

# ========= HELPERS =========
def init_state():
    if "records" not in st.session_state:
        st.session_state.records = {}

def entered(v):
    try:
        return v is not None and str(v) != "" and float(v) == float(v) and float(v) != 0 or float(v) == 0 and isinstance(v,(int,float))
    except Exception:
        return False

def parse_vals(s: str):
    s = (s or "").replace("，", ",").replace("\r\n", "\n").replace("\r", "\n")
    s = s.strip("\n ")
    if not s:
        return [None]*len(ORDER)
    # comma-mode OR line-mode, preserve blanks
    tokens = [tok.strip() for tok in (s.split(",") if ("," in s and "\n" not in s) else s.split("\n"))]
    out = []
    for i in range(len(ORDER)):
        tok = tokens[i] if i < len(tokens) else ""
        try:
            out.append(float(tok) if tok != "" else None)
        except:
            out.append(None)
    return out

def interpret_labs(vals):
    l = dict(zip(ORDER, vals))
    out=[]
    def add(s): out.append("• " + s)

    if entered(l.get("WBC")):
        add(f"WBC {l['WBC']}: " + ("낮음 → 감염 위험↑" if l["WBC"] < 4 else "높음 → 감염/염증 가능" if l["WBC"] > 10 else "정상"))
    if entered(l.get("Hb")):
        add(f"Hb {l['Hb']}: " + ("낮음 → 빈혈" if l["Hb"] < 12 else "정상"))
    if entered(l.get("PLT")):
        add(f"혈소판 {l['PLT']}: " + ("낮음 → 출혈 위험" if l["PLT"] < 150 else "정상"))
    if entered(l.get("ANC")):
        anc_val = l["ANC"]
        if anc_val < 500: anc_txt = "중증 감소(<500)"
        elif anc_val < 1500: anc_txt = "감소(<1500)"
        else: anc_txt = "정상"
        add(f"ANC {anc_val}: {anc_txt}")
    if entered(l.get("Albumin")):
        add(f"Albumin {l['Albumin']}: " + ("낮음 → 영양/염증/간질환 가능" if l["Albumin"] < 3.5 else "정상"))
    if entered(l.get("Glucose")):
        g = l["Glucose"]
        add(f"Glucose {g}: " + ("고혈당(≥200)" if g >= 200 else "저혈당(<70)" if g < 70 else "정상"))
    if entered(l.get("CRP")):
        add(f"CRP {l['CRP']}: " + ("상승 → 염증/감염 의심" if l["CRP"] > 0.5 else "정상"))
    if entered(l.get("BUN")) and entered(l.get("Cr")) and l["Cr"] not in (None, 0):
        ratio = l["BUN"] / l["Cr"]
        if ratio > 20: add(f"BUN/Cr {ratio:.1f}: 탈수 의심")
        elif ratio < 10: add(f"BUN/Cr {ratio:.1f}: 간질환/영양 고려")
    return out, l

def summarize_meds(meds: dict):
    out=[]
    for k, v in meds.items():
        info = ANTICANCER.get(k)
        if info:
            line = f"• {k} ({info['alias']}): AE {', '.join(info['aes'])}"
            if info.get("warn"): line += f" | 주의: {', '.join(info['warn'])}"
            if info.get("ix"): line += f" | 상호작용: {', '.join(info['ix'])}"
            if k == "ARA-C" and isinstance(v, dict) and v.get("form"):
                line += f" | 제형: {v['form']}"
            out.append(line)
    return out

def food_suggestions(l):
    foods=[]
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
        foods.append("🧼 호중구 감소: 생채소 금지, 익힌 음식(전자레인지 30초↑ 포함), 남은 음식 2시간 후 섭취 금지, 껍질 과일은 주치의와 상담.")
    foods.append(IRON_WARNING)
    return foods

# ========= STATE =========
init_state()

# ========= INPUT (SINGLE FORM - MOBILE SAFE) =========
st.divider()
st.header("1️⃣ 기본 정보")
col1, col2 = st.columns(2)
with col1:
    nickname = st.text_input("별명(저장/그래프용)", placeholder="예: 홍길동")
with col2:
    date_str = st.text_input("검사 날짜", value=datetime.now().strftime("%Y-%m-%d"))

st.divider()
st.header("2️⃣ 카테고리 선택")
category = st.radio("분류", ["일반 해석","항암치료","항생제","투석 환자","당뇨 환자"], horizontal=True)

st.divider()
st.header("3️⃣ 수치 입력 (줄바꿈 또는 쉼표 구분, 비워두면 제외)")
st.caption("ORDER: " + ", ".join(ORDER))
raw = st.text_area(
    "값을 순서대로 입력하세요",
    height=140,
    placeholder="예) 5.2, 11.8, 180, 1200, 8.6, 3.5, 140, 3.6, 3.2, 110, 6.6, 35, 40, 300, 0.2, 0.9, 4.5, 0.8, 18, 120"
)

# Category-specific inputs
meds, extras = {}, {}

if category == "항암치료":
    st.markdown("### 💊 항암제/보조제")
    if st.checkbox("ARA-C 사용"):
        meds["ARA-C"] = {
            "form": st.selectbox("ARA-C 제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"]),
            "dose": st.number_input("ARA-C 용량/일 (선택)", min_value=0.0, step=0.1)
        }
    for key in ["6-MP","MTX","ATRA","G-CSF","Hydroxyurea","Daunorubicin","Idarubicin","Mitoxantrone",
                "Cyclophosphamide","Etoposide","Topotecan","Fludarabine","Vincristine"]:
        if st.checkbox(f"{key} 사용"):
            meds[key] = {"dose_or_tabs": st.number_input(f"{key} 투여량/알약 개수(소수 허용)", min_value=0.0, step=0.1, key=f"dose_{key}")}
    if st.checkbox("이뇨제 복용 중"):
        extras["diuretic"] = True
    st.info(FEVER_GUIDE)

elif category == "항생제":
    st.markdown("### 🧪 항생제")
    extras["abx"] = st.multiselect("사용 중인 항생제", list(ABX_GUIDE.keys()))

elif category == "투석 환자":
    st.markdown("### 🫧 투석 추가 항목")
    extras["urine_ml"] = st.number_input("하루 소변량 (mL)", min_value=0.0, step=10.0)
    extras["hd_today"] = st.checkbox("오늘 투석 시행")
    extras["post_hd_weight_delta"] = st.number_input("투석 후 체중 변화 (kg)", min_value=-10.0, max_value=10.0, step=0.1)
    if st.checkbox("이뇨제 복용 중"):
        extras["diuretic"] = True

elif category == "당뇨 환자":
    st.markdown("### 🍚 당뇨 지표")
    extras["FPG"] = st.number_input("식전 혈당 (mg/dL)", min_value=0.0, step=1.0)
    extras["PP1h"] = st.number_input("식후 1시간 혈당 (mg/dL)", min_value=0.0, step=1.0)
    extras["PP2h"] = st.number_input("식후 2시간 혈당 (mg/dL)", min_value=0.0, step=1.0)
    extras["HbA1c"] = st.number_input("HbA1c (%)", min_value=0.0, step=0.1, format="%.1f")

# ========= RUN =========
st.divider()
run = st.button("🔎 해석하기", use_container_width=True)

if run:
    vals = parse_vals(raw)
    lines, labs = interpret_labs(vals)

    st.subheader("📋 해석 결과")
    if lines:
        for line in lines:
            st.write(line)
    else:
        st.info("입력된 수치가 없습니다. 최소 1개 이상 입력해주세요.")

    # 음식 가이드
    fs = food_suggestions(labs)
    if fs:
        st.markdown("### 🥗 음식 가이드")
        for f in fs:
            st.write("- " + f)

    # 항암제 요약
    if category == "항암치료" and meds:
        st.markdown("### 💊 항암제 부작용·상호작용 요약")
        for line in summarize_meds(meds):
            st.write(line)

    # 항생제 주의
    if category == "항생제" and extras.get("abx"):
        st.markdown("### 🧪 항생제 주의 요약")
        for a in extras["abx"]:
            st.write(f"• {a}: {', '.join(ABX_GUIDE[a])}")

    # 발열 가이드 항상 표시
    st.markdown("### 🌡️ 발열 가이드")
    st.write(FEVER_GUIDE)

    # 투석/이뇨제 간단 가이드
    if extras.get("diuretic"):
        st.warning("이뇨제 복용 중: 저칼륨/저나트륨/저칼슘 위험 및 탈수 위험 ↑ → 전해질/수분 상태 주의.")
    if category == "투석 환자":
        st.info("투석 환자: 칼륨/인/수분 관리가 중요합니다. 담당 의료진과 식이·체액 계획을 상의하세요.")

    # 보고서 (.md) - 입력한 값만 포함
    buf = [f"# BloodMap 보고서 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n",
           f"- 카테고리: {category}\n",
           f"- 별명: {nickname or ''}\n",
           f"- 검사일: {date_str}\n\n",
           "## 입력 수치\n"]
    for name, v in labs.items():
        if entered(v):
            buf.append(f"- {name}: {v}\n")
    report_md = "".join(buf)

    st.download_button(
        "📥 보고서(.md) 다운로드",
        data=report_md.encode("utf-8"),
        file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown"
    )

    # 저장 (별명 있는 경우만)
    if (nickname or "").strip():
        rec = {
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "category": category,
            "labs": {k: v for k, v in labs.items() if entered(v)},
            "meds": meds,
            "extras": extras
        }
        st.session_state.records.setdefault(nickname, []).append(rec)
        st.success("저장되었습니다. 아래 그래프에서 추이를 확인하세요.")
    else:
        st.info("별명을 입력하면 추이 그래프를 사용할 수 있어요.")

# ========= GRAPHS =========
st.markdown("---")
st.subheader("📈 별명별 추이 그래프 (WBC, Hb, PLT, CRP, ANC)")
if not HAS_PD:
    st.info("그래프는 pandas 설치 시 활성화됩니다. (pip install pandas)")
else:
    if st.session_state.records:
        sel = st.selectbox("별명 선택", sorted(st.session_state.records.keys()))
        rows = st.session_state.records.get(sel, [])
        if rows:
            data = []
            for r in rows:
                row = {"ts": r["ts"]}
                for k in ["WBC","Hb","PLT","CRP","ANC"]:
                    row[k] = r["labs"].get(k)
                data.append(row)
            df = pd.DataFrame(data).set_index("ts")
            st.line_chart(df.dropna(how="all"))
        else:
            st.info("선택한 별명의 저장 기록이 없습니다.")
    else:
        st.info("아직 저장된 기록이 없습니다.")
