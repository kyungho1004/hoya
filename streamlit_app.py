
# -*- coding: utf-8 -*-
# 피수치 자동 해석기 (BloodMap) - 암종류별 항암제/피수치 선택 통합판
# 제작: Hoya / 자문: GPT
import json
from datetime import datetime
import streamlit as st

# Optional pandas for charts
try:
    import pandas as pd
    HAS_PD = True
except Exception:
    HAS_PD = False

# ================== PAGE CONFIG ==================
st.set_page_config(page_title="피수치 자동 해석기 by Hoya", layout="centered")
st.title("🩸 피수치 자동 해석기")
st.markdown("👤 **제작: Hoya / 자문: GPT**")
st.caption("※ 교육·보조용 안내입니다. 치료 결정은 반드시 주치의와 상의하세요.")

# ================== CONSTANTS ==================
CORE_ORDER = [
    "WBC (백혈구)","Hb (혈색소)","PLT (혈소판)","ANC (절대 호중구 수)",
    "Ca (칼슘)","P (인)","Na (소디움)","K (포타슄)".replace("슄","슘"),
    "Albumin (알부민)","Glucose (혈당)","Total Protein (총단백)",
    "AST","ALT","LDH","CRP","Creatinine (Cr)",
    "Uric Acid (UA)","Total Bilirubin (TB)","BUN","BNP"
]
CBC_EXT = ["Reticulocyte (망상적혈구)","Hct (헤마토크릿)","MCV","MCH","MCHC","RDW"]
ALL_FIELDS = CORE_ORDER + CBC_EXT

# 키 정규화 맵 (표시 라벨 → 내부 키)
def norm_key(label: str) -> str:
    # 괄호 앞 키워드 또는 첫 단어를 내부 키로 사용 (공백 제거)
    if "(" in label:
        head = label.split("(")[0].strip()
    else:
        head = label.split()[0].strip()
    # 특례
    special = {
        "Creatinine": "Cr",
        "Uric": "Uric Acid",
        "Total": label,  # Total Protein / Total Bilirubin 그대로
        "Reticulocyte": "Reticulocyte",
        "Hct": "Hct",
    }
    for k, v in special.items():
        if head.startswith(k):
            return v
    return head

# 암종별 기본 피수치 세트 (요청 사항 반영)
CANCER_LAB_DEFAULTS = {
    "AML": CORE_ORDER,  # 예시와 동일
    "APL": CORE_ORDER,  # 기본 동일, 필요시 추후 응고계 추가 가능
    "ALL": CORE_ORDER,
    "CML": CORE_ORDER,  # 백혈구/혈소판 트래킹 중요
    "CLL": CORE_ORDER,  # 림프구↑ 특성, 기본 세트 유지
}

