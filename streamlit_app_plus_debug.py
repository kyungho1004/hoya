import json
from datetime import datetime
from io import StringIO

import pandas as pd
import streamlit as st

# =========================
# 🧭 기본 설정 & 전역 상태
# =========================
st.set_page_config(
    page_title="피수치 자동 해석기 | BloodMap",
    page_icon="🩸",
    layout="centered",
)

st.title("🔬 피수치 자동 해석기 by Hoya/GPT")
st.caption("자문: Hoya/GPT · 피수치 가이드 공식카페 · 본 도구는 교육/정보 제공용이며 진단/치료를 대체하지 않습니다.")

# 조회수 카운터
if "views" not in st.session_state:
    st.session_state.views = 0
st.session_state.views += 1
st.toast(f"누적 조회수: {st.session_state.views}", icon="👀")

# 저장소 초기화
if "records" not in st.session_state:
    # records 구조: {nickname: [{ts, category, labs:{...}, extras:{...}}]}
    st.session_state.records = {}

# =========================
# 🔧 유틸 함수
# =========================
LAB_ORDER = [
    ("WBC", "WBC (백혈구)"),
    ("Hb", "Hb (혈색소)"),
    ("PLT", "혈소판 (PLT)"),
    ("ANC", "ANC (호중구)"),
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
    ("Cr", "Creatinine (Cr)"),
    ("UA", "Uric Acid (UA)"),
    ("TB", "Total Bilirubin (TB)"),
    ("BUN", "BUN"),
    ("BNP", "BNP (선택)"),
]

FOODS = {
    "Albumin_low": ["달걀", "연두부", "흰살 생선", "닭가슴살", "귀리죽"],
    "K_low": ["바나나", "감자", "호박죽", "고구마", "오렌지"],
    "Hb_low": ["소고기", "시금치", "두부", "달걀 노른자", "렌틸콩"],
    "Na_low": ["전해질 음료", "미역국", "바나나", "오트밀죽", "삶은 감자"],
    "Ca_low": ["연어 통조림", "두부", "케일", "브로콜리", "(참깨 제외)"]
}

