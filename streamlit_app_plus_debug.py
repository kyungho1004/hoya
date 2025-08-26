
import json
from datetime import datetime
import pandas as pd
import streamlit as st

# ================== PAGE CONFIG & MOBILE CSS ==================
st.set_page_config(page_title="BloodMap | 최종 초고정 풀옵션(롱버전)", page_icon="🩸", layout="centered")
st.markdown(
    """
    <style>
    /* iOS 숫자입력 확대 방지 + 레이블 줄바꿈 방지 */
    input[type=number]{ font-size:16px; }
    .stNumberInput label{ white-space:nowrap; }
    /* 데이터 에디터 가독성 향상 */
    [data-testid="stDataFrame"] table{ font-size:14px; }
    </style>
    """, unsafe_allow_html=True
)

st.title("🔬 BloodMap — 최종 초고정 풀옵션 (롱버전)")
st.caption("표(데이터그리드)로 입력 순서를 **행으로 잠금** → 모바일에서도 절대 안 꼬임 · 저장/그래프/보고서/항암제/항생제/투석/당뇨/발열/이뇨제/음식 가이드")

# ================== SESSION STATE ==================
if "records" not in st.session_state:
    # { nickname: [ {ts, category, labs, meds, extras} ] }
    st.session_state.records = {}
if "views" not in st.session_state:
    st.session_state.views = 0
st.session_state.views += 1
st.toast(f"조회수: {st.session_state.views}", icon="👀")

# ================== LAB ORDER ==================
ORDER = [
    "WBC","Hb","PLT","ANC","Ca","P","Na","K","Albumin","Glucose",
    "Total Protein","AST","ALT","LDH","CRP","Cr","UA","TB","BUN","BNP"
]

# ================== DICTS (DETAIL) ==================
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

# ================== 기본 데이터프레임 ==================
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame({"항목": ORDER, "값": [None]*len(ORDER)})

# ================== IMPORT / EXPORT ==================
with st.expander("📂 데이터 관리 (불러오기/내보내기)"):
    c1,c2 = st.columns(2)
    with c1:
        up = st.file_uploader("저장 JSON 불러오기", type=["json"])
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
                           file_name="bloodmap_records.json", mime="application/json")

# ================== PROFILE ==================
nickname = st.text_input("별명(저장/그래프용)", placeholder="예: 홍길동")
category = st.radio("카테고리", ["일반 해석","항암치료","항생제","투석 환자","당뇨 환자"])
st.markdown("---")
st.info("표에서 **'값' 열만 입력**하세요. 순서는 행 고정 → 모바일에서도 절대 안 꼬임")

# ================== LAB INPUT TABLE (ULTRA-LOCK) ==================
with st.form("main_form", clear_on_submit=False):
    edited = st.data_editor(
        st.session_state.df,
        num_rows="fixed", hide_index=True, use_container_width=True,
        column_order=["항목","값"],
        column_config={
            "항목": st.column_config.Column(disabled=True),
            "값": st.column_config.NumberColumn(help="수치 입력 (미입력 가능)", step=0.1),
        },
        key="grid"
    )

    meds, extras = {}, {}

    # ---- 항암치료 ----
    if category == "항암치료":
        st.markdown("### 💊 항암제/보조제")
        if st.checkbox("ARA-C 사용", key="med_arac_use"):
            meds["ARA-C"] = {
                "form": st.selectbox("ARA-C 제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"], key="med_arac_form"),
                "dose": st.number_input("ARA-C 용량/일(임의 입력)", min_value=0.0, step=0.1, key="med_arac_dose"),
            }
        for key in ["6-MP","MTX","ATRA","G-CSF","Hydroxyurea","Daunorubicin","Idarubicin","Mitoxantrone",
                    "Cyclophosphamide","Etoposide","Topotecan","Fludarabine","Vincristine"]:
            if st.checkbox(f"{key} 사용", key=f"med_use_{key}"):
                meds[key] = {"dose_or_tabs": st.number_input(f"{key} 투여량/알약 개수(소수 허용)", min_value=0.0, step=0.1, key=f"med_dose_{key}")}
        st.info(FEVER_GUIDE)
        if st.checkbox("이뇨제 복용 중", key="diuretic_on"):
            extras["diuretic"] = True

    # ---- 항생제 ----
    if category == "항생제":
        st.markdown("### 🧪 항생제")
        options = list(ABX_GUIDE.keys())
        extras["abx"] = st.multiselect("사용 중인 항생제", options, key="abx_select")

    # ---- 투석 환자 ----
    if category == "투석 환자":
        st.markdown("### 🫧 투석 추가 항목")
        extras["urine_ml"] = st.number_input("하루 소변량 (mL)", min_value=0.0, step=10.0, key="dialysis_urine")
        extras["hd_today"] = st.checkbox("오늘 투석 시행", key="dialysis_today")
        extras["post_hd_weight_delta"] = st.number_input("투석 후 체중 변화 (kg)", min_value=-10.0, max_value=10.0, step=0.1, key="dialysis_delta")
        if st.checkbox("이뇨제 복용 중", key="diuretic_on_dial"):
            extras["diuretic"] = True

    # ---- 당뇨 ----
    if category == "당뇨 환자":
        st.markdown("### 🍚 당뇨 지표")
        extras["FPG"] = st.number_input("식전 혈당 (mg/dL)", min_value=0.0, step=1.0, key="dm_fpg")
        extras["PP1h"] = st.number_input("식후 1시간 혈당 (mg/dL)", min_value=0.0, step=1.0, key="dm_pp1")
        extras["PP2h"] = st.number_input("식후 2시간 혈당 (mg/dL)", min_value=0.0, step=1.0, key="dm_pp2")
        extras["HbA1c"] = st.number_input("HbA1c (%)", min_value=0.0, step=0.1, format="%.1f", key="dm_a1c")

    run = st.form_submit_button("🔎 해석하기", use_container_width=True)