# 항암제 사전 (요약)
ANTICANCER = {
    "6-MP":{"alias":"6-머캅토퓨린","aes":["골수억제","간수치 상승","구내염","오심"],"warn":["황달/진한 소변 시 진료","감염 징후 즉시 연락"],"ix":["알로푸리놀 병용 감량 가능","와파린 효과 변동"]},
    "MTX":{"alias":"메토트렉세이트","aes":["골수억제","간독성","신독성","구내염","광과민"],"warn":["탈수 시 독성↑","고용량 후 류코보린"],"ix":["NSAIDs/TMP-SMX 병용 독성↑","일부 PPI 상호작용"]},
    "ATRA":{"alias":"트레티노인","aes":["분화증후군","발열","피부/점막 건조","두통"],"warn":["분화증후군 의심 시 즉시 병원"],"ix":["테트라사이클린계와 가성뇌압상승"]},
    "ARA-C":{"alias":"시타라빈","aes":["골수억제","발열","구내염","(HDAC) 신경독성"],"warn":["HDAC 시 신경증상 즉시 보고"],"ix":["효소유도제 상호작용"]},
    "G-CSF":{"alias":"그라신","aes":["골통/근육통","주사부위 반응","드물게 비장비대"],"warn":["좌상복부 통증 시 평가"],"ix":[]},
    "Hydroxyurea":{"alias":"하이드록시우레아","aes":["골수억제","피부색소침착","궤양"],"warn":["임신 회피"],"ix":[]},
    "Daunorubicin":{"alias":"도우노루비신","aes":["골수억제","심독성","오심/구토","점막염"],"warn":["누적용량·심기능 추적"],"ix":["심독성↑ 병용 주의"]},
    "Idarubicin":{"alias":"이달루비신","aes":["골수억제","심독성","점막염"],"warn":["심기능 추적"],"ix":[]},
    "Mitoxantrone":{"alias":"미토잔트론","aes":["골수억제","심독성","청록색 소변"],"warn":["심기능 추적"],"ix":[]},
    "Cyclophosphamide":{"alias":"사이클로포스파미드","aes":["골수억제","출혈성 방광염","탈모"],"warn":["수분섭취·메스나 고려"],"ix":["CYP 상호작용"]},
    "Etoposide":{"alias":"에토포사이드","aes":["골수억제","저혈압(주입)"],"warn":[],"ix":[]},
    "Topotecan":{"alias":"토포테칸","aes":["골수억제","설사"],"warn":[],"ix":[]},
    "Fludarabine":{"alias":"플루다라빈","aes":["면역억제","감염 위험↑","혈구감소"],"warn":["PCP 예방 고려"],"ix":[]},
    "Vincristine":{"alias":"빈크리스틴","aes":["말초신경병증","변비/장폐색"],"warn":["IT 금지"],"ix":["CYP3A 상호작용"]},
}

# 암종별 권장 항암제 프리셋
CANCER_REGIMENS = {
    "AML": {"recommended": ["ARA-C","Daunorubicin","Idarubicin","Mitoxantrone","Fludarabine","Etoposide","G-CSF","Hydroxyurea"],
            "notes": ["유도요법 중 범혈구감소 예상", "발열 + ANC<500 = 응급 연락"]},
    "APL": {"recommended": ["ATRA","Daunorubicin","Idarubicin","ARA-C"],
            "notes": ["분화증후군 증상(호흡곤란, 부종, 체중증가 등) 즉시 병원", "초기 출혈위험↑ → PLT/피브리노겐 관리"]},
    "ALL": {"recommended": ["Vincristine","Cyclophosphamide","Daunorubicin","ARA-C","MTX","6-MP","Etoposide","Topotecan","G-CSF"],
            "notes": ["구내염·간독성 모니터", "감염예방 주의(ANC)"]},
    "CML": {"recommended": ["Hydroxyurea","ARA-C","Cyclophosphamide","G-CSF"],
            "notes": ["표적치료제(TKI)는 별도 기록/관리(예: 이매티닙).", "WBC·PLT 추세 관리"]},
    "CLL": {"recommended": ["Fludarabine","Cyclophosphamide","Mitoxantrone","Etoposide"],
            "notes": ["면역억제 강함 → 감염 예방", "백신/예방약 상담"]},
    "기타(직접 선택)": {"recommended": list(ANTICANCER.keys()),
                  "notes": ["필요 약물만 선택하세요. 표적치료제(TKI 등)는 메모에 기록."]},
}

