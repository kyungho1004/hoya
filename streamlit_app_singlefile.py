
import json
from datetime import datetime
import streamlit as st

# Optional deps
try:
    import pandas as pd
    HAS_PD = True
except Exception:
    HAS_PD = False

# ================== INLINE EXPORTER (MD/TXT/PDF) ==================
from io import BytesIO
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

def markdown_to_text(md: str) -> str:
    if md is None: return ""
    text = md.replace("\r\n","\n").replace("\r","\n")
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r"[Image: \1] (\2)", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()

def _register_korean_font(font_paths=None) -> str:
    candidates = (font_paths or []) + [
        "fonts/NanumGothic.ttf",
        "fonts/NotoSansKR-Regular.otf",
        "fonts/NotoSansKR-Regular.ttf",
        "NanumGothic.ttf",
        "NotoSansKR-Regular.otf",
        "NotoSansKR-Regular.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                pdfmetrics.registerFont(TTFont("KoreanPrimary", p))
                return "KoreanPrimary"
            except Exception:
                pass
    return "Helvetica"

def markdown_to_pdf_bytes(md: str, *, font_paths=None, title="Report") -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm, title=title)
    font_name = _register_korean_font(font_paths)

    styles = getSampleStyleSheet()
    for k in ("Normal","Title","Heading1","Heading2","Heading3"):
        if k in styles: styles[k].fontName = font_name
    body = ParagraphStyle("Body", parent=styles["Normal"], fontName=font_name, fontSize=10.5, leading=14, spaceAfter=4)
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, leading=20, spaceAfter=8)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14, leading=18, spaceAfter=6)
    h3 = ParagraphStyle("H3", parent=styles["Heading3"], fontSize=12, leading=16, spaceAfter=6)

    story, bullet_block = [], []
    def flush_bullets():
        nonlocal bullet_block
        if bullet_block:
            items = [ListItem(Paragraph(re.sub(r"^\s*[-*]\s*", "", li).strip(), body)) for li in bullet_block]
            story.append(ListFlowable(items, bulletType="bullet", start="•", leftIndent=10, spaceAfter=6))
            bullet_block = []

    for raw in md.replace("\r\n","\n").replace("\r","\n").split("\n"):
        line = raw.rstrip()
        if not line.strip():
            flush_bullets(); story.append(Spacer(1,6)); continue
        if line.startswith("### "): flush_bullets(); story.append(Paragraph(line[4:].strip(), h3)); continue
        if line.startswith("## "):  flush_bullets(); story.append(Paragraph(line[3:].strip(), h2)); continue
        if line.startswith("# "):   flush_bullets(); story.append(Paragraph(line[2:].strip(), h1)); continue
        if re.match(r"^\s*[-*]\s+", line): bullet_block.append(line); continue
        line_html = (line.replace("**","<b>").replace("__","<b>").replace("*","").replace("_","").replace("`",""))
        story.append(Paragraph(line_html, body))
    flush_bullets()
    doc.build(story)
    pdf = buffer.getvalue(); buffer.close(); return pdf

def render_download_buttons_inline(report_md: str, base_filename: str = "report", *, font_paths=None, title="Report"):
    if not report_md or not isinstance(report_md, str):
        st.info("생성된 보고서가 없습니다. 먼저 해석 결과를 만들어주세요."); return
    md_bytes = report_md.encode("utf-8")
    txt_bytes = markdown_to_text(report_md).encode("utf-8")
    pdf_bytes = markdown_to_pdf_bytes(report_md, font_paths=font_paths, title=title)
    st.download_button("📝 보고서(.md) 다운로드", data=md_bytes, file_name=f"{base_filename}.md", mime="text/markdown", use_container_width=True)
    st.download_button("📄 보고서(.txt) 다운로드", data=txt_bytes, file_name=f"{base_filename}.txt", mime="text/plain", use_container_width=True)
    st.download_button("🧾 보고서(.pdf) 다운로드", data=pdf_bytes, file_name=f"{base_filename}.pdf", mime="application/pdf", use_container_width=True)

