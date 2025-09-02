
from io import BytesIO

def build_report(mode, meta, vals, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines):
    lines = ["# 피수치 가이드 결과 요약", ""]
    lines.append(f"- 모드: {mode}")
    for k,v in (meta or {}).items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 입력 수치")
    for k,v in (vals or {}).items():
        if v is not None: lines.append(f"- {k}: {v}")
    if cmp_lines:
        lines += ["", "## 변화 비교"] + cmp_lines
    if extra_vals:
        lines += ["", "## 암별 디테일"] + [f"- {k}: {v}" for k,v in extra_vals.items() if v is not None]
    if meds_lines:
        lines += ["", "## 항암제 요약"] + meds_lines
    if abx_lines:
        lines += ["", "## 항생제 요약"] + abx_lines
    if food_lines:
        lines += ["", "## 음식 가이드"] + food_lines
    return "\n".join(lines)

def md_to_pdf_bytes_fontlocked(md_text: str) -> bytes:
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        textobject = c.beginText(15*mm, height-20*mm)
        for line in md_text.splitlines():
            textobject.textLine(line)
        c.drawText(textobject)
        c.showPage()
        c.save()
        return buffer.getvalue()
    except Exception:
        raise FileNotFoundError("PDF 생성용 폰트/모듈이 없습니다. (reportlab 필요)")
