import streamlit as st
import datetime

st.set_page_config(page_title="피수치 자동 해석기", layout="centered")
st.title("🔬 피수치 자동 해석기 by Hoya")
st.write("입력한 수치에 따라 해석 결과와 식이 가이드를 제공합니다.")

nickname = st.text_input("👤 별명 (닉네임)", max_chars=20)
category = st.selectbox("📂 해석 카테고리", ["항암 치료", "일반 해석", "투석 환자", "당뇨"])

# 수치 입력을 문자열로 받아서 실제 입력된 항목만 추출
def float_input(label):
    val = st.text_input(label)
    return float(val) if val.strip() else None

# 주요 수치 입력
wbc = float_input("WBC (백혈구)")
hb = float_input("Hb (적혈구)")
plt = float_input("혈소판 (PLT)")
anc = float_input("ANC (호중구)")
ca = float_input("칼슘 (Ca²⁺)")
na = float_input("나트륨 (Na⁺)")
k = float_input("칼륨 (K⁺)")
alb = float_input("알부민 (Albumin)")
glu = float_input("혈당 (Glucose)")
tp = float_input("총단백 (Total Protein)")
ast = float_input("AST")
alt = float_input("ALT")
ldh = float_input("LDH")
crp = float_input("CRP")
cr = float_input("크레아티닌 (Cr)")
tb = float_input("총 빌리루빈 (TB)")
bun = float_input("BUN")
bnp = float_input("BNP")
ua = float_input("요산 (UA)")

# 항암제 입력
st.subheader("💊 항암제 복용")
chemo_dict = {}
chemo_list = ["6-MP", "MTX", "베사노이드", "아라씨(IV)", "아라씨(SC)", "아라씨(HDAC)",
              "하이드록시우레아", "비크라빈", "도우노루비신", "이달루시신", "미토잔트론",
              "사이클로포스파마이드", "에토포사이드", "토포테칸", "플루다라빈"]
for drug in chemo_list:
    val = st.text_input(f"{drug} 복용량 (정)")
    chemo_dict[drug] = float(val) if val.strip() else None

# 이뇨제
diuretic = st.checkbox("💧 이뇨제 복용 중")

if st.button("✅ 결과 해석하기"):
    st.success("📊 수치를 기반으로 해석 결과를 생성했습니다.")
    st.markdown("※ 결과는 참고용이며, 최종 판단은 주치의와 상의하세요.")
    st.write("🔽 아래에서 보고서를 다운로드하세요.")

    report_lines = [f"# 피수치 해석 보고서 ({datetime.date.today()})", f"**닉네임**: {nickname}", f"**카테고리**: {category}", "---"]
    if wbc is not None: report_lines.append(f"- WBC: {wbc}")
    if hb is not None: report_lines.append(f"- Hb: {hb}")
    if plt is not None: report_lines.append(f"- 혈소판: {plt}")
    if anc is not None: report_lines.append(f"- 호중구: {anc}")
    if alb is not None and alb < 3.5:
        report_lines.append("  - ⛔ 알부민 수치 낮음 → 달걀, 연두부, 흰살생선 등 권장")
    if k is not None and k < 3.5:
        report_lines.append("  - ⛔ 칼륨 낮음 → 바나나, 감자, 오렌지 등 권장")
    if hb is not None and hb < 9:
        report_lines.append("  - ⛔ 빈혈 의심 → 소고기, 달걀 노른자, 렌틸콩 등 권장")
    if anc is not None and anc < 500:
        report_lines.append("  - ⛔ 호중구 감소 → 생야채 금지, 멸균식품 권장")
    if diuretic:
        report_lines.append("  - ⚠️ 이뇨제 복용 중 → 탈수/전해질 이상 주의")

    report_lines.append("---\n🧾 제작: Hoya / GPT\n자문: Hoya / GPT")
    full_report = "\n".join(report_lines)

    st.download_button("📥 보고서 다운로드 (.md)", data=full_report, file_name="report.md")
