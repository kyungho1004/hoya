import streamlit as st
import datetime, io, os, re

st.set_page_config(page_title="피수치 자동 해석기 (v8: 자유 입력)", layout="centered")
st.title("🔬 피수치 자동 해석기 (자유 입력 버전)")
st.caption("제작: Hoya/GPT · 자문: Hoya/GPT")
st.write("※ 본 결과는 교육/보조 용도이며 **최종 승인 = 주치의** 입니다.")

# 조회수 카운터
if "views" not in st.session_state:
    st.session_state.views = 0
st.session_state.views += 1
st.sidebar.success(f"조회수: {st.session_state.views}")

# ─────────────────────────────
# 유틸
# ─────────────────────────────
def parse_float(s: str):
    if s is None:
        return None
    s = s.strip()
    if not s:
        return None
    # 숫자, 점, 콤마, 음수만 허용
    s = re.sub(r"[^0-9,.-]", "", s)
    # 천단위 콤마 제거
    s = s.replace(",", "")
    try:
        return float(s)
    except:
        return None

def num_input(label, key=None, placeholder="예: 12.5"):
    val = st.text_input(label, key=key, placeholder=placeholder)
    return parse_float(val)

def exists(x, zero_ok=False):
    if zero_ok:
        return True
    return x is not None and x != 0

def add_food(lines, items, title):
    foods = ", ".join(items)
    lines.append(f"🥗 **{title}** → {foods}")

def write_header(report_lines):
    today = datetime.date.today()
    report_lines.append(f"# 피수치 자동 해석 보고서 ({today})")
    report_lines.append("")
    report_lines.append("- 제작: Hoya/GPT · 자문: Hoya/GPT")
    report_lines.append("- 본 자료는 교육/보조용이며 **최종 승인은 주치의**에게 받으세요.")
    report_lines.append("")

# 공통 경고
NEUTROPENIA_NOTICE = (
    "⚠️ **호중구 낮음 위생 가이드**\n"
    "- 생채소 금지, 모든 음식은 충분히 익혀 섭취\n"
    "- 멸균/살균식품 권장\n"
    "- 조리 후 남은 음식은 **2시간 이후 섭취 비권장**\n"
    "- 껍질 있는 과일은 **주치의와 상담 후** 섭취 결정\n"
)
IRON_WARN = (
    "❗ **철분제 주의**\n"
    "항암 치료 중이거나 백혈병 환자는 **철분제 복용을 지양**하세요.\n"
    "철분제와 비타민 C를 함께 복용하면 흡수가 증가합니다. 반드시 **주치의와 상의 후** 결정하세요."
)

# 카테고리 선택
category = st.selectbox("해석 카테고리 선택", ["항암 치료", "투석 환자", "당뇨 환자", "일반 해석"])

# 별명 & 파일
nickname = st.text_input("별명 입력 (저장/불러오기용)", placeholder="예: hoya_kid01")
if not nickname:
    st.warning("별명을 입력해야 결과 저장/다운로드가 가능합니다.")

st.sidebar.header("📁 파일 관리")
uploaded = st.sidebar.file_uploader("과거 보고서(.md) 업로드하여 이어쓰기", type=["md"])
if uploaded and nickname:
    content = uploaded.read()
    with open(f"{nickname}_results.md", "wb") as f:
        f.write(content)
    st.sidebar.success("업로드 완료. 이 별명 파일로 이어서 저장됩니다.")

if nickname and st.sidebar.button("🚫 이 별명 보고서 파일 삭제"):
    try:
        os.remove(f"{nickname}_results.md")
        st.sidebar.success("삭제 완료")
    except FileNotFoundError:
        st.sidebar.info("삭제할 파일이 없습니다.")

# ─────────────────────────────
# 입력 폼 (텍스트 자유 입력)
# ─────────────────────────────
st.subheader("📊 입력 (숫자를 직접 타이핑하세요)")
inputs = {}

