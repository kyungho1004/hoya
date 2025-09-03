
from datetime import datetime
def build_report(mode, meta, vals, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines):
    lines = ["# 피수치 가이드 보고서", f"- 생성시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
    lines.append(f"- 모드: {mode}")
    if meta.get("group"): lines.append(f"- 그룹/진단: {meta.get('group')} / {meta.get('cancer')}")
    lines.append("\n## 입력 수치")
    for k, v in vals.items():
        if v is not None and str(v)!="":
            lines.append(f"- {k}: {v}")
    if extra_vals:
        lines.append("\n## 특수검사")
        for k, v in extra_vals.items():
            if v is not None and str(v)!="":
                lines.append(f"- {k}: {v}")
    if meds_lines:
        lines.append("\n## 항암제 요약")
        lines += meds_lines
    if abx_lines:
        lines.append("\n## 항생제 요약")
        lines += abx_lines
    return "\n".join(lines)

def md_to_pdf_bytes_fontlocked(md_text):
    # 간단한 placeholder (실제 PDF 변환은 생략; ReportLab로 빈 PDF 제공)
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from io import BytesIO
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    text = c.beginText(40, 800)
    for line in md_text.splitlines()[:60]:
        text.textLine(line[:100])
    c.drawText(text)
    c.showPage(); c.save()
    return buf.getvalue()