ANTICANCER = {
    "6-MP": {
        "alias": "6-머캅토퓨린",
        "aes": ["골수억제", "간수치 상승", "구내염", "오심"],
        "warn": ["황달/진한 소변 시 진료", "감염 징후 시 즉시 연락"],
        "ix": ["알로푸리놀 병용 시 감량 필요 가능성", "와파린 효과 변동"]
    },
    "MTX": {
        "alias": "메토트렉세이트",
        "aes": ["골수억제", "간독성", "신독성", "구내염", "광과민"],
        "warn": ["탈수 시 독성↑", "고용량 후 류코보린 구조화"],
        "ix": ["NSAIDs/아스피린/TMP-SMX 병용 시 독성↑", "PPI 일부와 상호작용"]
    },
    "ATRA": {
        "alias": "베사노이드(트레티노인)",
        "aes": ["분화증후군", "발열", "피부/점막 건조", "두통"],
        "warn": ["호흡곤란·부종·저혈압 등 분화증후군 의심 시 즉시 병원"],
        "ix": ["테트라사이클린계와 병용 시 가성 뇌종양 위험"]
    },
    "ARA-C": {
        "alias": "시타라빈",
        "aes": ["골수억제", "발열", "구내염", "HDAC: 신경독성/소뇌실조"],
        "warn": ["HDAC 시 신경학적 증상 즉시 보고"],
        "ix": ["리팜핀 등 효소유도제 상호작용 가능"]
    },
    "G-CSF": {
        "alias": "그라신(필그라스팀 등)",
        "aes": ["골통/근육통", "주사부위 반응", "드물게 비장비대"],
        "warn": ["좌상복부 통증·어지럼 시 평가 필요"],
        "ix": []
    },
    "Hydroxyurea": {
        "alias": "하이드록시우레아",
        "aes": ["골수억제", "피부색소침착", "궤양"],
        "warn": ["임신 회피"],
        "ix": []
    },
    "Daunorubicin": {
        "alias": "도우노루비신",
        "aes": ["골수억제", "심독성", "오심/구토", "점막염"],
        "warn": ["누적용량 심기능 모니터링"],
        "ix": ["트라스투주맙 등과 병용 시 심독성↑"]
    },
    "Idarubicin": {
        "alias": "이달루비신",
        "aes": ["골수억제", "심독성", "점막염"],
        "warn": ["심기능 모니터링"],
        "ix": []
    },
    "Mitoxantrone": {
        "alias": "미토잔트론",
        "aes": ["골수억제", "심독성", "청록색 소변"],
        "warn": ["심기능"],
        "ix": []
    },
    "Cyclophosphamide": {
        "alias": "사이클로포스파미드",
        "aes": ["골수억제", "출혈성 방광염", "탈모"],
        "warn": ["수분섭취·메스나 병용 시 방광 보호"],
        "ix": ["CYP 상호작용"]
    },
    "Etoposide": {
        "alias": "에토포사이드",
        "aes": ["골수억제", "저혈압(주입)"],
        "warn": [],
        "ix": []
    },
    "Topotecan": {
        "alias": "토포테칸",
        "aes": ["골수억제", "설사"],
        "warn": [],
        "ix": []
    },
    "Fludarabine": {
        "alias": "플루다라빈",
        "aes": ["면역억제", "감염 위험↑", "혈구감소"],
        "warn": ["PCP 예방 고려(의료진 지시 따름)"],
        "ix": []
    },
    "Vincristine": {
        "alias": "빈크리스틴(비크라빈 유사)",
        "aes": ["말초신경병증", "변비/장폐색"],
        "warn": ["IT(척수강) 투여 금지"],
        "ix": ["CYP3A 상호작용"]
    },
}

ABX_GUIDE = {
    "페니실린계": ["발진/설사", "와파린 효과↑ 가능"],
    "세팔로스포린계": ["설사", "알코올과 병용 시 플러싱 일부"],
    "마크롤라이드": ["QT 연장 가능", "CYP 상호작용"],
    "플루오로퀴놀론": ["힘줄염·광과민", "QT 연장"],
    "카바페넴": ["경련 위험(고용량/신부전)", "광범위 스펙트럼"],
    "TMP-SMX": ["고칼륨혈증", "골수억제", "MTX와 병용 주의"],
    "메트로니다졸": ["금주", "금속맛/구역"],
    "반코마이신": ["Red man syndrome(주입속도)", "신독성(고농도)"]
}

def entered(val):
    # number_input 기본값 0.0을 미입력으로 취급
    try:
        return val is not None and float(val) > 0
    except Exception:
        return False

@st.cache_data(show_spinner=False)
def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# =========================
# 📦 데이터 불러오기/내보내기
# =========================
st.markdown("---")
with st.expander("📂 데이터 관리 (불러오기/내보내기)"):
    c1, c2 = st.columns(2)
    with c1:
        up = st.file_uploader("저장 JSON 불러오기", type=["json"])
        if up is not None:
            try:
                data = json.loads(up.read().decode("utf-8"))
                if isinstance(data, dict):
                    st.session_state.records.update(data)
                    st.success("불러오기 완료")
                else:
                    st.error("JSON 형식이 올바르지 않습니다.")
            except Exception as e:
                st.error(f"불러오기 실패: {e}")
    with c2:
        dump = json.dumps(st.session_state.records, ensure_ascii=False, indent=2)
        st.download_button(
            "💾 전체 기록 JSON 다운로드",
            data=dump.encode("utf-8"),
            file_name="bloodmap_records.json",
            mime="application/json",
        )