ABX_GUIDE = {
    "페니실린계":["발진/설사","와파린 효과↑ 가능"],
    "세팔로스포린계":["설사","일부 알코올 병용 시 플러싱 유사"],
    "마크롤라이드":["QT 연장","CYP 상호작용(클라리스/에리쓰)"],
    "플루오로퀴놀론":["힘줄염/파열","광과민","QT 연장"],
    "카바페넴":["경련 위험(고용량/신부전)","광범위 커버"],
    "TMP-SMX":["고칼륨혈증","골수억제","MTX 병용 주의"],
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
NEUTROPENIA_FOOD_RULE = "🧼 호중구 감소 시: 생채소 금지, 익혀 섭취(전자레인지 30초+), 남은 음식 2시간 이후 섭취 금지, 껍질 과일은 주치의와 상의."
DISCLAIMER_FE = "⚠️ 항암/백혈병 환자는 철분제는 반드시 주치의와 상의(비타민C 병용 시 흡수↑)."

# ================== HELPERS ==================
def entered(v):
    try:
        return v is not None and float(v) > 0
    except Exception:
        return False

def interpret_labs(l):
    out = []
    def add(s): out.append("- " + s)

    # 기본 해석 (핵심 파라미터 위주)
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
        add(f"CRP {c}: " + ("상승 → 염증/감염 의심" if c > 0.5 else "정상"))
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
        if isinstance(v, dict) and v.get("dose_or_tabs") is not None:
            line += f" | 입력량: {v['dose_or_tabs']}"
        out.append(line)
    return out

def food_suggestions(l: dict):
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
        foods.append(NEUTROPENIA_FOOD_RULE)
    foods.append(DISCLAIMER_FE)
    return foods

def init_state():
    st.session_state.setdefault("records", {})

# ================== UI ==================
init_state()

st.divider()
st.header("1️⃣ 환자 정보 입력")
nickname = st.text_input("별명(저장/그래프용)", placeholder="예: 홍길동", key="nick")
date_str = st.date_input("검사 날짜").strftime("%Y-%m-%d")

st.divider()
st.header("2️⃣ 카테고리 선택")
category = st.radio("분류", ["일반 해석","항암치료(암종류별)","항생제","투석 환자","당뇨 환자"], horizontal=False)

# ---------- 암종류별: 피수치 선택 + 항암 프리셋 ----------
meds = {}
extras = {}
selected_lab_labels = CORE_ORDER  # 기본

if category == "항암치료(암종류별)":
    st.markdown("### 🧬 암 종류")
    cancer_type = st.selectbox("암 종류를 선택하세요", ["AML","APL","ALL","CML","CLL","기타(직접 선택)"])

    # 피수치 선택 (암종별 기본값 로드 + 사용자 수정 가능)
    default_panel = CANCER_LAB_DEFAULTS.get(cancer_type, CORE_ORDER)
    st.markdown("### 🧪 표시할 피수치 선택")
    selected_lab_labels = st.multiselect(
        "필요한 피수치를 선택하세요 (선택한 항목만 입력창에 표시됩니다)",
        options=ALL_FIELDS,
        default=default_panel,
        help="CBC 세트(망상적혈구/헤마토크릿/MCV/MCH/MCHC/RDW)는 일부 환자에게만 표시하세요."
    )

    # 항암 프리셋
    st.markdown("### 💊 항암제 프리셋")
    rec = CANCER_REGIMENS.get(cancer_type, CANCER_REGIMENS["기타(직접 선택)"])["recommended"]
    selected_rx = st.multiselect("항암제 선택", options=sorted(set(rec + list(ANTICANCER.keys()))), default=rec)
    for key in selected_rx:
        if key == "ARA-C":
            c1, c2 = st.columns(2)
            with c1:
                form = st.selectbox("ARA-C 제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"], key="arac_form")
            with c2:
                dose = st.number_input("ARA-C 용량/일(선택)", min_value=0.0, step=0.1, key="arac_dose")
            meds[key] = {"form": form, "dose_or_tabs": dose}
        else:
            dose = st.number_input(f"{key} 투여량/알약 개수(소수 허용)", min_value=0.0, step=0.1, key=f"dose_{key}")
            meds[key] = {"dose_or_tabs": dose}

    # 암종별 주의
    for note in CANCER_REGIMENS.get(cancer_type, CANCER_REGIMENS["기타(직접 선택)"])["notes"]:
        st.write("• " + note)

    st.info("증상 가이드: " + FEVER_GUIDE)
    if st.checkbox("이뇨제 복용 중"):
        extras["diuretic"] = True

elif category == "항생제":
    st.markdown("### 🧪 항생제")
    extras["abx"] = st.multiselect("사용 중인 항생제 계열", list(ABX_GUIDE.keys()))

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