if category in ["항암 치료", "일반 해석"]:
    col1, col2 = st.columns(2)
    with col1:
        inputs["wbc"] = num_input("WBC (x10³/µL)", key="wbc", placeholder="예: 4.3")
        inputs["hb"]  = num_input("혈색소 Hb (g/dL)", key="hb", placeholder="예: 9.8")
        inputs["plt"] = num_input("혈소판 PLT (x10³/µL)", key="plt", placeholder="예: 120")
        inputs["anc"] = num_input("ANC (/µL)", key="anc", placeholder="예: 450")
    with col2:
        inputs["ca"]  = num_input("칼슘 Ca (mg/dL)", key="ca", placeholder="예: 8.1")
        inputs["na"]  = num_input("나트륨 Na (mEq/L)", key="na", placeholder="예: 132")
        inputs["k"]   = num_input("칼륨 K (mEq/L)", key="k", placeholder="예: 3.2")
        inputs["alb"] = num_input("알부민 Albumin (g/dL)", key="alb", placeholder="예: 3.2")
    inputs["temp"] = num_input("🌡️ 체온 (°C)", key="temp", placeholder="예: 38.2")

if category == "항암 치료":
    st.markdown("**🟢 유지요법 (경구제)**")
    maint_drugs = ["6-MP", "MTX", "베사노이드"]
    inputs["maint"] = {}
    mcols = st.columns(3)
    for i, d in enumerate(maint_drugs):
        with mcols[i]:
            if st.checkbox(f"{d} 복용", key=f"maint_use_{d}"):
                dose = num_input(f"{d} 알약 개수(소수 가능)", key=f"maint_dose_{d}", placeholder="예: 1.5")
                if exists(dose, zero_ok=True):
                    inputs["maint"][d] = dose

    st.markdown("**🔴 항암제 투여중 (주사/강화요법 등)**")
    active_drugs = [
        "ARA-C (아라씨)", "도우노루비신", "사이클로포스파마이드",
        "에토포사이드", "토포테칸", "플루다라빈",
        "비크라빈", "미토잔트론", "이달루시신",
        "하이드록시우레아", "그라신(G-CSF)"
    ]
    inputs["active"] = {}
    for d in active_drugs:
        use = st.checkbox(f"{d} 투여", key=f"active_use_{d}")
        if use:
            if d.startswith("ARA-C"):
                form = st.selectbox(f"아라씨 제형 선택", ["정맥(IV)", "피하(SC)", "고용량(HDAC)"], key=f"arac_form_{d}")
                sched = st.text_input("용량/주기 (예: 100mg/m² q12h x 7d)", key=f"arac_s_{d}")
                inputs["active"][d] = {"제형": form, "용량/주기": sched}
            else:
                sched = st.text_input(f"{d} 용량/주기", key=f"active_s_{d}")
                inputs["active"][d] = {"용량/주기": sched}
    inputs["diuretic"] = st.checkbox("💧 이뇨제 복용 중")

    # 증상 체크
    st.subheader("🩺 증상 체크")
    inputs["sx_mucositis"] = st.checkbox("구내염 있음")
    inputs["sx_diarrhea"] = st.checkbox("설사 있음")
    inputs["sx_rash"] = st.checkbox("피부 발진/가려움 있음")
    inputs["sx_fever"] = st.checkbox("발열 증상 있음")