# =========================
# 👤 별명(닉네임) 및 카테고리
# =========================
col_nick = st.columns(1)[0]
nickname = col_nick.text_input("별명(닉네임) — 저장/그래프에 쓰입니다.", placeholder="예: 홍길동")
if nickname.strip() and nickname in st.session_state.records:
    st.info("이미 존재하는 별명입니다. 저장 시 기존 기록에 추가됩니다.")

category = st.radio(
    "카테고리 선택",
    ["일반 해석", "항암치료", "항생제", "투석 환자", "당뇨 환자"],
)

st.markdown("---")

# =========================
# 🧪 입력 컴포넌트 (모바일 1열, 고정 순서)
# =========================
def render_lab_inputs(include_bnp=True):
    values = {}
    for key, label in LAB_ORDER:
        if key == "BNP" and not include_bnp:
            continue
        # 0을 미입력으로 간주
        values[key] = st.number_input(label, min_value=0.0, step=0.1, format="%.2f")
    return values

# 공통 경고/가이드 생성기
def build_lab_interpretation(labs: dict) -> list:
    out = []
    # 예시 해석 (입력한 값만)
    if entered(labs.get("WBC")):
        v = labs["WBC"]
        if v < 4:
            out.append(f"WBC {v:.1f}: 낮음 → 면역저하·감염 위험↑")
        elif v > 10:
            out.append(f"WBC {v:.1f}: 높음 → 감염/염증 가능")
        else:
            out.append(f"WBC {v:.1f}: 정상 범위")

    if entered(labs.get("Hb")):
        v = labs["Hb"]
        if v < 12:
            out.append(f"Hb {v:.1f}: 낮음 → 빈혈 가능")
        else:
            out.append(f"Hb {v:.1f}: 정상 범위")

    if entered(labs.get("PLT")):
        v = labs["PLT"]
        if v < 150:
            out.append(f"혈소판 {v:.1f}: 낮음 → 출혈 위험")
        else:
            out.append(f"혈소판 {v:.1f}: 정상 범위")

    if entered(labs.get("ANC")):
        v = labs["ANC"]
        if v < 500:
            out.append(f"ANC {v:.0f}: 심한 호중구감소 → 즉시 감염예방 수칙")
        elif v < 1500:
            out.append(f"ANC {v:.0f}: 경~중등도 감소")
        else:
            out.append(f"ANC {v:.0f}: 정상 범위")

    if entered(labs.get("Albumin")):
        v = labs["Albumin"]
        if v < 3.5:
            out.append(f"Albumin {v:.2f}: 낮음 → 영양 부족/염증/간질환 가능")
        else:
            out.append(f"Albumin {v:.2f}: 정상 범위")

    if entered(labs.get("Glucose")):
        v = labs["Glucose"]
        if v >= 200:
            out.append(f"Glucose {v:.1f}: 고혈당 (식후/스트레스 여부 확인)")
        elif v < 70:
            out.append(f"Glucose {v:.1f}: 저혈당 주의")
        else:
            out.append(f"Glucose {v:.1f}: 정상 범위")

    if entered(labs.get("CRP")):
        v = labs["CRP"]
        if v > 0.5:
            out.append(f"CRP {v:.2f}: 상승 → 염증/감염 의심")
        else:
            out.append(f"CRP {v:.2f}: 정상 범위")

    if entered(labs.get("BUN")) and entered(labs.get("Cr")):
        bun = labs["BUN"]
        cr = labs["Cr"]
        ratio = bun / cr if cr > 0 else None
        if ratio:
            if ratio > 20:
                out.append(f"BUN/Cr {ratio:.1f}: 탈수 의심")
            elif ratio < 10:
                out.append(f"BUN/Cr {ratio:.1f}: 간질환/영양 상태 등 고려")

    return out