# ================== APP CONFIG ==================
st.set_page_config(page_title="피수치 자동 해석기 by Hoya", layout="centered")
st.title("🩸 피수치 자동 해석기")
st.markdown("👤 **제작: Hoya / 자문: Hoya·GPT**")

if "records" not in st.session_state:
    st.session_state.records = {}
if "last_report_md" not in st.session_state:
    st.session_state.last_report_md = ""

# ================== CONSTANTS ==================
ORDER = ["WBC","Hb","PLT","ANC","Ca","P","Na","K","Albumin","Glucose","Total Protein","AST","ALT","LDH","CRP","Cr","UA","TB","BUN","BNP"]
LABEL_MAP = {
    "WBC":"WBC (백혈구)","Hb":"Hb (혈색소)","PLT":"PLT (혈소판)","ANC":"ANC (호중구)","Ca":"Ca (칼슘)","P":"P (인)","Na":"Na (소디움)","K":"K (포타슘)",
    "Albumin":"Albumin (알부민)","Glucose":"Glucose (혈당)","Total Protein":"Total Protein (총단백)","AST":"AST","ALT":"ALT","LDH":"LDH","CRP":"CRP",
    "Cr":"Creatinine (Cr)","UA":"Uric Acid (요산)","TB":"Total Bilirubin (TB)","BUN":"BUN","BNP":"BNP"
}
FEVER_GUIDE = "🌡️ 38.0~38.5℃ 해열제/경과, 38.5℃↑ 병원 연락, 39.0℃↑ 즉시 병원. (ANC<500 동반 발열=응급)"
IRON_WARN = "⚠️ 항암/백혈병 환자는 철분제 복용을 권장하지 않습니다. (철분제+비타민C 병용 시 흡수↑ → 반드시 주치의 상담)"

# Minimal sets (omitted here for brevity)
ANTICANCER = {"MTX":{"alias":"메토트렉세이트","aes":["골수억제","간독성","신독성","구내염","광과민"],"warn":["탈수 시 독성↑","고용량 후 류코보린"],"ix":["NSAIDs/TMP-SMX 병용 독성↑","일부 PPI 상호작용"]}}
ABX_GUIDE = {"세팔로스포린계":["설사","일부 알코올과 병용 시 플러싱 유사"]}
FOODS = {
    "Albumin_low": ["달걀","연두부","흰살 생선","닭가슴살","귀리죽"],
    "K_low": ["바나나","감자","호박죽","고구마","오렌지"],
    "Hb_low": ["소고기","시금치","두부","달걀 노른자","렌틸콩"],
    "Na_low": ["전해질 음료","미역국","바나나","오트밀죽","삶은 감자"],
    "Ca_low": ["연어 통조림","두부","케일","브로콜리","(참깨 제외)"],
}

# ================== HELPERS ==================
def parse_vals(s: str):
    s = (s or "").replace("，", ",").replace("\r\n", "\n").replace("\r", "\n").strip("\n ")
    if not s: return [None]*len(ORDER)
    tokens = [tok.strip() for tok in (s.split(",") if ("," in s and "\n" not in s) else s.split("\n"))]
    out = []
    for i in range(len(ORDER)):
        tok = tokens[i] if i < len(tokens) else ""
        try: out.append(float(tok) if tok != "" else None)
        except: out.append(None)
    return out

def entered(v): 
    try: return v is not None and float(v) > 0
    except: return False

def interpret_labs(vals):
    l = dict(zip(ORDER, vals)); out=[]
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
        if ratio>20: out.append(f"- BUN/Cr {ratio:.1f}: 탈수 의심")
        elif ratio<10: out.append(f"- BUN/Cr {ratio:.1f}: 간질환/영양 고려")
    return out, l