if category == "투석 환자":
    col1, col2 = st.columns(2)
    with col1:
        inputs["k"]   = num_input("칼륨 K (mEq/L)", key="k_d", placeholder="예: 5.8")
        inputs["na"]  = num_input("나트륨 Na (mEq/L)", key="na_d", placeholder="예: 136")
        inputs["ca"]  = num_input("칼슘 Ca (mg/dL)", key="ca_d", placeholder="예: 8.9")
        inputs["phos"]= num_input("인 Phosphorus (mg/dL)", key="phos", placeholder="예: 6.1")
    with col2:
        inputs["bun"] = num_input("BUN (mg/dL)", key="bun", placeholder="예: 65")
        inputs["cr"]  = num_input("Creatinine (mg/dL)", key="cr", placeholder="예: 9.2")
        inputs["alb"] = num_input("알부민 Albumin (g/dL)", key="alb_d", placeholder="예: 3.6")
        inputs["hb"]  = num_input("혈색소 Hb (g/dL)", key="hb_d", placeholder="예: 10.1")
    inputs["fluid_gain"] = num_input("투석 간 체중 증가(kg)", key="fluid_gain", placeholder="예: 3.0")

if category == "당뇨 환자":
    col1, col2 = st.columns(2)
    with col1:
        inputs["fpg"]   = num_input("식전(공복) 혈당 FPG (mg/dL)", key="fpg", placeholder="예: 115")
        inputs["pp2"]   = num_input("식후 2시간 혈당 PP2 (mg/dL)", key="pp2", placeholder="예: 195")
    with col2:
        inputs["hba1c"] = num_input("HbA1c (%)", key="hba1c", placeholder="예: 7.2")
        inputs["hb"]    = num_input("혈색소 Hb (g/dL)", key="hb_dm", placeholder="예: 12.8")
        inputs["alb"]   = num_input("알부민 Albumin (g/dL)", key="alb_dm", placeholder="예: 3.4")

