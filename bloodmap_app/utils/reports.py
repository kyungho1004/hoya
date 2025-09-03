# -*- coding: utf-8 -*-
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from ..config import FONT_PATH_REG

def build_report(mode, meta, vals, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines):
    lines = []
    lines.append(f"# 보고서 — 모드: {mode}")
    for k, v in meta.items():
        lines.append(f"- {k}: {v}")
    lines.append("\n## 입력 수치")
    for k, v in vals.items():
        if v is None: continue
        lines.append(f"- {k}: {v}")
    if extra_vals:
        lines.append("\n## 디테일 수치")
        for k, v in extra_vals.items():
            if v is None: continue
            lines.append(f"- {k}: {v}")
    if cmp_lines:
        lines.append("\n## 변화 비교")
        lines.extend(cmp_lines)
    if meds_lines:
        lines.append("\n## 항암제 요약")
        lines.extend(meds_lines)
    if abx_lines:
        lines.append("\n## 항생제 요약")
        lines.extend(abx_lines)
    if food_lines:
        lines.append("\n## 음식 가이드")
        lines.extend(food_lines)
    return "\n".join(lines)

def md_to_pdf_bytes_fontlocked(md_text):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    W, H = A4
    y = H - 20*mm
    # 폰트 등록 시도
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        pdfmetrics.registerFont(TTFont("NanumGothic", FONT_PATH_REG))
        c.setFont("NanumGothic", 10)
    except Exception:
        c.setFont("Helvetica", 10)
    for line in md_text.split("\n"):
        if y < 20*mm:
            c.showPage()
            try:
                c.setFont("NanumGothic", 10)
            except Exception:
                c.setFont("Helvetica", 10)
            y = H - 20*mm
        c.drawString(20*mm, y, line)
        y -= 6*mm
    c.showPage()
    c.save()
    return buffer.getvalue()
