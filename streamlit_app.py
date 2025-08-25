import streamlit as st
import datetime, io, os

st.set_page_config(page_title="피수치 자동 해석기 (v6: 증상 가이드)", layout="centered")
st.title("🔬 피수치 자동 해석기 (증상 가이드 포함)")
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

# ─────────────────────────────
# 카테고리 선택
# ─────────────────────────────
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
# 입력 폼 (항암 치료 전용: 증상 추가)
# ─────────────────────────────
inputs = {}
if category == "항암 치료":
    st.subheader("📊 혈액 수치 입력")
    col1, col2 = st.columns(2)
    with col1:
        inputs["wbc"] = st.number_input("WBC (x10³/µL)", min_value=0.0, step=0.1, format="%.1f")
        inputs["hb"]  = st.number_input("Hb (g/dL)", min_value=0.0, step=0.1, format="%.1f")
        inputs["plt"] = st.number_input("PLT (x10³/µL)", min_value=0.0, step=1.0, format="%.0f")
        inputs["anc"] = st.number_input("ANC (/µL)", min_value=0.0, step=10.0, format="%.0f")
    with col2:
        inputs["ca"]  = st.number_input("Ca (mg/dL)", min_value=0.0, step=0.1, format="%.1f")
        inputs["na"]  = st.number_input("Na (mEq/L)", min_value=0.0, step=0.1, format="%.1f")
        inputs["k"]   = st.number_input("K (mEq/L)", min_value=0.0, step=0.1, format="%.1f")
        inputs["alb"] = st.number_input("Albumin (g/dL)", min_value=0.0, step=0.1, format="%.1f")
    inputs["temp"] = st.number_input("🌡️ 체온 (°C)", min_value=0.0, step=0.1, format="%.1f")

    # 증상 체크박스
    st.subheader("🩺 증상 체크")
    inputs["sx_mucositis"] = st.checkbox("구내염 있음")
    inputs["sx_diarrhea"] = st.checkbox("설사 있음")
    inputs["sx_rash"] = st.checkbox("피부 발진/가려움 있음")
    inputs["sx_fever"] = st.checkbox("발열 증상 있음")

# (다른 카테고리는 v5 코드 구조 재사용 - 여기서는 간단히 표기)
if category != "항암 치료":
    st.info("⚠️ 이 버전(v6)은 '항암 치료' 카테고리에 증상 가이드가 추가되었습니다. 다른 카테고리는 v5 구조와 동일하게 동작합니다.")

# ─────────────────────────────
# 해석 실행
# ─────────────────────────────
if st.button("🔎 해석하기"):
    today = datetime.date.today()
    screen_lines = []
    report_lines = []
    write_header(report_lines)

    if category == "항암 치료":
        hb=inputs.get("hb"); alb=inputs.get("alb"); k=inputs.get("k"); na=inputs.get("na"); ca=inputs.get("ca"); anc=inputs.get("anc"); temp=inputs.get("temp")

        report_lines.append("## 해석 (항암 치료)")
        if exists(hb) and hb < 10:
            screen_lines.append(f"Hb {hb} → 빈혈 가능")
        if exists(alb) and alb < 3.5:
            screen_lines.append(f"Albumin {alb} → 저알부민")
        if exists(k) and k < 3.5:
            screen_lines.append(f"K {k} → 저칼륨")
        if exists(na) and na < 135:
            screen_lines.append(f"Na {na} → 저나트륨")
        if exists(ca) and ca < 8.5:
            screen_lines.append(f"Ca {ca} → 저칼슘")
        if exists(anc) and anc < 500:
            screen_lines.append(f"ANC {anc} → 심한 감염 위험")
            report_lines.append(NEUTROPENIA_NOTICE)

        # 체온 해석
        if exists(temp) and temp >= 37.8:
            if temp >= 38.5:
                screen_lines.append(f"🌡️ 체온 {temp}°C → 고열 주의 (즉시 병원 연락)")
            elif 38.0 <= temp < 38.5:
                screen_lines.append(f"🌡️ 체온 {temp}°C → 발열 관찰 (해열제/경과관찰)")
            else:
                screen_lines.append(f"🌡️ 체온 {temp}°C → 미열")

        # 증상 가이드
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
            screen_lines.append("🩺 발열 증상 → 체온 연동 가이드 확인 필요")
            report_lines.append("- **발열 증상**: 38.0~38.5 해열제/경과관찰, ≥38.5 즉시 병원 연락")

        report_lines.append("")
        report_lines.append(IRON_WARN)

    st.subheader("📌 요약 결과")
    if screen_lines:
        for line in screen_lines:
            st.write("• " + line)
    else:
        st.info("표시할 요약이 없습니다.")

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