# ─────────────────────────────
# 해석 실행 (카테고리별)
# ─────────────────────────────
if st.button("🔎 해석하기"):
    today = datetime.date.today()
    screen_lines = []
    report_lines = []
    write_header(report_lines)

    # 입력 요약 (라벨링)
    label_map = {
        "wbc":"WBC (x10³/µL)", "hb":"혈색소 Hb (g/dL)", "plt":"혈소판 PLT (x10³/µL)", "anc":"ANC (/µL)",
        "ca":"칼슘 Ca (mg/dL)", "na":"나트륨 Na (mEq/L)", "k":"칼륨 K (mEq/L)", "alb":"알부민 (g/dL)",
        "temp":"체온 (°C)", "fpg":"식전 FPG (mg/dL)", "pp2":"식후2시간 PP2 (mg/dL)",
        "hba1c":"HbA1c (%)","phos":"인 Phosphorus (mg/dL)", "bun":"BUN (mg/dL)", "cr":"Creatinine (mg/dL)",
        "fluid_gain":"투석 간 체중 증가 (kg)"
    }
    report_lines.append("## 입력 수치")
    for k, v in inputs.items():
        if isinstance(v, dict):  # 약물 dict 제외
            continue
        if exists(v):
            report_lines.append(f"- {label_map.get(k,k)}: {v}")
    report_lines.append("")

    # ── 항암 치료 ─────────────────
    if category == "항암 치료":
        FOODS = {
            "Hb_low": ["소고기", "시금치", "두부", "달걀 노른자", "렌틸콩"],
            "Alb_low": ["달걀", "연두부", "흰살 생선", "닭가슴살", "귀리죽"],
            "K_low": ["바나나", "감자", "호박죽", "고구마", "오렌지"],
            "Na_low": ["전해질 음료", "미역국", "바나나", "오트밀죽", "삶은 감자"],
            "Ca_low": ["연어통조림", "두부", "케일", "브로콜리", "참깨 제외"],
            "ANC_low": ["익힌 채소", "멸균 우유", "죽(쌀죽·호박죽)", "통조림 과일", "멸균 주스"]
        }
        wbc=inputs.get("wbc"); hb=inputs.get("hb"); plt=inputs.get("plt"); anc=inputs.get("anc")
        ca=inputs.get("ca"); na=inputs.get("na"); k=inputs.get("k"); alb=inputs.get("alb")
        temp=inputs.get("temp"); maint=inputs.get("maint", {}); active=inputs.get("active", {}); diuretic=inputs.get("diuretic", False)

        # 치료 요약
        if maint:
            screen_lines.append("🟢 유지요법: " + ", ".join([f"{d} {dose}정" for d, dose in maint.items()]))
            report_lines.append("**유지요법(경구):** " + ", ".join([f"{d} {dose}정" for d, dose in maint.items()]))
        if active:
            def _summarize_active(ad):
                parts=[]; 
                for d, info in ad.items():
                    if d.startswith("ARA-C"): parts.append(f"{d}({info.get('제형')}, {info.get('용량/주기','')})")
                    else: parts.append(f"{d}({info.get('용량/주기','')})")
                return ", ".join(parts)
            screen_lines.append("🔴 투여중: " + _summarize_active(active))
            report_lines.append("**투여중(주사/강화):** " + _summarize_active(active))
        if diuretic:
            screen_lines.append("💧 이뇨제 복용 중")
            report_lines.append("- 이뇨제 복용 중: 탈수/전해질 이상 주의")
        report_lines.append("")

        # 해석
        report_lines.append("## 해석 (항암 치료)")
        if exists(hb) and hb < 10:
            screen_lines.append(f"Hb {hb} → 빈혈 가능")
            report_lines.append(f"- **빈혈**: Hb {hb} g/dL (피로/창백 가능)")
            add_food(report_lines, FOODS["Hb_low"], "Hb 낮음 권장 식단")
            screen_lines.append("🥗 Hb 낮음 권장 식단: " + ", ".join(FOODS["Hb_low"]))
        if exists(alb) and alb < 3.5:
            screen_lines.append(f"Albumin {alb} → 저알부민")
            report_lines.append(f"- **저알부민혈증**: Albumin {alb} g/dL (회복력 저하)")
            add_food(report_lines, FOODS["Alb_low"], "알부민 낮음 권장 식단")
            screen_lines.append("🥗 알부민 낮음 권장 식단: " + ", ".join(FOODS["Alb_low"]))
        if exists(k) and k < 3.5:
            screen_lines.append(f"K {k} → 저칼륨")
            report_lines.append(f"- **저칼륨혈증**: K {k} mEq/L (부정맥 위험)")
            add_food(report_lines, FOODS["K_low"], "칼륨 낮음 권장 식단")
            screen_lines.append("🥗 칼륨 낮음 권장 식단: " + ", ".join(FOODS["K_low"]))
        if exists(na) and na < 135:
            screen_lines.append(f"Na {na} → 저나트륨")
            report_lines.append(f"- **저나트륨혈증**: Na {na} mEq/L (의식저하/경련 가능)")
            add_food(report_lines, FOODS["Na_low"], "나트륨 낮음 권장 식단")
            screen_lines.append("🥗 나트륨 낮음 권장 식단: " + ", ".join(FOODS["Na_low"]))
        if exists(ca) and ca < 8.5:
            screen_lines.append(f"Ca {ca} → 저칼슘")
            report_lines.append(f"- **저칼슘혈증**: Ca {ca} mg/dL (근육경련/저림)")
            add_food(report_lines, FOODS["Ca_low"], "칼슘 낮음 권장 식단")
            screen_lines.append("🥗 칼슘 낮음 권장 식단: " + ", ".join(FOODS["Ca_low"]))
        if exists(anc) and anc < 500:
            screen_lines.append(f"ANC {anc} → 심한 감염 위험")
            report_lines.append(f"- **심한 호중구감소증**: ANC {anc} /µL")
            report_lines.append("")
            report_lines.append(NEUTROPENIA_NOTICE)
            add_food(report_lines, FOODS["ANC_low"], "ANC 낮음 권장 식단")
            screen_lines.append("🥗 ANC 낮음 권장 식단: " + ", ".join(FOODS["ANC_low"]))

        # 체온/증상
        if exists(temp) and temp >= 37.8:
            report_lines.append("")
            report_lines.append("## 체온 가이드")
            if temp >= 38.5:
                screen_lines.append(f"🌡️ 체온 {temp}°C → 고열 주의")
                report_lines.append(f"- **고열 주의**: 체온 {temp}°C → 즉시 의료진 상의/내원 고려")
            elif 38.0 <= temp < 38.5:
                screen_lines.append(f"🌡️ 체온 {temp}°C → 발열 관찰")
                report_lines.append(f"- **발열 관찰**: 체온 {temp}°C → 1~2시간 재측정, 수분/전해질 보충")
            else:
                screen_lines.append(f"🌡️ 체온 {temp}°C → 미열")
                report_lines.append(f"- **미열**: 체온 {temp}°C → 증상 변화 시 보고")

        report_lines.append("")
        report_lines.append("## 증상 기반 가이드")
        if inputs.get("sx_mucositis"):
            screen_lines.append("🩺 구내염 → 자극적 음식 피하기, 미지근한 물로 자주 헹구기")
            report_lines.append("- **구내염**: 자극적 음식 피하고, 주치의 처방漱口액 사용 고려")
        if inputs.get("sx_diarrhea"):
            screen_lines.append("🩺 설사 → 수분·전해질 보충, 고섬유질 음식 피하기")
            report_lines.append("- **설사**: 탈수 주의, 지사제 사용은 주치의와 상의")
        if inputs.get("sx_rash"):
            screen_lines.append("🩺 피부 발진 → 보습제 사용, 자극 피하기")
            report_lines.append("- **피부 발진**: 보습제 사용, 심한 경우 피부과/혈액종양내과 상담")
        if inputs.get("sx_fever"):
            screen_lines.append("🩺 발열 증상 → 체온 연동 가이드 확인")
            report_lines.append("- **발열 증상**: 38.0~38.5 해열제/경과관찰, ≥38.5 즉시 병원 연락")

        report_lines.append("")
        report_lines.append(IRON_WARN)

    # ── 투석 환자 ─────────────────
    elif category == "투석 환자":
        # 기준값 (교육용)
        K_HIGH = 5.5; K_LOW = 3.5
        PHOS_HIGH = 5.5
        ALB_LOW = 3.8
        FLUID_MAX = 2.5  # kg

        k=inputs.get("k"); na=inputs.get("na"); ca=inputs.get("ca"); phos=inputs.get("phos")
        bun=inputs.get("bun"); cr=inputs.get("cr"); alb=inputs.get("alb"); hb=inputs.get("hb")
        fluid_gain=inputs.get("fluid_gain", 0.0)

        report_lines.append("## 해석 (투석 환자)")
        any_flag = False

        # 칼륨
        if exists(k):
            if k > K_HIGH:
                any_flag = True
                screen_lines.append(f"K {k} → 고칼륨혈증 위험")
                report_lines.append(f"- **고칼륨혈증 위험**: K {k} mEq/L")
                add_food(report_lines, ["살구/바나나 제한", "감자/고구마는 삶아 물 버리기", "콩/견과류 제한", "저칼륨 과일(사과/배)"], "칼륨 조절 식단")
                screen_lines.append("🥗 칼륨 조절: 바나나·감자·콩 제한, 삶아 물 버리기")
            elif k < K_LOW:
                any_flag = True
                screen_lines.append(f"K {k} → 저칼륨")
                report_lines.append(f"- **저칼륨혈증**: K {k} mEq/L")
                add_food(report_lines, ["바나나(의사 지시 시)", "키위", "오렌지", "고구마"], "칼륨 보충 식단")

        # 인
        if exists(phos) and phos > PHOS_HIGH:
            any_flag = True
            screen_lines.append(f"Phos {phos} → 고인산혈증")
            report_lines.append(f"- **고인산혈증**: Phosphorus {phos} mg/dL → 인결합제 복용 여부 확인")
            add_food(report_lines, ["우유/치즈/요거트 제한", "내장육/멸치/견과류 제한", "콜라/가공치즈 주의"], "인 제한 식단")

        # 알부민
        if exists(alb) and alb < ALB_LOW:
            any_flag = True
            screen_lines.append(f"Albumin {alb} → 저알부민(영양 불량)")
            report_lines.append(f"- **저알부민혈증**: Albumin {alb} g/dL → 단백질/에너지 섭취 부족 의심")
            add_food(report_lines, ["계란흰자", "흰살 생선", "닭가슴살", "연두부", "에너지 보충 음료(의사 지시 시)"], "단백질 보충 식단")

        # 수분
        if exists(fluid_gain) and fluid_gain > FLUID_MAX:
            any_flag = True
            screen_lines.append(f"체중 +{fluid_gain}kg → 수분 과다")
            report_lines.append(f"- **수분 과다**: 투석 간 체중 증가 {fluid_gain}kg → 수분/염분 제한 강화")
            add_food(report_lines, ["싱겁게 먹기", "국/찌개 국물 줄이기", "얼음 조각으로 갈증 조절"], "수분/염분 제한 팁")

        # Hb
        if exists(hb) and hb < 10:
            any_flag = True
            screen_lines.append(f"Hb {hb} → 빈혈(투석)")
            report_lines.append(f"- **빈혈**: Hb {hb} g/dL → EPO/철 상태 평가 필요")

        if not any_flag:
            screen_lines.append("✅ 입력 범위 내 특별한 경고 없음 (담당 의료진 지시 우선)")
            report_lines.append("- 입력 값 기준으로 특별한 경고 없음")

    # ── 당뇨 환자 ─────────────────
    elif category == "당뇨 환자":
        fpg=inputs.get("fpg"); pp2=inputs.get("pp2"); hba1c=inputs.get("hba1c"); alb=inputs.get("alb"); hb=inputs.get("hb")

        report_lines.append("## 해석 (당뇨 환자)")
        any_flag = False

        # FPG
        if exists(fpg):
            if fpg < 70:
                any_flag = True
                screen_lines.append(f"식전 FPG {fpg} → 저혈당")
                report_lines.append(f"- **저혈당**: FPG {fpg} mg/dL")
                add_food(report_lines, ["포도당 15g", "사과주스 150mL", "콜라(일반) 150mL"], "저혈당 응급 섭취 (15-15 규칙)")
            elif fpg > 130:
                any_flag = True
                screen_lines.append(f"식전 FPG {fpg} → 목표 초과")
                report_lines.append(f"- **공복 고혈당**: FPG {fpg} mg/dL → 식사/운동/약물 점검")

        # PP2
        if exists(pp2):
            if pp2 > 180:
                any_flag = True
                screen_lines.append(f"식후2시간 PP2 {pp2} → 목표 초과")
                report_lines.append(f"- **식후 고혈당**: 2hr {pp2} mg/dL → 탄수화물 분배/식사 순서(채-단백-탄수) 적용")
                add_food(report_lines, ["현미·잡곡 비중↑", "채소 먼저", "단백질 충분히", "단순당 음료 피하기"], "식후 혈당 관리 식단")

        # HbA1c
        if exists(hba1c):
            if hba1c >= 7.0:
                any_flag = True
                screen_lines.append(f"HbA1c {hba1c}% → 장기 조절 미흡")
                report_lines.append(f"- **장기 조절 미흡**: HbA1c {hba1c}% → 생활습관/약물 조정 논의")
            else:
                screen_lines.append(f"HbA1c {hba1c}% → 양호(개인 목표 확인)")
                report_lines.append(f"- **장기 조절 양호**: HbA1c {hba1c}%")

        # Hb (빈혈 동반 여부)
        if exists(hb) and hb < 10:
            any_flag = True
            screen_lines.append(f"Hb {hb} → 빈혈 동반")
            report_lines.append(f"- **빈혈**: Hb {hb} g/dL → 철/EPO/기저질환 평가")

        # Albumin
        if exists(alb) and alb < 3.5:
            any_flag = True
            screen_lines.append(f"Albumin {alb} → 영양 저하")
            report_lines.append(f"- **저알부민혈증**: Albumin {alb} g/dL → 단백질/에너지 보강")

        if not any_flag:
            screen_lines.append("✅ 입력 범위 내 특별한 경고 없음 (담당 의료진 지시 우선)")
            report_lines.append("- 입력 값 기준으로 특별한 경고 없음")

    # ── 일반 해석 ─────────────────
    elif category == "일반 해석":
        FOODS = {
            "Hb_low": ["소고기", "시금치", "두부", "달걀 노른자", "렌틸콩"],
            "Alb_low": ["달걀", "연두부", "흰살 생선", "닭가슴살", "귀리죽"],
            "K_low": ["바나나", "감자", "호박죽", "고구마", "오렌지"],
            "Na_low": ["전해질 음료", "미역국", "바나나", "오트밀죽", "삶은 감자"],
            "Ca_low": ["연어통조림", "두부", "케일", "브로콜리", "참깨 제외"]
        }
        hb=inputs.get("hb"); alb=inputs.get("alb"); k=inputs.get("k"); na=inputs.get("na"); ca=inputs.get("ca")
        report_lines.append("## 해석 (일반)")
        any_flag = False
        if exists(hb) and hb < 10:
            any_flag = True
            screen_lines.append(f"Hb {hb} → 빈혈 가능")
            report_lines.append(f"- **빈혈**: Hb {hb} g/dL")
            add_food(report_lines, FOODS["Hb_low"], "Hb 낮음 권장 식단")
        if exists(alb) and alb < 3.5:
            any_flag = True
            screen_lines.append(f"Albumin {alb} → 저알부민")
            report_lines.append(f"- **저알부민혈증**: Albumin {alb} g/dL")
            add_food(report_lines, FOODS["Alb_low"], "알부민 낮음 권장 식단")
        if exists(k) and k < 3.5:
            any_flag = True
            screen_lines.append(f"K {k} → 저칼륨")
            report_lines.append(f"- **저칼륨혈증**: K {k} mEq/L")
            add_food(report_lines, FOODS["K_low"], "칼륨 낮음 권장 식단")
        if exists(na) and na < 135:
            any_flag = True
            screen_lines.append(f"Na {na} → 저나트륨")
            report_lines.append(f"- **저나트륨혈증**: Na {na} mEq/L")
            add_food(report_lines, FOODS["Na_low"], "나트륨 낮음 권장 식단")
        if exists(ca) and ca < 8.5:
            any_flag = True
            screen_lines.append(f"Ca {ca} → 저칼슘")
            report_lines.append(f"- **저칼슘혈증**: Ca {ca} mg/dL")
            add_food(report_lines, FOODS["Ca_low"], "칼슘 낮음 권장 식단")
        if not any_flag:
            screen_lines.append("✅ 입력 범위 내 특별한 경고 없음 (담당 의료진 지시 우선)")
            report_lines.append("- 입력 값 기준으로 특별한 경고 없음")

    # 화면 출력
    st.subheader("📌 요약 결과")
    if screen_lines:
        for line in screen_lines:
            st.write("• " + line)
    else:
        st.info("표시할 요약이 없습니다.")

    # 저장/다운로드
    if nickname:
        with open(f"{nickname}_results.md", "a", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
            f.write("\n\n---\n\n")
        st.success(f"'{nickname}_results.md'에 결과가 저장되었습니다.")

        md_bytes = io.BytesIO("\n".join(report_lines).encode("utf-8"))
        st.download_button(
            "📥 이번 결과 .md 다운로드",
            data=md_bytes,
            file_name=f"{nickname}_{today}.md",
            mime="text/markdown"
        )
    else:
        st.warning("별명을 입력하면 결과를 저장/다운로드할 수 있습니다.")

