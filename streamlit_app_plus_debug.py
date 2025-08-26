
import json
from datetime import datetime

import pandas as pd
import streamlit as st

# =============== Page & CSS (mobile hardening) ===============
st.set_page_config(page_title="피수치 자동 해석기 | BloodMap", page_icon="🩸", layout="centered")
st.markdown(
    """
    <style>
    input[type=number]{ font-size:16px; } /* iOS auto-zoom prevention */
    .stNumberInput label{ white-space:nowrap; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🔬 피수치 자동 해석기 by Hoya/GPT")
st.caption("자문: Hoya/GPT · 피수치 가이드 공식카페 · 교육/정보용(진단/치료 대체X)")

# =============== Safe UI reset ===============
left, right = st.columns(2)
with left:
    if st.button("🧹 UI 리셋", use_container_width=True):
        for k in list(st.session_state.keys()):
            if k.startswith(("lab_","med_","dm_","dialysis_","category_radio","nick")):
                del st.session_state[k]
        st.rerun()
with right:
    st.toast("모바일 순서 고정(Form+Keys+CSS) 적용중", icon="📱")

# =============== Session stores ===============
if "records" not in st.session_state:
    # {nickname: [{ts, category, labs:{...}, extras:{...}}]}
    st.session_state.records = {}
if "views" not in st.session_state:
    st.session_state.views = 0
st.session_state.views += 1
st.toast(f"누적 조회수: {st.session_state.views}", icon="👀")

# =============== Constants ===============
LAB_ORDER = [
    ("WBC", "01. WBC (백혈구)"),
    ("Hb", "02. Hb (혈색소)"),
    ("PLT", "03. 혈소판 (PLT)"),
    ("ANC", "04. ANC (호중구)"),
    ("Ca", "05. Ca (칼슘)"),
    ("P", "06. P (인)"),
    ("Na", "07. Na (소디움)"),
    ("K", "08. K (포타슘)"),
    ("Albumin", "09. Albumin (알부민)"),
    ("Glucose", "10. Glucose (혈당)"),
    ("Total Protein", "11. Total Protein (총단백)"),
    ("AST", "12. AST"),
    ("ALT", "13. ALT"),
    ("LDH", "14. LDH"),
    ("CRP", "15. CRP"),
    ("Cr", "16. Creatinine (Cr)"),
    ("UA", "17. Uric Acid (UA)"),
    ("TB", "18. Total Bilirubin (TB)"),
    ("BUN", "19. BUN"),
    ("BNP", "20. BNP (선택)"),
]

FOODS = {
    "Albumin_low": ["달걀","연두부","흰살 생선","닭가슴살","귀리죽"],
    "K_low": ["바나나","감자","호박죽","고구마","오렌지"],
    "Hb_low": ["소고기","시금치","두부","달걀 노른자","렌틸콩"],
    "Na_low": ["전해질 음료","미역국","바나나","오트밀죽","삶은 감자"],
    "Ca_low": ["연어 통조림","두부","케일","브로콜리","(참깨 제외)"],
}

ANTICANCER = {
    "6-MP":{"alias":"6-머캅토퓨린","aes":["골수억제","간수치 상승","구내염","오심"],"warn":["황달/진한 소변 시 진료","감염 징후 시 즉시 연락"],"ix":["알로푸리놀 병용 감량 가능","와파린 효과 변동"]},
    "MTX":{"alias":"메토트렉세이트","aes":["골수억제","간독성","신독성","구내염","광과민"],"warn":["탈수 시 독성↑","고용량 후 류코보린"],"ix":["NSAIDs/TMP-SMX 병용 독성↑","일부 PPI 상호작용"]},
    "ATRA":{"alias":"베사노이드(트레티노인)","aes":["분화증후군","발열","피부/점막 건조","두통"],"warn":["분화증후군 의심 시 즉시 병원"],"ix":["테트라사이클린계와 가성뇌종양"]},
    "ARA-C":{"alias":"시타라빈","aes":["골수억제","발열","구내염","(HDAC) 신경독성"],"warn":["HDAC 시 신경증상 즉시 보고"],"ix":["효소유도제 상호작용"]},
    "G-CSF":{"alias":"그라신","aes":["골통/근육통","주사부위 반응","드물게 비장비대"],"warn":["좌상복부 통증 시 평가"],"ix":[]},
    "Hydroxyurea":{"alias":"하이드록시우레아","aes":["골수억제","피부색소침착","궤양"],"warn":["임신 회피"],"ix":[]},
    "Daunorubicin":{"alias":"도우노루비신","aes":["골수억제","심독성","오심/구토","점막염"],"warn":["누적용량 심기능"],"ix":["트라스투주맙 등 심독성↑"]},
    "Idarubicin":{"alias":"이달루비신","aes":["골수억제","심독성","점막염"],"warn":["심기능"],"ix":[]},
    "Mitoxantrone":{"alias":"미토잔트론","aes":["골수억제","심독성","청록색 소변"],"warn":["심기능"],"ix":[]},
    "Cyclophosphamide":{"alias":"사이클로포스파미드","aes":["골수억제","출혈성 방광염","탈모"],"warn":["수분섭취·메스나"],"ix":["CYP 상호작용"]},
    "Etoposide":{"alias":"에토포사이드","aes":["골수억제","저혈압(주입)"],"warn":[],"ix":[]},
    "Topotecan":{"alias":"토포테칸","aes":["골수억제","설사"],"warn":[],"ix":[]},
    "Fludarabine":{"alias":"플루다라빈","aes":["면역억제","감염 위험↑","혈구감소"],"warn":["PCP 예방 고려"],"ix":[]},
    "Vincristine":{"alias":"빈크리스틴(비크라빈 유사)","aes":["말초신경병증","변비/장폐색"],"warn":["IT 투여 금지"],"ix":["CYP3A 상호작용"]},
}

ABX_GUIDE = {
    "페니실린계":["발진/설사","와파린 효과↑ 가능"],
    "세팔로스포린계":["설사","알코올과 병용 시 플러싱 일부"],
    "마크롤라이드":["QT 연장","CYP 상호작용"],
    "플루오로퀴놀론":["힘줄염·광과민","QT 연장"],
    "카바페넴":["경련 위험(고용량/신부전)","광범위"],
    "TMP-SMX":["고칼륨혈증","골수억제","MTX와 병용 주의"],
    "메트로니다졸":["금주","금속맛/구역"],
    "반코마이신":["Red man(주입속도)","신독성(고농도)"],
}

def entered(v):
    try:
        return v is not None and float(v) > 0
    except Exception:
        return False

def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# =============== Data import/export ===============
with st.expander("📂 데이터 관리 (불러오기/내보내기)"):
    c1, c2 = st.columns(2)
    with c1:
        up = st.file_uploader("저장 JSON 불러오기", type=["json"], key="uploader_json")
        if up:
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
        st.download_button("💾 전체 기록 JSON 다운로드", data=dump.encode("utf-8"),
                           file_name="bloodmap_records.json", mime="application/json",
                           key="download_json")

# =============== Profile & Category ===============
nickname = st.text_input("별명(닉네임) — 저장/그래프용", placeholder="예: 홍길동", key="nick")
if nickname.strip() and nickname in st.session_state.records:
    st.info("이미 존재하는 별명입니다. 저장 시 기존 기록에 추가됩니다.")
category = st.radio("카테고리 선택", ["일반 해석","항암치료","항생제","투석 환자","당뇨 환자"], key="category_radio")
st.markdown("---")

# =============== Input widgets (FORM to lock order) ===============
def render_lab_inputs():
    vals = {}
    for k, label in LAB_ORDER:
        vals[k] = st.number_input(label, min_value=0.0, step=0.1, format="%.2f", key=f"lab_{k}")
    return vals

def build_lab_interpretation(labs: dict):
    out = []
    if entered(labs.get("WBC")):
        v = labs["WBC"]; out.append(f"WBC {v:.1f}: " + ("낮음 → 면역저하·감염 위험↑" if v < 4 else "높음 → 감염/염증 가능" if v > 10 else "정상 범위"))
    if entered(labs.get("Hb")):
        v = labs["Hb"]; out.append(f"Hb {v:.1f}: " + ("낮음 → 빈혈 가능" if v < 12 else "정상 범위"))
    if entered(labs.get("PLT")):
        v = labs["PLT"]; out.append(f"혈소판 {v:.1f}: " + ("낮음 → 출혈 위험" if v < 150 else "정상 범위"))
    if entered(labs.get("ANC")):
        v = labs["ANC"]; out.append(f"ANC {v:.0f}: " + ("심한 호중구감소 → 즉시 감염예방 수칙" if v < 500 else "경~중등도 감소" if v < 1500 else "정상 범위"))
    if entered(labs.get("Albumin")):
        v = labs["Albumin"]; out.append(f"Albumin {v:.2f}: " + ("낮음 → 영양 부족/염증/간질환 가능" if v < 3.5 else "정상 범위"))
    if entered(labs.get("Glucose")):
        v = labs["Glucose"]; out.append(f"Glucose {v:.1f}: " + ("고혈당 (식후/스트레스 여부 확인)" if v >= 200 else "저혈당 주의" if v < 70 else "정상 범위"))
    if entered(labs.get("CRP")):
        v = labs["CRP"]; out.append(f"CRP {v:.2f}: " + ("상승 → 염증/감염 의심" if v > 0.5 else "정상 범위"))
    if entered(labs.get("BUN")) and entered(labs.get("Cr")) and labs["Cr"] > 0:
        ratio = labs["BUN"]/labs["Cr"]
        if ratio > 20: out.append(f"BUN/Cr {ratio:.1f}: 탈수 의심")
        elif ratio < 10: out.append(f"BUN/Cr {ratio:.1f}: 간질환/영양 상태 등 고려")
    return out

def build_food_suggestions(labs: dict):
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
    foods.append("⚠️ 항암/백혈병 환자는 철분제 복용을 피하거나 반드시 주치의와 상의하세요.")
    foods.append("⚠️ 철분제+비타민C 병용 시 흡수↑ → 복용은 반드시 의료진과 상의 후 결정.")
    if entered(labs.get("ANC")) and labs["ANC"] < 500:
        foods.append("🧼 호중구 감소: 생채소 금지, 모든 음식은 익혀 섭취(전자레인지 30초+), 멸균/살균 식품 권장, 2시간 지난 음식 금지, 껍질 과일은 주치의와 상의.")
    return foods

def render_anticancer_inputs():
    st.subheader("💊 항암제/보조제 입력")
    meds = {}
    if st.checkbox("ARA-C 사용", key="med_arac_use"):
        meds["ARA-C"] = {
            "use": True,
            "form": st.selectbox("ARA-C 제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"], key="med_arac_form"),
            "dose": st.number_input("ARA-C 용량/일(임의 입력)", min_value=0.0, step=0.1, key="med_arac_dose"),
        }
    for key in ["6-MP","MTX","ATRA","G-CSF","Hydroxyurea","Daunorubicin","Idarubicin","Mitoxantrone","Cyclophosphamide","Etoposide","Topotecan","Fludarabine","Vincristine"]:
        if st.checkbox(f"{key} 사용", key=f"med_use_{key}"):
            meds[key] = {"use": True, "dose_or_tabs": st.number_input(f"{key} 투여량/알약 개수(소수 허용)", min_value=0.0, step=0.1, key=f"med_dose_{key}")}
    return meds

def render_antibiotic_inputs():
    st.subheader("🧪 항생제 선택")
    options = list(ABX_GUIDE.keys())
    sel = st.multiselect("사용 중인 항생제", options, key="abx_select")
    notes = [f"• {s}: {', '.join(ABX_GUIDE[s])}" for s in sel]
    return {"abx": sel, "notes": notes}

FEVER_GUIDE = "🌡️ 38.0~38.5℃ 해열제/경과관찰 · 38.5℃↑ 병원 연락 · 39.0℃↑ 즉시 병원. (ANC<500 동반 발열=응급)"
def render_diuretic_input():
    return st.checkbox("이뇨제 복용 중", key="diuretic_on")
def render_dialysis_extras():
    st.subheader("🫧 투석 환자 추가 항목")
    urine = st.number_input("하루 소변량 (mL)", min_value=0.0, step=10.0, key="dialysis_urine")
    hd_today = st.checkbox("오늘 투석 시행", key="dialysis_today")
    post_delta = st.number_input("투석 후 체중 변화 (kg)", min_value=-10.0, max_value=10.0, step=0.1, key="dialysis_delta")
    return {"urine_ml": urine, "hd_today": hd_today, "post_hd_weight_delta": post_delta}
def render_diabetes_inputs():
    st.subheader("🍚 당뇨 지표")
    fpg = st.number_input("식전 혈당 (mg/dL)", min_value=0.0, step=1.0, key="dm_fpg")
    pp1 = st.number_input("식후 1시간 혈당 (mg/dL)", min_value=0.0, step=1.0, key="dm_pp1")
    pp2 = st.number_input("식후 2시간 혈당 (mg/dL)", min_value=0.0, step=1.0, key="dm_pp2")
    a1c = st.number_input("HbA1c (%)", min_value=0.0, step=0.1, format="%.1f", key="dm_a1c")
    tips = []
    if entered(fpg) and fpg >= 126: tips.append("식전 고혈당: 저당 식이·규칙적 식사 간격")
    if entered(pp2) and pp2 >= 200: tips.append("식후 고혈당: 식사 탄수 조절·걷기")
    if entered(a1c) and a1c >= 6.5: tips.append("HbA1c 상승: 장기 혈당 관리 필요")
    return {"FPG": fpg, "PP1h": pp1, "PP2h": pp2, "HbA1c": a1c, "tips": tips}

# ======== FORM (locks order visually & logically) ========
labs, extras, meds, notes_sections = {}, {}, {}, []
with st.form("main_form", clear_on_submit=False):
    if category in ("일반 해석","항암치료","투석 환자"):
        labs = render_lab_inputs()
    if category == "항암치료":
        st.markdown("### 약물 요약")
        meds = render_anticancer_inputs()
        if render_diuretic_input():
            notes_sections.append("💧 이뇨제: 탈수/저Na/저K/쥐 경고 · BUN/Cr 상승 시 수분 상태 확인")
        st.info(FEVER_GUIDE)
    elif category == "항생제":
        extras.update(render_antibiotic_inputs())
        st.info("💡 임의 중단/변경 금지. 복용시간 규칙 · 수분섭취 · 이상 시 의료진.")
    elif category == "투석 환자":
        extras.update(render_dialysis_extras())
        if render_diuretic_input():
            notes_sections.append("💧 이뇨제: 전해질 이상·탈수 위험. 어지럼/경련 시 평가.")
    elif category == "당뇨 환자":
        extras.update(render_diabetes_inputs())

    run = st.form_submit_button("🔎 해석하기", use_container_width=True)

# =============== Output & Save ===============
def summarize_anticancer(meds: dict):
    out = []
    for k in meds.keys():
        info = ANTICANCER.get(k)
        if info:
            line = f"• {k} ({info['alias']}): AE {', '.join(info['aes'])}"
            if info.get("warn"): line += f" | 주의: {', '.join(info['warn'])}"
            if info.get("ix"): line += f" | 상호작용: {', '.join(info['ix'])}"
            out.append(line)
    return out

if run:
    st.subheader("📋 해석 결과")
    if labs:
        for line in build_lab_interpretation(labs): st.write("- " + line)
        fs = build_food_suggestions(labs)
        if fs:
            st.markdown("### 🥗 음식 가이드")
            for f in fs: st.write("- " + f)
    if meds:
        st.markdown("### 💊 항암제 부작용·상호작용 요약")
        for line in summarize_anticancer(meds): st.write(line)
    if extras.get("notes"):
        st.markdown("### 🧪 항생제 주의 요약")
        for n in extras["notes"]: st.write(n)
    if "tips" in extras and extras["tips"]:
        st.markdown("### 🍚 당뇨 팁")
        for t in extras["tips"]: st.write("- " + t)
    if notes_sections:
        st.markdown("### 📌 추가 노트")
        for n in notes_sections: st.write("- " + n)

    # Report build
    buf = [
        "# 피수치 자동 해석 보고서\n",
        f"- 생성시각: {now_ts()}\n",
        f"- 별명: {nickname or '미입력'}\n",
        f"- 카테고리: {category}\n\n",
        "## 수치 해석\n",
    ]
    for k, label in LAB_ORDER:
        if k in labs and entered(labs[k]): buf.append(f"- {label}: {labs[k]}\n")
    if meds:
        buf.append("\n## 항암제 요약\n")
        for line in summarize_anticancer(meds): buf.append(f"- {line}\n")
    if extras.get("notes"):
        buf.append("\n## 항생제 주의\n")
        for n in extras["notes"]: buf.append(f"- {n}\n")
    if extras.get("tips"):
        buf.append("\n## 당뇨 팁\n")
        for t in extras["tips"]: buf.append(f"- {t}\n")
    if notes_sections:
        buf.append("\n## 추가 노트\n")
        for n in notes_sections: buf.append(f"- {n}\n")
    buf.append("\n---\n본 보고서는 교육 용도로 제공되며, 치료·진단은 담당 의료진의 안내를 따르세요.\n")
    report_md = "".join(buf)
    st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"),
                       file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                       mime="text/markdown", use_container_width=True, key="download_md")

    # Save record for graphs
    if nickname.strip():
        if st.checkbox("📝 결과를 이 별명으로 저장하시겠습니까?", value=True, key="save_checkbox"):
            rec = {"ts": now_ts(), "category": category,
                   "labs": {k:v for k,v in labs.items() if entered(v)} if labs else {},
                   "extras": extras}
            st.session_state.records.setdefault(nickname, []).append(rec)
            st.success("저장되었습니다. 아래 그래프에서 추이를 확인하세요.")
    else:
        st.warning("별명을 입력하면 추이 그래프를 사용할 수 있어요.")

# =============== Graphs ===============
st.markdown("---")
st.subheader("📈 별명별 추이 그래프 (WBC, Hb, PLT, CRP, ANC)")
if st.session_state.records:
    nicknames = sorted(st.session_state.records.keys())
    sel = st.selectbox("그래프 볼 별명 선택", nicknames)
    rows = st.session_state.records.get(sel, [])
    if rows:
        data = []
        for r in rows:
            row = {"ts": r["ts"]}
            for k in ["WBC","Hb","PLT","CRP","ANC"]:
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

# =============== Footer ===============
st.markdown("**제작**: Hoya/GPT  \n**표시 원칙**: *입력한 항목만* 결과에 표시됩니다.  \n**주의**: 약물(항암제/항생제/해열제/이뇨제)은 반드시 **담당 의료진 지시**를 우선하세요.")