# 음식 추천
def build_food_suggestions(labs: dict) -> list:
    foods = []
    if entered(labs.get("Albumin")) and labs["Albumin"] < 3.5:
        foods.append("알부민 낮음 → 추천: " + ", ".join(FOODS["Albumin_low"]))
    if entered(labs.get("K")) and labs["K"] < 3.5:
        foods.append("칼륨 낮음 → 추천: " + ", ".join(FOODS["K_low"]))
    if entered(labs.get("Hb")) and labs["Hb"] < 12:
        foods.append("Hb 낮음 → 추천: " + ", ".join(FOODS["Hb_low"]))
    if entered(labs.get("Na")) and labs["Na"] < 135:
        foods.append("나트륨 낮음 → 추천: " + ", ".join(FOODS["Na_low"]))
    if entered(labs.get("Ca")) and labs["Ca"] < 8.5:
        foods.append("칼슘 낮음 → 추천: " + ", ".join(FOODS["Ca_low"]))

    # 철분제 경고 (항암/백혈병 환자)
    foods.append("⚠️ 항암 치료 중/백혈병 환자는 철분제 복용을 피하거나 반드시 주치의와 상의하세요.")
    foods.append("⚠️ 철분제+비타민C 병용 시 흡수↑ → 복용은 반드시 의료진과 상의 후 결정.")

    # ANC 식이 위생 가이드
    if entered(labs.get("ANC")) and labs["ANC"] < 500:
        foods.append("🧼 호중구 감소 시: 생채소 금지, 모든 음식은 익혀서 섭취(전자레인지 30초+), 멸균/살균 식품 권장, 조리 후 2시간 지난 음식은 폐기, 껍질 과일은 주치의와 상의 후 섭취.")

    return foods

# 항암제 입력 위젯
def render_anticancer_inputs():
    st.subheader("💊 항암제/보조제 입력 (알약 개수 또는 주사 여부)")
    meds = {}
    c_arac = st.checkbox("ARA-C 사용", value=False)
    if c_arac:
        meds["ARA-C"] = {
            "use": True,
            "form": st.selectbox("ARA-C 제형", ["정맥(IV)", "피하(SC)", "고용량(HDAC)"]),
            "dose": st.number_input("ARA-C 용량/일(임의 입력)", min_value=0.0, step=0.1),
        }
    for key in ["6-MP", "MTX", "ATRA", "G-CSF", "Hydroxyurea", "Daunorubicin", "Idarubicin", "Mitoxantrone", "Cyclophosphamide", "Etoposide", "Topotecan", "Fludarabine", "Vincristine"]:
        use = st.checkbox(f"{key} ({ANTICANCER[key]['alias']}) 사용", value=False)
        if use:
            meds[key] = {
                "use": True,
                "dose_or_tabs": st.number_input(f"{key} 투여량/알약 개수(소수 허용)", min_value=0.0, step=0.1),
            }
    return meds

# 항암제 부작용/상호작용 요약 생성
def summarize_anticancer(meds: dict) -> list:
    out = []
    for k, v in meds.items():
        info = ANTICANCER.get(k)
        if not info:
            continue
        line = f"• {k} ({info['alias']}): AE {', '.join(info['aes'])}"
        if info['ix']:
            line += f" | 상호작용: {', '.join(info['ix'])}"
        if info['warn']:
            line += f" | 주의: {', '.join(info['warn'])}"
        if k == "ARA-C" and isinstance(v, dict) and v.get("form"):
            line += f" | 제형: {v['form']}"
        out.append(line)
    return out

# 항생제 안내
def render_antibiotic_inputs():
    st.subheader("🧪 항생제 선택 (세대 구분 없이 간단 설명)")
    options = list(ABX_GUIDE.keys())
    sel = st.multiselect("사용 중인 항생제", options)
    notes = []
    for s in sel:
        notes.append(f"• {s}: {', '.join(ABX_GUIDE[s])}")
    return {"abx": sel, "notes": notes}

