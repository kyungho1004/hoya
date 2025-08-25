import streamlit as st
import datetime, io, os, re
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

st.set_page_config(page_title="피수치 자동 해석기 (v9.1)", layout="centered")
st.title("🔬 피수치 자동 해석기 (v9.1)")
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
    s = re.sub(r"[^0-9,.-]", "", s)
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

def write_header(report_lines):
    today = datetime.date.today()
    report_lines.append(f"# 피수치 자동 해석 보고서 ({today})")
    report_lines.append("")
    report_lines.append("- 제작: Hoya/GPT · 자문: Hoya/GPT")
    report_lines.append("- 본 자료는 교육/보조용이며 **최종 승인은 주치의**에게 받으세요.")
    report_lines.append("")

def md_to_pdf_bytes(md_text: str) -> bytes:
    # 매우 단순한 PDF 렌더링(텍스트만) — 줄바꿈 기준으로 출력
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    left = 15 * mm
    top = height - 15 * mm
    line_height = 6 * mm
    y = top
    for line in md_text.split("\n"):
        # 아주 단순히 마크다운 기호 제거
        clean = line.replace("# ", "").replace("## ", "").replace("**", "").replace("-", "• ")
        if len(clean) > 110:
            # 길면 줄바꿈
            while len(clean) > 110:
                c.drawString(left, y, clean[:110])
                clean = clean[110:]
                y -= line_height
                if y < 20 * mm:
                    c.showPage(); y = top
            if clean:
                c.drawString(left, y, clean)
        else:
            c.drawString(left, y, clean)
        y -= line_height
        if y < 20 * mm:
            c.showPage(); y = top
    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()