# ---------- 선택된 피수치만 입력창 표시 ----------
st.divider()
st.header("3️⃣ 혈액 검사 수치 입력 (선택한 항목만 표시)")

# 내부 dict (해석용 키)
labs = {}
for label in selected_lab_labels:
    key = norm_key(label)
    # 모바일 줄꼬임 방지 → 단일컬럼 순차 입력
    val = st.number_input(label, min_value=0.0, step=0.1 if key not in ["ANC","Glucose","AST","ALT","LDH","BNP"] else 1.0, key=f"lab_{key}")
    labs[key] = val

st.divider()
run = st.button("🔎 해석하기", use_container_width=True)

if run:
    st.subheader("📋 해석 결과")
    for line in interpret_labs(labs):
        st.write(line)

    # 음식 가이드
    fs = food_suggestions(labs)
    if fs:
        st.markdown("### 🥗 음식 가이드")
        for f in fs:
            st.write("- " + f)

    # 약물 요약
    if meds:
        st.markdown("### 💊 항암제 부작용·상호작용 요약")
        for line in summarize_meds(meds):
            st.write(line)

    # 항생제 요약
    if extras.get("abx"):
        st.markdown("### 🧪 항생제 주의 요약")
        for a in extras["abx"]:
            st.write(f"• {a}: {', '.join(ABX_GUIDE[a])}")

    # 발열 가이드
    st.markdown("### 🌡️ 발열 가이드")
    st.write(FEVER_GUIDE)

    # 보고서 저장/다운로드
    buf = [f"# BloodMap 보고서 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n",
           f"- 날짜: {date_str}\n",
           f"- 카테고리: {category}\n\n"]
    for label in selected_lab_labels:
        key = norm_key(label)
        v = labs.get(key)
        if entered(v):
            buf.append(f"- {label}: {v}\n")
    if meds:
        buf.append("\n## 약물\n")
        for line in summarize_meds(meds):
            buf.append(line + "\n")
    report_md = "".join(buf)
    st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"),
                       file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                       mime="text/markdown")
    st.download_button("📥 보고서(.txt) 다운로드", data=report_md.encode("utf-8"),
                       file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                       mime="text/plain")

    # 별명 저장
    if nickname.strip():
        if st.checkbox("📝 이 별명으로 저장", value=True):
            rec = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                   "date": date_str,
                   "category": category,
                   "labs": {norm_key(lbl): labs.get(norm_key(lbl)) for lbl in selected_lab_labels if entered(labs.get(norm_key(lbl)))},
                   "meds": meds,
                   "extras": extras,
                   "panel": selected_lab_labels}
            st.session_state.setdefault("records", {}).setdefault(nickname, []).append(rec)
            st.success("저장되었습니다. 아래 그래프에서 추이를 확인하세요.")
    else:
        st.info("별명을 입력하면 추이 그래프를 사용할 수 있어요.")

# ================== GRAPHS ==================
st.markdown("---")
st.subheader("📈 별명별 추이 그래프 (WBC, Hb, PLT, CRP, ANC)")
if not HAS_PD:
    st.info("그래프는 pandas 설치 시 활성화됩니다. (pip install pandas)")
else:
    if st.session_state.get("records"):
        sel = st.selectbox("별명 선택", sorted(st.session_state["records"].keys()))
        rows = st.session_state["records"].get(sel, [])
        if rows:
            data = []
            for r in rows:
                row = {"ts": r["ts"]}
                for k in ["WBC","Hb","PLT","CRP","ANC"]:
                    row[k] = r["labs"].get(k)
                data.append(row)
            if data:
                df = pd.DataFrame(data).set_index("ts")
                st.line_chart(df.dropna(how="all"))
            else:
                st.info("그래프화 가능한 항목이 없습니다.")
        else:
            st.info("선택한 별명의 저장 기록이 없습니다.")
    else:
        st.info("아직 저장된 기록이 없습니다.")

st.caption("© BloodMap | 제작: Hoya / 자문: GPT")