# 해열제/발열 가이드 (요약)
FEVER_GUIDE = (
    "🌡️ 발열 가이드: 38.0~38.5℃ 해열제+경과관찰, 38.5℃ 이상 병원 연락, 39.0℃ 이상 즉시 병원. "
    "특히 호중구감소(ANC < 500) 동반 발열은 응급상황으로 간주하세요."
)

# 이뇨제 여부
def render_diuretic_input():
    on = st.checkbox("이뇨제 복용 중", value=False)
    return on

# 투석 환자 추가 입력
def render_dialysis_extras():
    st.subheader("🫧 투석 환자 추가 항목")
    urine = st.number_input("하루 소변량 (mL)", min_value=0.0, step=10.0)
    hd_today = st.checkbox("오늘 투석 시행")
    post_delta = st.number_input("투석 후 체중 변화 (kg)", min_value=-10.0, max_value=10.0, step=0.1)
    return {"urine_ml": urine, "hd_today": hd_today, "post_hd_weight_delta": post_delta}

# 당뇨 환자 입력
def render_diabetes_inputs():
    st.subheader("🍚 당뇨 지표")
    fpg = st.number_input("식전 혈당 (mg/dL)", min_value=0.0, step=1.0)
    pp1 = st.number_input("식후 1시간 혈당 (mg/dL)", min_value=0.0, step=1.0)
    pp2 = st.number_input("식후 2시간 혈당 (mg/dL)", min_value=0.0, step=1.0)
    a1c = st.number_input("HbA1c (%)", min_value=0.0, step=0.1, format="%.1f")
    tips = []
    if entered(fpg) and fpg >= 126:
        tips.append("식전 고혈당: 저당 식이·규칙적 식사 간격")
    if entered(pp2) and pp2 >= 200:
        tips.append("식후 고혈당: 식사 탄수 조절·걷기")
    if entered(a1c) and a1c >= 6.5:
        tips.append("HbA1c 상승: 장기 혈당 관리 필요")
    return {"FPG": fpg, "PP1h": pp1, "PP2h": pp2, "HbA1c": a1c, "tips": tips}

# =========================
# 🧾 본문 UI
# =========================

labs = {}
extras = {}
meds = {}
notes_sections = []

if category in ("일반 해석", "항암치료", "투석 환자"):
    labs = render_lab_inputs(include_bnp=True)

if category == "항암치료":
    st.markdown("### 약물 요약")
    meds = render_anticancer_inputs()
    diuretic_on = render_diuretic_input()
    if diuretic_on:
        notes_sections.append("💧 이뇨제 복용 중: 탈수·저나트륨/저칼륨·크램프 주의. BUN/Cr 상승 시 수분 상태 확인.")
    st.info(FEVER_GUIDE)

elif category == "항생제":
    abx = render_antibiotic_inputs()
    extras.update(abx)
    st.info("💡 항생제는 임의 중단/변경 금지. 복용 시간 규칙, 충분한 수분 섭취, 이상 증상 시 의료진과 상의.")

elif category == "투석 환자":
    extras.update(render_dialysis_extras())
    diuretic_on = render_diuretic_input()
    if diuretic_on:
        notes_sections.append("💧 이뇨제 복용 중: 전해질 이상 및 탈수 위험. 경련·어지럼 증상 시 평가.")

elif category == "당뇨 환자":
    extras.update(render_diabetes_inputs())

# =========================
# ▶️ 해석하기
# =========================
run = st.button("🔎 해석하기", use_container_width=True)

