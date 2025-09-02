# -*- coding: utf-8 -*-
import io, math
from datetime import datetime
from reportlab.pdfgen import canvas as _pdf_canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ---- UI helpers ----
def _parse_numeric(raw, decimals=1):
    try:
        if raw is None or raw == "":
            return None
        v = float(raw)
        return round(v, decimals)
    except Exception:
        return None

def num_input_generic(label, key=None, decimals=1, placeholder="", as_int=False):
    import streamlit as st
    raw = st.text_input(label, key=key, placeholder=placeholder)
    v = _parse_numeric(raw, decimals=0 if as_int else decimals)
    if as_int and v is not None:
        v = int(v)
    return v

def entered(v):
    try:
        return v is not None and str(v) != "" and float(v) != 0
    except Exception:
        return False

# ---- minimal logic ----
def _range(name):
    # very rough normal ranges (for demo)
    ref = {
        "ANC": (1500, None),
        "Albumin": (3.5, 5.2),
        "Ca": (8.6, 10.2),
        "Na": (135, 145),
        "K": (3.5, 5.1),
        "CRP": (0.0, 0.5),
        "Hb": (12.0, 17.0),
        "혈소판": (150, 450),
    }
    return ref.get(name, (None, None))

def interpret_labs(vals, extras):
    from config import (ORDER, LBL_Alb, LBL_Ca, LBL_ANC, LBL_PLT, LBL_CRP, LBL_Na, LBL_K)
    lines = []
    # ANC / 식이
    anc = vals.get(LBL_ANC)
    if entered(anc):
        if anc < 500:
            lines.append("🚨 ANC 500 미만: 생야채·생과일 금지, 즉시 의료진과 상의/격리 식사, 외출 자제")
        elif anc < 1000:
            lines.append("⚠️ ANC 1000 미만: 익힌 음식 중심, 남은 음식 2시간 이후 섭취 금지")
        else:
            lines.append("✅ ANC 양호: 일반 위생수칙 유지")
    # Albumin
    alb = vals.get(LBL_Alb)
    if entered(alb) and alb < 3.5:
        lines.append("🥚 알부민 낮음: 달걀·연두부·흰살생선·닭가슴살·귀리죽 권장")
    # Calcium
    ca = vals.get(LBL_Ca)
    if entered(ca) and ca < 8.6:
        lines.append("🦴 칼슘 낮음: 연어통조림·두부·케일·브로콜리 권장(참깨 제외)")
    # PLT
    plt = vals.get(LBL_PLT)
    if entered(plt) and plt < 50:
        lines.append("🩸 혈소판 50 미만: 넘어짐/출혈 주의, 양치 부드럽게")
    # CRP
    crp = vals.get(LBL_CRP)
    if entered(crp) and crp >= 0.5:
        lines.append("🔥 염증 수치 상승: 발열·증상 추적, 필요 시 진료")
    # 전해질
    for k in (LBL_Na, LBL_K):
        v = vals.get(k)
        lo, hi = _range(k)
        if entered(v) and lo and v < lo:
            lines.append(f"⚠️ {k} 낮음: 전해질 보충/식이 조절")
    if not lines:
        lines.append("🙂 입력된 값 범위에서 특이 위험 신호 없음")
    return lines

def compare_with_previous(nickname, current_vals):
    # session_state 기반 비교는 app에서 처리하므로, 여기서는 간단한 비교만 반환
    out = []
    for k, v in current_vals.items():
        out.append(f"- {k}: 이번 {v} (이전 대비 비교는 저장 기록 이후 표시)")
    return out

def food_suggestions(vals, anc_place):
    from config import LBL_Alb, LBL_Ca
    fs = []
    alb = vals.get(LBL_Alb)
    ca = vals.get(LBL_Ca)
    if entered(alb) and alb < 3.5:
        fs.append("알부민 낮음 → 고단백 부드러운 음식 중심(달걀·연두부·흰살생선·닭가슴살·귀리죽).")
    if entered(ca) and ca < 8.6:
        fs.append("칼슘 낮음 → 연어통조림·두부·케일·브로콜리 (참깨 제외).")
    if fs and anc_place == "병원":
        fs.append("현재 병원 식사 중 → 병원식 권장 범위 내에서 선택.")
    return fs

def summarize_meds(meds):
    from bloodmap_app.data.drugs import ANTICANCER
    out = []
    for k, v in meds.items():
        meta = ANTICANCER.get(k, {})
        alias = meta.get("alias", "")
        aes = ", ".join(meta.get("aes", []))
        dose_desc = v.get("dose_or_tabs") or v.get("dose")
        if v.get("form"):
            out.append(f"- {k}({alias}) · 제형: {v['form']} · 용량: {dose_desc} → 주의: {aes}")
        else:
            out.append(f"- {k}({alias}) · 용량: {dose_desc} → 주의: {aes}")
    if not out:
        out.append("선택한 항암제가 없습니다.")
    return out

def abx_summary(extras_abx):
    out = []
    from bloodmap_app.data.drugs import ABX_GUIDE
    for cat, amt in extras_abx.items():
        tips = ", ".join(ABX_GUIDE.get(cat, []))
        out.append(f"- {cat} · 투여량: {amt} → 주의: {tips}")
    return out

def build_report(mode, meta, vals, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines):
    from config import APP_TITLE, DISCLAIMER
    lines = [f"# {APP_TITLE}", "", f"## 모드: {mode}", ""]
    for k, v in (meta or {}).items():
        lines.append(f"- **{k}**: {v}")
    lines += ["", "## 해석", ""]
    lines += cmp_lines or []
    if extra_vals:
        lines += ["", "## 추가 입력", ""] + [f"- {k}: {v}" for k, v in extra_vals.items()]
    if meds_lines:
        lines += ["", "## 항암제", ""] + meds_lines
    if abx_lines:
        lines += ["", "## 항생제", ""] + abx_lines
    if food_lines:
        lines += ["", "## 음식 가이드", ""] + food_lines
    lines += ["", "> " + DISCLAIMER]
    return "\n".join(lines)

def md_to_pdf_bytes_fontlocked(md_text):
    # 간단 PDF 렌더(텍스트만)
    buf = io.BytesIO()
    pdf = _pdf_canvas.Canvas(buf, pagesize=A4)
    try:
        pdfmetrics.registerFont(TTFont("NanumGothic", "fonts/NanumGothic.ttf"))
        font_name = "NanumGothic"
    except Exception:
        font_name = "Helvetica"
    pdf.setFont(font_name, 10)
    width, height = A4
    x, y = 40, height - 40
    for line in md_text.splitlines():
        if y < 40:
            pdf.showPage(); pdf.setFont(font_name, 10); y = height - 40
        pdf.drawString(x, y, line[:120])
        y -= 14
    pdf.save()
    buf.seek(0)
    return buf.read()

# ---- very small viewer helpers ----
def render_graphs():
    import streamlit as st
    st.markdown("#### 📈 추이 그래프 (데모)")
    st.line_chart([1,2,3,2,4])

def render_schedule(nickname):
    import streamlit as st
    st.markdown("#### 📅 항암 스케줄 (데모)")
    st.write("별명 기반 실제 스케줄 저장/불러오기는 확장 예정:", nickname)

# ---- visits counter (local session only) ----
class _Counter:
    def __init__(self):
        self.c = 0
    def bump(self):
        self.c += 1
    def count(self):
        return self.c

counter = _Counter()