def food_suggestions(l):
    foods=[]
    if entered(l.get("Albumin")) and l["Albumin"]<3.5: foods.append("알부민 낮음 → " + ", ".join(FOODS["Albumin_low"]))
    if entered(l.get("K")) and l["K"]<3.5: foods.append("칼륨 낮음 → " + ", ".join(FOODS["K_low"]))
    if entered(l.get("Hb")) and l["Hb"]<12: foods.append("Hb 낮음 → " + ", ".join(FOODS["Hb_low"]))
    if entered(l.get("Na")) and l["Na"]<135: foods.append("나트륨 낮음 → " + ", ".join(FOODS["Na_low"]))
    if entered(l.get("Ca")) and l["Ca"]<8.5: foods.append("칼슘 낮음 → " + ", ".join(FOODS["Ca_low"]))
    if entered(l.get("ANC")) and l["ANC"]<500:
        foods.append("🧼 호중구 감소: 생채소 금지, 익힌 음식(전자레인지 30초 이상), 2시간 지난 음식 금지.")
    foods.append(IRON_WARN); return foods

# ================== UI ==================
st.divider()
st.header("1️⃣ 환자 정보")
col1, col2 = st.columns(2)
with col1:
    nickname = st.text_input("별명(저장/그래프용)", placeholder="예: 홍길동")
with col2:
    test_date = st.date_input("검사 날짜", value=datetime.today())

st.divider()
st.header("2️⃣ 수치 입력 (한 칸에 모아서, 순서 고정)")
raw = st.text_area("값을 순서대로 입력 (쉼표 또는 줄바꿈으로 구분)",
                   height=180,
                   placeholder="예) 5.2, 9.3, 42, 320, 8.6, 3.2, 138, 4.1, 2.3, 110, 6.4, 103, 84, 426, 0.13, 0.84, 6.2, 0.8, 29, 392",
                   help="ORDER: " + ", ".join(ORDER))

st.divider()
st.header("3️⃣ 카테고리 및 옵션")
category = st.radio("카테고리", ["일반 해석","항암치료","항생제","투석 환자","당뇨 환자"], horizontal=True)

meds, extras = {}, {}

st.divider()
run = st.button("🔎 해석하기", use_container_width=True)

# ================== RUN ==================
if run:
    vals = parse_vals(raw)
    lines, labs = interpret_labs(vals)

    st.subheader("📋 해석 결과")
    if lines:
        for line in lines: st.write(line)
    else:
        st.info("입력된 수치가 없습니다. 위 순서대로 값을 넣어주세요.")

    # 음식 가이드
    fs = food_suggestions(labs)
    if fs:
        st.markdown("### 🥗 음식 가이드")
        for f in fs: st.write("- " + f)

    # 발열 가이드
    st.markdown("### 🌡️ 발열 가이드")
    st.write(FEVER_GUIDE)

    # 보고서 MD
    buf = [f"# BloodMap 보고서 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n",
           f"- 카테고리: {category}\n",
           f"- 별명: {nickname or '(미입력)'}\n",
           f"- 검사일: {test_date}\n\n",
           "## 수치 요약\n"]
    for key, label in LABEL_MAP.items():
        v = labs.get(key)
        if entered(v): buf.append(f"- {label}: {v}\n")
    if lines:
        buf.append("\n## 해석 결과\n"); buf.extend([ln+"\n" for ln in lines])
    if fs:
        buf.append("\n## 음식 가이드\n"); buf.extend(["- "+f+"\n" for f in fs])
    buf.append("\n---\n본 도구는 교육·보호자 보조용으로 제작되었으며, 최종 의학적 판단은 담당 의료진의 몫입니다.\n")
    report_md = "".join(buf)

    st.subheader("📥 보고서 다운로드")
    base = f"bloodmap_{nickname or 'anon'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    render_download_buttons_inline(report_md, base_filename=base, font_paths=["fonts/NanumGothic.ttf"], title="피수치 자동 해석 보고서")
    st.caption("📌 한글 PDF가 깨지면 저장소에 fonts/NanumGothic.ttf를 추가해 주세요.")

# ================== GRAPHS ==================
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
                row = {"ts": r.get("ts")}
                for k in ["WBC","Hb","PLT","CRP","ANC"]:
                    row[k] = r["labs"].get(k)
                data.append(row)
            import pandas as pd
            df = pd.DataFrame(data).set_index("ts")
            st.line_chart(df.dropna(how="all"))
        else:
            st.info("선택한 별명의 저장 기록이 없습니다.")
    else:
        st.info("아직 저장된 기록이 없습니다. 해석 후 저장을 눌러보세요.")
