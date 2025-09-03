\
from io import BytesIO

def build_report(mode, meta, vals, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines):
    lines = []
    lines.append(f"# 피수치 가이드 보고서")
    lines.append(f"- 모드: {mode}")
    if meta:
        for k, v in meta.items():
            if v: lines.append(f"- {k}: {v}")
    lines.append("\n## 기본 수치")
    for k, v in (vals or {}).items():
        if v is not None:
            lines.append(f"- {k}: {v}")
    if cmp_lines:
        lines.append("\n## 수치 변화 비교")
        lines += [f"- {x}" for x in cmp_lines]
    if extra_vals:
        lines.append("\n## 암별 디테일 수치")
        for k, v in extra_vals.items():
            if v is not None:
                lines.append(f"- {k}: {v}")
    if meds_lines:
        lines.append("\n## 항암제 요약")
        lines += meds_lines
    if abx_lines:
        lines.append("\n## 항생제 요약")
        lines += abx_lines
    if food_lines:
        lines.append("\n## 음식 가이드")
        lines += food_lines
    return "\n".join(lines)

def md_to_pdf_bytes_fontlocked(md_text):
    # 최소 구현: reportlab 사용 불가 시 텍스트 PDF 유사 바이트 반환
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfbase import pdfmetrics
        import os
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        try:
            if os.path.exists("fonts/NanumGothic.ttf"):
                pdfmetrics.registerFont(TTFont("NanumGothic", "fonts/NanumGothic.ttf"))
                font_name = "NanumGothic"
            else:
                font_name = "Helvetica"
        except Exception:
            font_name = "Helvetica"
        c.setFont(font_name, 10)
        x, y = 40, 800
        for line in md_text.splitlines():
            c.drawString(x, y, line[:120])
            y -= 14
            if y < 40:
                c.showPage()
                c.setFont(font_name, 10)
                y = 800
        c.save()
        buf.seek(0)
        return buf.read()
    except Exception:
        return md_text.encode("utf-8")