# ================== HELPERS ==================
def entered(v):
    try:
        return v is not None and float(v) > 0
    except Exception:
        return False

def interpret_labs(l):
    out=[]
    def add(s): out.append("- " + s)
    if entered(l.get("WBC")): add(f"WBC {l['WBC']}: " + ("낮음 → 감염 위험↑" if l["WBC"]<4 else "높음 → 감염/염증 가능" if l["WBC"]>10 else "정상"))
    if entered(l.get("Hb")): add(f"Hb {l['Hb']}: " + ("낮음 → 빈혈" if l["Hb"]<12 else "정상"))
    if entered(l.get("PLT")): add(f"혈소판 {l['PLT']}: " + ("낮음 → 출혈 위험" if l["PLT"]<150 else "정상"))
    if entered(l.get("ANC")): add(f"ANC {l['ANC']}: " + ("중증 감소(<500)" if l["ANC"]<500 else "감소(<1500)" if l["ANC"]<1500 else "정상"))
    if entered(l.get("Albumin")): add(f"Albumin {l['Albumin']}: " + ("낮음 → 영양/염증/간질환 가능" if l["Albumin"]<3.5 else "정상"))
    if entered(l.get("Glucose")): add(f"Glucose {l['Glucose']}: " + ("고혈당(≥200)" if l["Glucose"]>=200 else "저혈당(<70)" if l["Glucose"]<70 else "정상"))
    if entered(l.get("CRP")): add(f"CRP {l['CRP']}: " + ("상승 → 염증/감염 의심" if l["CRP"]>0.5 else "정상"))
    if entered(l.get("BUN")) and entered(l.get("Cr")) and l["Cr"]>0:
        ratio=l["BUN"]/l["Cr"]
        if ratio>20: add(f"BUN/Cr {ratio:.1f}: 탈수 의심")
        elif ratio<10: add(f"BUN/Cr {ratio:.1f}: 간질환/영양 상태 고려")
    return out

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
    if entered(l.get("Albumin")) and l["Albumin"]<3.5: foods.append("알부민 낮음 → " + ", ".join(FOODS["Albumin_low"]))
    if entered(l.get("K")) and l["K"]<3.5: foods.append("칼륨 낮음 → " + ", ".join(FOODS["K_low"]))
    if entered(l.get("Hb")) and l["Hb"]<12: foods.append("Hb 낮음 → " + ", ".join(FOODS["Hb_low"]))
    if entered(l.get("Na")) and l["Na"]<135: foods.append("나트륨 낮음 → " + ", ".join(FOODS["Na_low"]))
    if entered(l.get("Ca")) and l["Ca"]<8.5: foods.append("칼슘 낮음 → " + ", ".join(FOODS["Ca_low"]))
    if entered(l.get("ANC")) and l["ANC"]<500:
        foods.append("🧼 호중구 감소: 생채소 금지, 모든 음식 익혀 섭취(전자레인지 30초+), 멸균/살균 식품 권장, 2시간 지난 음식 금지, 껍질 과일은 주치의 상의.")
    foods.append("⚠️ 항암/백혈병 환자는 철분제 복용을 피하거나 반드시 주치의와 상의하세요. (비타민C 병용 시 흡수↑)")
    return foods

# ================== RUN ==================
# 최신 편집 상태를 반영 (표는 순서 고정)
if "grid" in st.session_state:
    current_df = st.session_state.grid.copy()
    # 편집한 테이블을 세션 df에도 반영 (다음 렌더에도 유지)
    st.session_state.df = current_df

labs = {row["항목"]: row["값"] for _, row in st.session_state.df.iterrows()}

