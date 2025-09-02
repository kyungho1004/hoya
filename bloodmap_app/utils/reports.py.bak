
from ..config import (APP_TITLE, DISCLAIMER, ORDER)
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import io

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
    # 간단한 PDF 렌더러 (폰트 고정은 간소화)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    x = 20*mm
    y = height - 20*mm
    for line in md_text.split("\n"):
        if y < 20*mm:
            c.showPage()
            y = height - 20*mm
        c.drawString(x, y, line[:110])  # 줄 자르기
        y -= 6*mm
    c.save()
    return buf.getvalue()
