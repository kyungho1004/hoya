
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

ANTICANCER = {
    "6-MP":{"alias":"6-머캅토퓨린","aes":["골수억제","간수치 상승","구내염","오심"],"warn":["황달/진한 소변 시 진료","감염 징후 즉시 연락"],"ix":["알로푸리놀 병용 감량 가능","와파린 효과 변동"]},
    "MTX":{"alias":"메토트렉세이트","aes":["골수억제","간독성","신독성","구내염","광과민"],"warn":["탈수 시 독성↑","고용량 후 류코보린"],"ix":["NSAIDs/TMP-SMX 병용 독성↑","일부 PPI 상호작용"]},
    "ATRA":{"alias":"트레티노인","aes":["분화증후군","발열","피부/점막 건조","두통"],"warn":["분화증후군 의심 시 즉시 병원"],"ix":["테트라사이클린계와 가성뇌종양"]},
    "ARA-C":{"alias":"시타라빈","aes":["골수억제","발열","구내염","(HDAC) 신경독성"],"warn":["HDAC 시 신경증상 즉시 보고"],"ix":["효소유도제 상호작용"]},
    "G-CSF":{"alias":"그라신","aes":["골통/근육통","주사부위 반응","드물게 비장비대"],"warn":["좌상복부 통증 시 평가"],"ix":[]},
    "Hydroxyurea":{"alias":"하이드록시우레아","aes":["골수억제","피부색소침착","궤양"],"warn":["임신 회피"],"ix":[]},
    "Daunorubicin":{"alias":"도우노루비신","aes":["골수억제","심독성","오심/구토","점막염"],"warn":["누적용량 심기능"],"ix":["심독성↑ 병용 주의"]},
    "Idarubicin":{"alias":"이달루비신","aes":["골수억제","심독성","점막염"],"warn":["심기능"],"ix":[]},
    "Mitoxantrone":{"alias":"미토잔트론","aes":["골수억제","심독성","청록색 소변"],"warn":["심기능"],"ix":[]},
    "Cyclophosphamide":{"alias":"사이클로포스파미드","aes":["골수억제","출혈성 방광염","탈모"],"warn":["수분섭취·메스나"],"ix":["CYP 상호작용"]},
    "Etoposide":{"alias":"에토포사이드","aes":["골수억제","저혈압(주입)"],"warn":[],"ix":[]},
    "Topotecan":{"alias":"토포테칸","aes":["골수억제","설사"],"warn":[],"ix":[]},
    "Fludarabine":{"alias":"플루다라빈","aes":["면역억제","감염 위험↑","혈구감소"],"warn":["PCP 예방 고려"],"ix":[]},
    "Vincristine":{"alias":"빈크리스틴","aes":["말초신경병증","변비/장폐색"],"warn":["IT 투여 금지"],"ix":["CYP3A 상호작용"]},
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
IRON_WARN = "⚠️ 항암/백혈병 환자는 철분제 복용을 권장하지 않습니다. (철분제+비타민C 병용 시 흡수↑ → 반드시 주치의 상담)"

# ================== HELPERS ==================
def parse_vals(s: str):
    s = (s or "").replace("，", ",").replace("\r\n", "\n").replace("\r", "\n").strip("\n ")
    if not s:
        return [None]*len(ORDER)
    if ("," in s) and ("\n" not in s):
        tokens = [tok.strip() for tok in s.split(",")]
    else:
        tokens = [line.strip() for line in s.split("\n")]
    out = []
    for i in range(len(ORDER)):
        tok = tokens[i] if i < len(tokens) else ""
        try:
            out.append(float(tok) if tok != "" else None)
        except:
            out.append(None)
    return out

def entered(v):
    try:
        return v is not None and float(v) > 0
    except Exception:
        return False

def interpret_labs(vals):
    l = dict(zip(ORDER, vals))
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
        if ratio>20: out.append(f"- BUN/Cr {ratio:.1f}: 탈수 의심")
        elif ratio<10: out.append(f"- BUN/Cr {ratio:.1f}: 간질환/영양 고려")
    return out, l

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
        foods.append("🧼 호중구 감소: 생채소 금지, 익힌 음식(전자레인지 30초 이상), 조리 후 2시간 지나면 폐기, 껍질 과일은 주치의 상담 후.")
    foods.append(IRON_WARN)
    return foods

def sort_key_for_record(rec):
    d = rec.get("date")
    try:
        return datetime.fromisoformat(d)
    except Exception:
        pass
    try:
        return datetime.strptime(rec.get("ts",""), "%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.now()

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
help_text = "ORDER: " + ", ".join([f"{k}" for k in ORDER])
raw = st.text_area(
    "값을 순서대로 입력 (쉼표 또는 줄바꿈으로 구분)",
    height=180,
    placeholder="예) 5.2, 9.3, 42, 320, 8.6, 3.2, 138, 4.1, 2.3, 110, 6.4, 103, 84, 426, 0.13, 0.84, 6.2, 0.8, 29, 392",
    help=help_text
)

st.divider()
st.header("3️⃣ 카테고리 및 옵션")
category = st.radio("카테고리", ["일반 해석","항암치료","항생제","투석 환자","당뇨 환자"], horizontal=True)

meds, extras = {}, {}

if category == "항암치료":
    st.markdown("### 💊 항암제/보조제 입력")
    c1, c2 = st.columns(2)
    with c1:
        use_arac = st.checkbox("ARA-C 사용")
        if use_arac:
            form = st.selectbox("ARA-C 제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"])
            dose = st.number_input("ARA-C 용량/일(선택)", min_value=0.0, step=0.1)
            meds["ARA-C"] = {"form": form, "dose": dose}
    with c2:
        diuretic = st.checkbox("이뇨제 복용 중")
        if diuretic:
            extras["diuretic"] = True
    st.caption(FEVER_GUIDE)

    with st.expander("다른 항암제 추가"):
        cols = st.columns(3)
        keys = ["6-MP","MTX","ATRA","G-CSF","Hydroxyurea","Daunorubicin","Idarubicin","Mitoxantrone",
                "Cyclophosphamide","Etoposide","Topotecan","Fludarabine","Vincristine"]
        for i, k in enumerate(keys):
            with cols[i % 3]:
                if st.checkbox(f"{k} 사용", key=f"use_{k}"):
                    meds[k] = {"dose_or_tabs": st.number_input(f"{k} 알/용량", min_value=0.0, step=0.1, key=f"dose_{k}")}

elif category == "항생제":
    st.markdown("### 🧪 항생제")
    extras["abx"] = st.multiselect("사용 중인 항생제", list(ABX_GUIDE.keys()))

elif category == "투석 환자":
    st.markdown("### 🫧 투석 추가 항목")
    extras["urine_ml"] = st.number_input("하루 소변량 (mL)", min_value=0.0, step=10.0)
    extras["hd_today"] = st.checkbox("오늘 투석 시행")
    extras["post_hd_weight_delta"] = st.number_input("투석 후 체중 변화 (kg)", min_value=-10.0, max_value=10.0, step=0.1)
    extras["urine_salinity"] = st.number_input("소변 염도 (%)", min_value=0.0, step=0.1, help="가정용 염도계 값 (예: 0.2%)")
    if st.checkbox("이뇨제 복용 중", key="diuretic_on_dial"):
        extras["diuretic"] = True

elif category == "당뇨 환자":
    st.markdown("### 🍚 당뇨 지표")
    extras["FPG"] = st.number_input("식전 혈당 (mg/dL)", min_value=0.0, step=1.0)
    extras["PP1h"] = st.number_input("식후 1시간 혈당 (mg/dL)", min_value=0.0, step=1.0)
    extras["PP2h"] = st.number_input("식후 2시간 혈당 (mg/dL)", min_value=0.0, step=1.0)
    extras["HbA1c"] = st.number_input("HbA1c (%)", min_value=0.0, step=0.1, format="%.1f")

st.divider()
run = st.button("🔎 해석하기", use_container_width=True)

# ================== RUN ==================
if run:
    vals = parse_vals(raw)
    lines, labs = interpret_labs(vals)

    st.subheader("📋 해석 결과")
    if lines:
        for line in lines:
            st.write(line)
    else:
        st.info("입력된 수치가 없습니다. 위 순서대로 값을 넣어주세요.")

    # 음식 가이드
    fs = food_suggestions(labs)
    if fs:
        st.markdown("### 🥗 음식 가이드")
        for f in fs:
            st.write("- " + f)

    # 약물/항생제 요약
    if category == "항암치료" and meds:
        st.markdown("### 💊 항암제 부작용·상호작용 요약")
        for line in summarize_meds(meds):
            st.write(line)

    if category == "항생제" and extras.get("abx"):
        st.markdown("### 🧪 항생제 주의 요약")
        for a in extras["abx"]:
            st.write(f"• {a}: {', '.join(ABX_GUIDE[a])}")

    # 발열 가이드
    st.markdown("### 🌡️ 발열 가이드")
    st.write(FEVER_GUIDE)

    # 투석 환자용 염도 해석
    if category == "투석 환자" and extras.get("urine_salinity") is not None and extras["urine_salinity"] > 0:
        percent = float(extras["urine_salinity"])
        meq = percent / 0.9 * 154  # 0.9% NaCl ≈ 154 mEq/L
        st.markdown("### 🧂 소변 염도 해석")
        if percent < 0.2:
            st.write(f"소변 염도 {percent}% (≈ {meq:.0f} mEq/L): **매우 낮음** → 수분 과다/저염 가능성")
        elif percent > 1.0:
            st.write(f"소변 염도 {percent}% (≈ {meq:.0f} mEq/L): **높음** → 고염식/수분 부족 가능성")
        else:
            st.write(f"소변 염도 {percent}% (≈ {meq:.0f} mEq/L): **중간 범위** (대략 0.2~1.0% 근처)")

    # 보고서 MD 구성 (입력한 것만 표시)
    buf = [f"# BloodMap 보고서 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n",
           f"- 카테고리: {category}\n",
           f"- 별명: {nickname or '(미입력)'}\n",
           f"- 검사일: {test_date}\n\n",
           "## 수치 요약\n"]
    for key in ORDER:
        v = labs.get(key)
        if entered(v):
            label = LABEL_MAP.get(key, key)
            buf.append(f"- {label}: {v}\n")

    # 결과 요약 붙이기
    if lines:
        buf.append("\n## 해석 결과\n")
        for ln in lines:
            buf.append(ln + "\n")

    # 음식 가이드 붙이기
    if fs:
        buf.append("\n## 음식 가이드\n")
        for f in fs:
            buf.append("- " + f + "\n")

    # 투석 환자 추가 정보
    if category == "투석 환자":
        if extras.get("urine_salinity") is not None and extras["urine_salinity"] > 0:
            percent = float(extras["urine_salinity"])
            meq = percent / 0.9 * 154
            buf.append("\n## 투석 부가 정보\n")
            buf.append(f"- 소변 염도: {percent}% (≈ {meq:.0f} mEq/L)\n")
        if extras.get("urine_ml") is not None:
            buf.append(f"- 하루 소변량: {extras['urine_ml']} mL\n")
        if extras.get("hd_today") is not None:
            buf.append(f"- 오늘 투석 시행: {'예' if extras.get('hd_today') else '아니오'}\n")
        if extras.get("post_hd_weight_delta") is not None:
            buf.append(f"- 투석 후 체중 변화: {extras.get('post_hd_weight_delta')} kg\n")

    # 약물/항생제 붙이기 (상세는 .md에 담고 UI는 요약만)
    if category == "항암치료" and meds:
        buf.append("\n## 항암제 정보\n")
        for k, v in meds.items():
            info = ANTICANCER.get(k, {})
            buf.append(f"- {k} ({info.get('alias','')}):\n")
            if info.get("aes"): buf.append(f"  - 부작용: {', '.join(info['aes'])}\n")
            if info.get("warn"): buf.append(f"  - 주의: {', '.join(info['warn'])}\n")
            if info.get("ix"): buf.append(f"  - 상호작용: {', '.join(info['ix'])}\n")
            if k == "ARA-C" and isinstance(v, dict) and v.get("form"):
                buf.append(f"  - 제형: {v['form']}\n")

    if category == "항생제" and extras.get("abx"):
        buf.append("\n## 항생제 정보\n")
        for a in extras["abx"]:
            buf.append(f"- {a}: {', '.join(ABX_GUIDE[a])}\n")

    buf.append("\n---\n본 도구는 교육·보호자 보조용으로 제작되었으며, 최종 의학적 판단은 담당 의료진의 몫입니다.\n")

    report_md = "".join(buf)
    st.session_state.last_report_md = report_md

    # 다운로드 (MD / TXT / PDF)
    st.subheader("📥 보고서 다운로드")
    base = f"bloodmap_{nickname or 'anon'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    render_download_buttons_inline(report_md, base_filename=base, font_paths=["fonts/NanumGothic.ttf"], title="피수치 자동 해석 보고서")
    st.caption("📌 한글 PDF가 깨지면 저장소에 fonts/NanumGothic.ttf를 추가해 주세요.")

    # 저장 (세션)
    if nickname.strip():
        if st.checkbox("📝 이 별명으로 세션에 저장", value=True):
            rec = {
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "date": str(test_date),
                "category": category,
                "labs": {k: v for k, v in dict(zip(ORDER, parse_vals(raw))).items() if entered(v)},
                "meds": meds,
                "extras": extras
            }
            st.session_state.records.setdefault(nickname, []).append(rec)
            st.success("저장되었습니다. 아래 그래프에서 추이를 확인하세요.")
    else:
        st.info("별명을 입력하면 추이 그래프를 사용할 수 있어요.")

# ================== DATA EXPORT / IMPORT ==================
st.markdown("---")
st.subheader("💾 데이터 관리 (추이 그래프용)")
c1, c2 = st.columns(2)
with c1:
    json_bytes = json.dumps(st.session_state.records, ensure_ascii=False, indent=2).encode("utf-8")
    st.download_button("⬇️ 전체 데이터 내보내기 (.json)", data=json_bytes, file_name="bloodmap_records.json",
                       mime="application/json", use_container_width=True)
with c2:
    if HAS_PD and st.session_state.records:
        who = st.selectbox("CSV 내보낼 별명 선택", ["(선택)"] + sorted(st.session_state.records.keys()))
        if who != "(선택)":
            rows = st.session_state.records.get(who, [])
            if rows:
                flat = []
                for r in rows:
                    row = {"date": r.get("date"), "ts": r.get("ts")}
                    for k in ["WBC","Hb","PLT","CRP","ANC"]:
                        row[k] = r["labs"].get(k)
                    flat.append(row)
                df = pd.DataFrame(flat)
                csv = df.to_csv(index=False).encode("utf-8-sig")
                st.download_button("⬇️ 선택 별명 CSV 내보내기", data=csv, file_name=f"{who}_trend.csv",
                                   mime="text/csv", use_container_width=True)
            else:
                st.info("선택한 별명 데이터가 없습니다.")

uploaded = st.file_uploader("📤 데이터 불러오기 (.json)", type=["json"], accept_multiple_files=False)
if uploaded is not None:
    try:
        incoming = json.loads(uploaded.read().decode("utf-8"))
        if isinstance(incoming, dict):
            for nick, recs in incoming.items():
                if not isinstance(recs, list):
                    continue
                st.session_state.records.setdefault(nick, [])
                st.session_state.records[nick].extend([r for r in recs if isinstance(r, dict)])
            st.success("데이터가 병합되었습니다. 아래 그래프에서 확인하세요.")
        else:
            st.error("JSON 루트는 dict 형태여야 합니다. (예: { '홍길동': [ ... ] })")
    except Exception as e:
        st.error(f"불러오기 실패: {e}")

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
            rows_sorted = sorted(rows, key=sort_key_for_record)
            data = []
            for r in rows_sorted:
                row = {"ts": r.get("date") or r.get("ts")}
                for k in ["WBC","Hb","PLT","CRP","ANC"]:
                    row[k] = r["labs"].get(k)
                data.append(row)
            df = pd.DataFrame(data).set_index("ts")
            st.line_chart(df.dropna(how="all"))
        else:
            st.info("선택한 별명의 저장 기록이 없습니다.")
    else:
        st.info("아직 저장된 기록이 없습니다. 해석 후 저장을 눌러보세요.")
