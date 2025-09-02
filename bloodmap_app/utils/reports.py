
from ..config import (APP_TITLE, DISCLAIMER, ORDER, FONT_PATH_REG)
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io, os

def _ensure_korean_font(font_path: str, font_name: str = "NanumGothic"):
    """Register a TTF so that Korean is rendered properly in PDF."""
    try:
        if not os.path.exists(font_path):
            # Fall back: try to find in working dir (in case relative path differs)
            alt = os.path.join(os.getcwd(), font_path)
            if os.path.exists(alt):
                font_path = alt
        # Avoid double-registration errors
        if font_name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(font_name, font_path))
        return font_name
    except Exception:
        # As a last resort, return a base font (may break Korean rendering)
        return "Helvetica"

def build_report(mode, meta, vals, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines):
    lines = []
    lines.append(f"# {APP_TITLE}")
    lines.append("")
    lines.append("## 기본 정보")
    lines.append(f"- 모드: {mode}")
    if meta.get("anc_place"): lines.append(f"- 식사 장소(ANC 가이드): {meta['anc_place']}")
    if meta.get("group"): lines.append(f"- 암 그룹: {meta.get('group')} / {meta.get('cancer')}")
    if meta.get("infect_sel"): lines.append(f"- 소아 감염: {meta.get('infect_sel')}")
    lines.append("")
    lines.append("## 입력 수치")
    for k in ORDER:
        v = vals.get(k)
        if v not in (None, ""):
            lines.append(f"- {k}: {v}")
    if extra_vals:
        lines.append("")
        lines.append("## 추가 수치")
        for k,v in extra_vals.items():
            if v not in (None, ""):
                lines.append(f"- {k}: {v}")
    if cmp_lines:
        lines.append("")
        lines.append("## 수치 변화 비교")
        for l in cmp_lines: lines.append(f"- {l}")
    if meds_lines:
        lines.append("")
        lines.append("## 항암제 요약")
        for l in meds_lines: lines.append(f"- {l}")
    if abx_lines:
        lines.append("")
        lines.append("## 항생제 주의")
        for l in abx_lines: lines.append(f"- {l}")
    if food_lines:
        lines.append("")
        lines.append("## 음식 가이드")
        for l in food_lines: lines.append(f"- {l}")
    lines.append("")
    lines.append("> " + DISCLAIMER)
    return "\n".join(lines)

def md_to_pdf_bytes_fontlocked(md_text: str) -> bytes:
    """Render a very simple PDF from Markdown-like plain text, using NanumGothic for Korean."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    # Ensure font for Korean
    font_name = _ensure_korean_font(FONT_PATH_REG, "NanumGothic")
    # Title font slightly larger
    body_font_size = 11
    title_font_size = 14

    x = 20*mm
    y = height - 20*mm
    for raw_line in md_text.split("\n"):
        line = raw_line.rstrip("\n")
        # Section headers a bit larger/bold-like (we keep same font; ReportLab ttf will handle weight if it's a bold TTF)
        if line.startswith("# "):
            c.setFont(font_name, title_font_size)
            text = line[2:]
        elif line.startswith("## "):
            c.setFont(font_name, 12)
            text = line[3:]
        else:
            c.setFont(font_name, body_font_size)
            text = line

        # Simple wrapping at ~100 chars (ReportLab has no auto-wrap for drawString)
        max_chars = 100
        while len(text) > max_chars:
            chunk = text[:max_chars]
            c.drawString(x, y, chunk)
            y -= 6*mm
            text = text[max_chars:]
            if y < 20*mm:
                c.showPage()
                y = height - 20*mm
        c.drawString(x, y, text)
        y -= 6*mm

        if y < 20*mm:
            c.showPage()
            y = height - 20*mm

    c.save()
    return buf.getvalue()