if run:
    st.subheader("📋 해석 결과")
    for line in interpret_labs(labs): st.write(line)

    # 음식
    fs = food_suggestions(labs)
    if fs:
        st.markdown("### 🥗 음식 가이드")
        for f in fs: st.write("- " + f)

    # 항암제 요약
    if category == "항암치료" and meds:
        st.markdown("### 💊 항암제 부작용·상호작용 요약")
        for line in summarize_meds(meds): st.write(line)

    # 항생제 요약
    if category == "항생제" and extras.get("abx"):
        st.markdown("### 🧪 항생제 주의 요약")
        for a in extras["abx"]: st.write(f"• {a}: {', '.join(ABX_GUIDE[a])}")

    # 투석/이뇨제/당뇨 노트
    note_sections = []
    if extras.get("diuretic"):
        note_sections.append("💧 이뇨제: 탈수·저Na/저K·쥐 경고. BUN/Cr 상승 시 수분 상태 점검.")
    if category == "투석 환자":
        note_sections.append("🫧 투석 환자 입력을 반영했습니다.")
    if category == "당뇨 환자":
        tips=[]
        if entered(extras.get("FPG")) and extras["FPG"]>=126: tips.append("식전 고혈당: 저당 식이·규칙적 식사 간격.")
        if entered(extras.get("PP2h")) and extras["PP2h"]>=200: tips.append("식후 고혈당: 탄수 조절·걷기.")
        if entered(extras.get("HbA1c")) and extras["HbA1c"]>=6.5: tips.append("HbA1c 상승: 장기 혈당 관리 필요.")
        if tips:
            st.markdown("### 🍚 당뇨 팁")
            for t in tips: st.write("- " + t)
    if note_sections:
        st.markdown("### 📌 추가 노트")
        for n in note_sections: st.write("- " + n)

    # 발열 가이드 (모든 카테고리에서 참조 가능)
    st.markdown("### 🌡️ 발열 가이드")
    st.write(FEVER_GUIDE)

    # 보고서 다운로드
    buf = [
        "# 피수치 자동 해석 보고서\n",
        f"- 생성시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"- 별명: {nickname or '미입력'}\n",
        f"- 카테고리: {category}\n\n",
        "## 수치 입력\n",
    ]
    for k in ORDER:
        v = labs.get(k)
        if entered(v): buf.append(f"- {k}: {v}\n")
    if category == "항암치료" and meds:
        buf.append("\n## 항암제 요약\n")
        for line in summarize_meds(meds): buf.append(f"- {line}\n")
    if category == "항생제" and extras.get("abx"):
        buf.append("\n## 항생제 주의\n")
        for a in extras["abx"]: buf.append(f"- {a}: {', '.join(ABX_GUIDE[a])}\n")
    if category == "당뇨 환자":
        buf.append("\n## 당뇨 입력\n")
        for k in ["FPG","PP1h","PP2h","HbA1c"]:
            if entered(extras.get(k)): buf.append(f"- {k}: {extras.get(k)}\n")
    if category == "투석 환자":
        buf.append("\n## 투석 입력\n")
        for k in ["urine_ml","hd_today","post_hd_weight_delta"]:
            val = extras.get(k, None)
            if val not in (None, False): buf.append(f"- {k}: {val}\n")
    buf.append("\n---\n본 보고서는 교육 용도로 제공되며, 치료·진단은 담당 의료진의 안내를 따르세요.\n")
    report_md = "".join(buf)
    st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"),
                       file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                       mime="text/markdown", use_container_width=True)

    # 저장
    if nickname.strip():
        if st.checkbox("📝 결과를 이 별명으로 저장하시겠습니까?", value=True, key="save_checkbox"):
            rec = {
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "category": category,
                "labs": {k:v for k,v in labs.items() if entered(v)},
                "meds": meds,
                "extras": extras
            }
            st.session_state.records.setdefault(nickname, []).append(rec)
            st.success("저장되었습니다. 아래 그래프에서 추이를 확인하세요.")
    else:
        st.warning("별명을 입력하면 추이 그래프를 사용할 수 있어요.")

# ================== GRAPHS ==================
st.markdown("---")
st.subheader("📈 별명별 추이 그래프 (WBC, Hb, PLT, CRP, ANC)")
if st.session_state.records:
    nicks = sorted(st.session_state.records.keys())
    sel = st.selectbox("그래프 볼 별명 선택", nicks)
    rows = st.session_state.records.get(sel, [])
    if rows:
        data=[]
        for r in rows:
            row={"ts": r["ts"]}
            for k in ["WBC","Hb","PLT","CRP","ANC"]:
                if r.get("labs") and k in r["labs"]:
                    row[k]=r["labs"][k]
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