report_md = ""
if run:
    st.subheader("📋 해석 결과")

    # 1) 수치 해석 (입력한 값만)
    if labs:
        interp = build_lab_interpretation(labs)
        if interp:
            for line in interp:
                st.write("- " + line)
        else:
            st.write("- 입력된 수치가 없습니다.")

        # 음식 추천
        food = build_food_suggestions(labs)
        if food:
            st.markdown("### 🥗 음식 가이드")
            for f in food:
                st.write("- " + f)

    # 2) 항암제 요약
    if meds:
        st.markdown("### 💊 항암제 부작용·상호작용 요약")
        for line in summarize_anticancer(meds):
            st.write(line)

    # 3) 항생제 요약
    if extras.get("notes"):
        st.markdown("### 🧪 항생제 주의 요약")
        for n in extras["notes"]:
            st.write(n)

    # 4) 추가 노트
    if notes_sections:
        st.markdown("### 📌 추가 노트")
        for n in notes_sections:
            st.write("- " + n)

    # 5) 보고서(.md) 생성 (입력 항목만 포함)
    buf = [
        f"# 피수치 자동 해석 보고서\n",
        f"- 생성시각: {now_ts()}\n",
        f"- 별명: {nickname or '미입력'}\n",
        f"- 카테고리: {category}\n\n",
        "## 수치 해석\n",
    ]
    if labs:
        for k, label in LAB_ORDER:
            if k in labs and entered(labs[k]):
                buf.append(f"- {label}: {labs[k]}\n")
    if meds:
        buf.append("\n## 항암제 요약\n")
        for line in summarize_anticancer(meds):
            buf.append(f"- {line}\n")
    if extras.get("notes"):
        buf.append("\n## 항생제 주의\n")
        for n in extras["notes"]:
            buf.append(f"- {n}\n")
    if extras.get("tips"):
        buf.append("\n## 당뇨 팁\n")
        for t in extras["tips"]:
            buf.append(f"- {t}\n")
    if notes_sections:
        buf.append("\n## 추가 노트\n")
        for n in notes_sections:
            buf.append(f"- {n}\n")

    buf.append("\n---\n본 보고서는 교육 용도로 제공되며, 치료·진단은 담당 의료진의 안내를 따르세요.\n")
    report_md = "".join(buf)

    st.download_button(
        "📥 보고서(.md) 다운로드",
        data=report_md.encode("utf-8"),
        file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown",
        use_container_width=True,
    )

    # 6) 저장 유도
    if nickname.strip():
        if st.checkbox("📝 결과를 이 별명으로 저장하시겠습니까?", value=True):
            rec = {
                "ts": now_ts(),
                "category": category,
                "labs": {k: v for k, v in labs.items() if entered(v)} if labs else {},
                "extras": extras,
            }
            st.session_state.records.setdefault(nickname, []).append(rec)
            st.success("저장되었습니다. 아래 그래프에서 추이를 확인하세요.")
    else:
        st.warning("별명을 입력하면 추이 그래프를 사용할 수 있어요.")

# =========================
# 📈 추이 그래프 (WBC, Hb, PLT, CRP, ANC)
# =========================
st.markdown("---")
st.subheader("📈 별명별 추이 그래프")

if st.session_state.records:
    nicknames = sorted(list(st.session_state.records.keys()))
    sel_nick = st.selectbox("그래프 볼 별명 선택", nicknames)
    rows = st.session_state.records.get(sel_nick, [])
    if rows:
        data = []
        for r in rows:
            row = {"ts": r["ts"]}
            for k in ["WBC", "Hb", "PLT", "CRP", "ANC"]:
                if r.get("labs") and k in r["labs"]:
                    row[k] = r["labs"][k]
            data.append(row)
        if data:
            df = pd.DataFrame(data).set_index("ts")
            st.line_chart(df)
        else:
            st.info("그래프로 표시할 수치가 아직 없습니다. 해석을 저장해보세요.")
    else:
        st.info("선택한 별명의 저장 기록이 없습니다.")
else:
    st.info("아직 저장된 기록이 없습니다. 해석 후 저장해보세요.")

# =========================
# 🔚 푸터 노트
# =========================
st.markdown(
    """
**제작**: Hoya/GPT  
**표시 원칙**: *입력한 항목만* 결과에 표시됩니다.  
**주의**: 약물(항암제/항생제/해열제/이뇨제)은 반드시 **담당 의료진 지시**를 우선하세요.
"""
)

