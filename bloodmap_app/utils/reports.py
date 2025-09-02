from ..config import (APP_TITLE, DISCLAIMER, ORDER, FONT_PATH_REG)
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io, os

def _ensure_korean_font(font_path: str, font_name: str = "NanumGothic"):
    try:
        if font_name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(font_name, font_path))
        return font_name
    except Exception:
        return "Helvetica"

def build_report(mode, meta, vals, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines):
    lines = []
    lines.append(f"# {APP_TITLE}")
    lines.append("")
    lines.append("> " + DISCLAIMER)
    return "\n".join(lines)

def md_to_pdf_bytes_fontlocked(md_text: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    font_name = _ensure_korean_font(FONT_PATH_REG, "NanumGothic")
    c.setFont(font_name, 12)
    x = 20*mm
    y = height - 20*mm
    for line in md_text.split("\n"):
        c.drawString(x, y, line)
        y -= 6*mm
        if y < 20*mm:
            c.showPage()
            y = height - 20*mm
            c.setFont(font_name, 12)
    c.save()
    return buf.getvalue()
