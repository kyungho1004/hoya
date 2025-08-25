import streamlit as st
import datetime, io, os

st.set_page_config(page_title="피수치 자동 해석기", layout="centered")
st.title("🔬 피수치 자동 해석기")
st.caption("제작: Hoya/GPT · 자문: Hoya/GPT")
st.write("※ 본 결과는 교육/보조 용도이며 **최종 승인 = 주치의** 입니다.")

if "views" not in st.session_state:
    st.session_state.views = 0
st.session_state.views += 1
st.sidebar.success(f"조회수: {st.session_state.views}")

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

st.subheader("📊 혈액 수치 입력 (입력한 것만 해석/표시)")
col1, col2 = st.columns(2)

with col1:
    wbc = st.number_input("WBC (백혈구)", min_value=0.0, step=0.1, format="%.1f", key="wbc")
    hb  = st.number_input("Hb (헤모글로빈)", min_value=0.0, step=0.1, format="%.1f", key="hb")
    plt = st.number_input("혈소판 (PLT)", min_value=0.0, step=1.0, format="%.0f", key="plt")
    anc = st.number_input("ANC (호중구)", min_value=0.0, step=10.0, format="%.0f", key="anc")

with col2:
    ca  = st.number_input("Ca²⁺ (칼슘)", min_value=0.0, step=0.1, format="%.1f", key="ca")
    na  = st.number_input("Na⁺ (소디움)", min_value=0.0, step=0.1, format="%.1f", key="na")
    k   = st.number_input("K⁺ (포타슘)", min_value=0.0, step=0.1, format="%.1f", key="k")
    alb = st.number_input("Albumin (알부민)", min_value=0.0, step=0.1, format="%.1f", key="alb")

st.subheader("💊 항암 치료 상태 입력")

st.markdown("**🟢 유지요법 (경구제)**")
maint_drugs = ["6-MP", "MTX", "베사노이드"]
maint = {}
mcols = st.columns(3)
for i, d in enumerate(maint_drugs):
    with mcols[i]:
        if st.checkbox(f"{d} 복용", key=f"maint_use_{d}"):
            dose = st.number_input(f"{d} 알약 개수(소수 가능)", step=0.1, key=f"maint_dose_{d}")
            maint[d] = dose

st.markdown("**🔴 항암제 투여중 (주사/강화요법 등)**")
active_drugs = [
    "ARA-C (아라씨)", "도우노루비신", "사이클로포스파마이드",
    "에토포사이드", "토포테칸", "플루다라빈",
    "비크라빈", "미토잔트론", "이달루시신",
    "하이드록시우레아", "그라신(G-CSF)"
]
active = {}
for d in active_drugs:
    use = st.checkbox(f"{d} 투여", key=f"active_use_{d}")
    if use:
        if d.startswith("ARA-C"):
            form = st.selectbox(f"아라씨 제형 선택", ["정맥(IV)", "피하(SC)", "고용량(HDAC)"], key="arac_form")
            sched = st.text_input("용량/주기 (예: 100mg/m² q12h x 7d)", key="arac_s")
            active[d] = {"제형": form, "용량/주기": sched}
        else:
            sched = st.text_input(f"{d} 용량/주기", key=f"active_s_{d}")
            active[d] = {"용량/주기": sched}

diuretic = st.checkbox("💧 이뇨제 복용 중")

FOODS = {
    "Hb_low": ["소고기", "시금치", "두부", "달걀 노른자", "렌틸콩"],
    "Alb_low": ["달걀", "연두부", "흰살 생선", "닭가슴살", "귀리죽"],
    "K_low": ["바나나", "감자", "호박죽", "고구마", "오렌지"],
    "Na_low": ["전해질 음료", "미역국", "바나나", "오트밀죽", "삶은 감자"],
    "Ca_low": ["연어통조림", "두부", "케일", "브로콜리", "참깨 제외"],
    "ANC_low": ["익힌 채소", "멸균 우유", "죽(쌀죽·호박죽)", "통조림 과일", "멸균 주스"]
}

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

def exists(x, zero_ok=False):
    if zero_ok:
        return True
    return x is not None and x != 0

def add_food(lines, key, title):
    foods = ", ".join(FOODS[key])
    lines.append(f"🥗 **{title}** → {foods}")

def summarize_active(active_dict):
    parts = []
    for d, info in active_dict.items():
        if d.startswith("ARA-C"):
            parts.append(f"{d}({info.get('제형')}, {info.get('용량/주기','')})")
        else:
            parts.append(f"{d}({info.get('용량/주기','')})")
    return ", ".join(parts)