NEUTROPENIA_NOTICE = (
    "⚠️ **호중구 낮음 위생 가이드**\n"
    "- 생채소 금지, 모든 음식은 충분히 익혀 섭취\n"
    "- 멸균/살균식품 권장\n"
    "- 조리 후 남은 음식은 **2시간 이후 섭취 비권장**\n"
    "- 껍질 있는 과일은 **주치의와 상담 후** 섭취 결정\n"
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

# 홈화면 안내
if st.sidebar.button("📲 홈 화면에 추가 방법"):
    st.sidebar.info(
        "### iPhone (iOS)\n"
        "1) Safari로 열기 (인앱 X)\n"
        "2) 하단 공유(⬆️) → '홈 화면에 추가'\n\n"
        "### Android\n"
        "1) Chrome으로 열기 (인앱 X)\n"
        "2) 주소창 오른쪽 ⋮ → '홈 화면에 추가' 또는 '앱 설치'\n"
        "3) 안 보이면: 설정 → 앱 → Chrome → '바로가기 추가 허용'"
    )

# ─────────────────────────────
# 입력 섹션
# ─────────────────────────────
st.subheader("📊 수치 입력")
inputs = {}

if category == "항암 치료":
    st.markdown("**🧪 19종 혈액검사 입력**")
    cols = st.columns(2)
    with cols[0]:
        inputs["wbc"] = num_input("WBC (백혈구) (x10³/µL)", key="wbc")
        inputs["hb"]  = num_input("Hb (적혈구)(g/dL)", key="hb")
        inputs["plt"] = num_input("PLT (혈소판) (x10³/µL)", key="plt")
        inputs["anc"] = num_input("ANC (호중구) (/µL)", key="anc")
        inputs["ca"]  = num_input("칼슘 Ca (mg/dL)", key="ca")
        inputs["na"]  = num_input("나트륨 Na (mEq/L)", key="na")
        inputs["k"]   = num_input("칼륨 K (mEq/L)", key="k")
        inputs["alb"] = num_input("알부민 Albumin (g/dL)", key="alb")
        inputs["glu"] = num_input("Glucose (mg/dL)", key="glu")
        inputs["tp"]  = num_input("총단백 TP (g/dL)", key="tp")
    with cols[1]:
        inputs["ast"] = num_input("AST (IU/L)", key="ast")
        inputs["alt"] = num_input("ALT (IU/L)", key="alt")
        inputs["ldh"] = num_input("LDH (IU/L)", key="ldh")
        inputs["crp"] = num_input("CRP(염증수치) (mg/dL)", key="crp")
        inputs["cr"]  = num_input("Creatinine(신장수치) (mg/dL)", key="cr")
        inputs["tb"]  = num_input("총빌리루빈(Total Bilirubin) (mg/dL)", key="tb")
        inputs["bun"] = num_input("BUN(mg/dL)", key="bun")
        inputs["bnp"] = num_input("BNP (pg/mL)", key="bnp")
        inputs["ua"]  = num_input("요산 UA (mg/dL)", key="ua")
    inputs["temp"] = num_input("체온 (°C)", key="temp")

elif category == "투석 환자":
    col1, col2 = st.columns(2)
    with col1:
        inputs["k"]   = num_input("칼륨 K (mEq/L)", key="k_d")
        inputs["na"]  = num_input("나트륨 Na (mEq/L)", key="na_d")
        inputs["ca"]  = num_input("칼슘 Ca (mg/dL)", key="ca_d")
        inputs["phos"]= num_input("인 Phosphorus (mg/dL)", key="phos")
    with col2:
        inputs["bun"] = num_input("BUN (mg/dL)", key="bun")
        inputs["cr"]  = num_input("Creatinine (mg/dL)", key="cr")
        inputs["alb"] = num_input("알부민 Albumin (g/dL)", key="alb_d")
        inputs["hb"]  = num_input("혈색소 Hb (g/dL)", key="hb_d")
    inputs["fluid_gain"] = num_input("투석 간 체중 증가(kg)", key="fluid_gain")

elif category == "당뇨 환자":
    col1, col2 = st.columns(2)
    with col1:
        inputs["fpg"]   = num_input("식전(공복) 혈당 FPG (mg/dL)", key="fpg")
        inputs["pp2"]   = num_input("식후 2시간 혈당 PP2 (mg/dL)", key="pp2")
    with col2:
        inputs["hba1c"] = num_input("HbA1c (당화혈색소)", key="hba1c")
        inputs["hb"]    = num_input("혈색소 Hb (g/dL)", key="hb_dm")
        inputs["alb"]   = num_input("알부민 Albumin (g/dL)", key="alb_dm")

elif category == "일반 해석":
    st.markdown("**👤 일반 환자 입력 (기본 항목)**")
    col1, col2 = st.columns(2)
    with col1:
        inputs["wbc"] = num_input("WBC 백혈구 (x10³/µL)", key="wbc_g")
        inputs["hb"]  = num_input("Hb 적혈구 (g/dL)", key="hb_g")
        inputs["plt"] = num_input("PLT 혈소판 (x10³/µL)", key="plt_g")
    with col2:
        inputs["anc"] = num_input("ANC 호중구 (/µL)", key="anc_g")
        inputs["crp"] = num_input("CRP 염증수치(mg/dL)", key="crp_g")
        inputs["temp"]= num_input("체온 (°C)", key="temp_g")

# ─────────────────────────────
# 해석 실행 (간단 버전)
# ─────────────────────────────
if st.button("🔎 해석하기"):
    today = datetime.date.today()
    screen_lines = []
    report_lines = []
    write_header(report_lines)

    # 항암식: 집 식단 + 병원 식단 정의
    HOME_FOODS = {
        "Hb_low": ["소고기", "시금치", "두부", "달걀 노른자", "렌틸콩"],
        "Alb_low": ["달걀", "연두부", "흰살 생선", "닭가슴살", "귀리죽"],
        "K_low": ["바나나", "감자", "호박죽", "고구마", "오렌지"],
        "Na_low": ["전해질 음료", "미역국", "오트밀죽", "삶은 감자"],
        "Ca_low": ["연어통조림", "두부", "케일", "브로콜리"]
    }
    HOSPITAL_FOODS = {
        "Hb_low": ["환자식 중 고단백 메뉴", "소고기죽/닭고기죽", "멸균팩 우유", "영양보충 음료(의사 지시)"],
        "Alb_low": ["고단백 환자식(단백질 강화)", "흰살생선죽/계란찜", "멸균팩 우유", "단백질 보충 음료"],
        "K_low": ["저칼륨 환자식 요청", "감자/고구마는 삶아 물 버린 메뉴", "사과/배 같은 저칼륨 과일 컵"],
        "ANC_low": ["멸균 우유/주스", "살균 요거트", "완전가열 조리식", "통조림 과일 컵"]
    }

    if category == "일반 해석":
        wbc=inputs.get("wbc"); hb=inputs.get("hb"); plt=inputs.get("plt")
        anc=inputs.get("anc"); crp=inputs.get("crp"); temp=inputs.get("temp")
        report_lines.append("## 해석 (일반 환자)")
        if exists(wbc) and wbc < 4:
            screen_lines.append(f"WBC {wbc} → 백혈구 감소")
            report_lines.append(f"- **백혈구 감소**: WBC {wbc}")
        if exists(hb) and hb < 10:
            screen_lines.append(f"Hb {hb} → 빈혈 가능")
            report_lines.append(f"- **빈혈**: Hb {hb}")
            report_lines.append(f"  - 집 식단: {', '.join(HOME_FOODS['Hb_low'])}")
            report_lines.append(f"  - 🏥 병원 식단: {', '.join(HOSPITAL_FOODS['Hb_low'])}")
        if exists(plt) and plt < 100:
            screen_lines.append(f"PLT {plt} → 혈소판 감소")
            report_lines.append(f"- **혈소판 감소**: PLT {plt}")
        if exists(anc) and anc < 500:
            screen_lines.append(f"ANC {anc} → 심한 호중구감소증")
            report_lines.append(f"- **심한 호중구감소증**: ANC {anc}")
            report_lines.append(NEUTROPENIA_NOTICE)
            report_lines.append(f"  - 🏠 집 식단(위생): {', '.join(HOME_FOODS.get('K_low', []))}")
            report_lines.append(f"  - 🏥 병원 식단(위생): {', '.join(HOSPITAL_FOODS['ANC_low'])}")
        if exists(crp) and crp > 0.5:
            screen_lines.append(f"CRP {crp} → 염증/감염 의심")
            report_lines.append(f"- **염증/감염 의심**: CRP {crp}")
        if exists(temp) and temp >= 37.8:
            if temp >= 39:
                screen_lines.append(f"🌡️ 체온 {temp}°C → 고열 (즉시 병원)")
                report_lines.append(f"- **고열**: {temp}°C → 즉시 병원 연락")
            elif temp >= 38.5:
                screen_lines.append(f"🌡️ 체온 {temp}°C → 38.5 이상 (즉시 병원)")
                report_lines.append(f"- **발열**: {temp}°C → 병원 연락 필요")
            else:
                screen_lines.append(f"🌡️ 체온 {temp}°C → 미열/관찰")
                report_lines.append(f"- **미열**: {temp}°C → 경과 관찰, 수분 보충")

    if category == "항암 치료":
        hb=inputs.get("hb"); alb=inputs.get("alb"); k=inputs.get("k"); anc=inputs.get("anc"); na=inputs.get("na"); ca=inputs.get("ca"); temp=inputs.get("temp")
        report_lines.append("## 해석 (항암 치료)")
        if exists(hb) and hb < 10:
            screen_lines.append(f"Hb {hb} → 빈혈 가능")
            report_lines.append(f"- **빈혈**: Hb {hb}")
            report_lines.append(f"  - 🏠 집 식단: {', '.join(HOME_FOODS['Hb_low'])}")
            report_lines.append(f"  - 🏥 병원 식단: {', '.join(HOSPITAL_FOODS['Hb_low'])}")
        if exists(alb) and alb < 3.5:
            screen_lines.append(f"Albumin {alb} → 저알부민")
            report_lines.append(f"- **저알부민혈증**: Albumin {alb}")
            report_lines.append(f"  - 🏠 집 식단: {', '.join(HOME_FOODS['Alb_low'])}")
            report_lines.append(f"  - 🏥 병원 식단: {', '.join(HOSPITAL_FOODS['Alb_low'])}")
        if exists(k) and k < 3.5:
            screen_lines.append(f"K {k} → 저칼륨")
            report_lines.append(f"- **저칼륨혈증**: K {k}")
            report_lines.append(f"  - 🏠 집 식단: {', '.join(HOME_FOODS['K_low'])}")
            report_lines.append(f"  - 🏥 병원 식단: {', '.join(HOSPITAL_FOODS['K_low'])}")
        if exists(na) and na < 135:
            report_lines.append(f"- **저나트륨혈증**: Na {na}")
        if exists(ca) and ca < 8.5:
            report_lines.append(f"- **저칼슘혈증**: Ca {ca}")
        if exists(anc) and anc < 500:
            screen_lines.append(f"ANC {anc} → 심한 감염 위험")
            report_lines.append(f"- **심한 호중구감소증**: ANC {anc}")
            report_lines.append(NEUTROPENIA_NOTICE)
            report_lines.append(f"  - 🏥 병원 식단(멸균/살균): {', '.join(HOSPITAL_FOODS['ANC_low'])}")
        if exists(temp) and temp >= 37.8:
            report_lines.append("")
            report_lines.append("## 체온 가이드(항암)")
            if temp >= 38.5:
                screen_lines.append(f"🌡️ 체온 {temp}°C → 고열 주의")
                report_lines.append(f"- **고열 주의**: 즉시 의료진 상의/내원 고려")
            elif 38.0 <= temp < 38.5:
                screen_lines.append(f"🌡️ 체온 {temp}°C → 발열 관찰")
                report_lines.append(f"- **발열 관찰**: 1~2시간 후 재측정, 수분/전해질 보충")
            else:
                screen_lines.append(f"🌡️ 체온 {temp}°C → 미열")
                report_lines.append(f"- **미열**: 증상 변화 시 보고")

    # 결과 출력
    st.subheader("📌 요약 결과")
    if screen_lines:
        for line in screen_lines:
            st.write("• " + line)
    else:
        st.info("표시할 요약이 없습니다.")

    # 저장/다운로드 (.md + .pdf)
    if nickname:
        md_text = "\n".join(report_lines)
        with open(f"{nickname}_results.md", "a", encoding="utf-8") as f:
            f.write(md_text)
            f.write("\n\n---\n\n")
        st.success(f"'{nickname}_results.md'에 결과가 저장되었습니다.")

        md_bytes = io.BytesIO(md_text.encode("utf-8"))
        st.download_button("📥 이번 결과 .md 다운로드", data=md_bytes, file_name=f"{nickname}_{today}.md", mime="text/markdown")

        pdf_bytes = md_to_pdf_bytes(md_text)
        st.download_button("🧾 PDF로 다운로드", data=pdf_bytes, file_name=f"{nickname}_{today}.pdf", mime="application/pdf")
    else:
        st.warning("별명을 입력하면 결과를 저장/다운로드할 수 있습니다.")