def summarize_maint(mdict):
    return ", ".join([f"{d} {dose}정" for d, dose in mdict.items()])

if st.button("🔎 해석하기"):
    today = datetime.date.today()
    screen_lines = []
    report_lines = []

    report_lines.append(f"# 피수치 자동 해석 보고서 ({today})")
    report_lines.append("")
    report_lines.append("- 제작: Hoya/GPT · 자문: Hoya/GPT")
    report_lines.append("- 본 자료는 교육/보조용이며 **최종 승인은 주치의**에게 받으세요.")
    report_lines.append("")

    report_lines.append("## 입력 수치")
    any_input = False
    if exists(wbc): report_lines.append(f"- WBC: {wbc} x10³/µL"); any_input=True
    if exists(hb):  report_lines.append(f"- Hb: {hb} g/dL"); any_input=True
    if exists(plt): report_lines.append(f"- 혈소판: {plt} x10³/µL"); any_input=True
    if exists(anc): report_lines.append(f"- ANC: {anc} /µL"); any_input=True
    if exists(ca):  report_lines.append(f"- Ca: {ca} mg/dL"); any_input=True
    if exists(na):  report_lines.append(f"- Na: {na} mEq/L"); any_input=True
    if exists(k):   report_lines.append(f"- K: {k} mEq/L"); any_input=True
    if exists(alb): report_lines.append(f"- Albumin: {alb} g/dL"); any_input=True
    if not any_input:
        report_lines.append("- (입력된 수치 없음)")
    report_lines.append("")

    if maint:
        screen_lines.append(f"🟢 유지요법: {summarize_maint(maint)}")
        report_lines.append(f"**유지요법(경구):** {summarize_maint(maint)}")
    if active:
        screen_lines.append(f"🔴 투여중: {summarize_active(active)}")
        report_lines.append(f"**투여중(주사/강화):** {summarize_active(active)}")
    if diuretic:
        screen_lines.append("💧 이뇨제 복용 중")
        report_lines.append("- 이뇨제 복용 중: 탈수/전해질 이상 주의")
    report_lines.append("")

    report_lines.append("## 해석")
    if exists(hb) and hb < 10:
        screen_lines.append(f"Hb {hb} → 빈혈 가능")
        report_lines.append(f"- **빈혈**: Hb {hb} g/dL (피로/창백 가능)")
        add_food(report_lines, "Hb_low", "Hb 낮음 식단")

    if exists(alb) and alb < 3.5:
        screen_lines.append(f"Albumin {alb} → 저알부민")
        report_lines.append(f"- **저알부민혈증**: Albumin {alb} g/dL (회복력 저하)")
        add_food(report_lines, "Alb_low", "알부민 낮음 식단")

    if exists(k) and k < 3.5:
        screen_lines.append(f"K {k} → 저칼륨")
        report_lines.append(f"- **저칼륨혈증**: K {k} mEq/L (부정맥 위험)")
        add_food(report_lines, "K_low", "칼륨 낮음 식단")

    if exists(na) and na < 135:
        screen_lines.append(f"Na {na} → 저나트륨")
        report_lines.append(f"- **저나트륨혈증**: Na {na} mEq/L (의식저하/경련 가능)")
        add_food(report_lines, "Na_low", "나트륨 낮음 식단")

    if exists(ca) and ca < 8.5:
        screen_lines.append(f"Ca {ca} → 저칼슘")
        report_lines.append(f"- **저칼슘혈증**: Ca {ca} mg/dL (근육경련/저림)")
        add_food(report_lines, "Ca_low", "칼슘 낮음 식단")

    # ✅ ANC: 한 번만, 화면+보고서 모두 출력
    if exists(anc) and anc < 500:
        screen_lines.append(f"ANC {anc} → 심한 감염 위험")
        report_lines.append(f"- **심한 호중구감소증**: ANC {anc} /µL")
        report_lines.append("")
        report_lines.append(NEUTROPENIA_NOTICE)
        add_food(report_lines, "ANC_low", "ANC 낮음 권장 식단")
        screen_lines.append("🥗 ANC 낮음 권장 식단: 익힌 채소, 멸균 우유, 죽, 통조림 과일, 멸균 주스")

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
    else:
        st.warning("별명을 입력하면 결과를 저장/다운로드할 수 있습니다.")
