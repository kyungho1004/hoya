from datetime import datetime
import os
from io import BytesIO

from config import (ORDER, LBL_CRP, DISCLAIMER, FONT_PATH_REG, FONT_PATH_B, FONT_PATH_XB)

def build_report(mode, meta, vals, compare_lines, extra_vals, meds_lines, food_lines, abx_lines):
    buf = [f"# BloodMap 보고서 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n",
           f"- 제작자/자문: Hoya / GPT\n",
           "[피수치 가이드 공식카페](https://cafe.naver.com/bloodmap)\n"]

    if mode == "일반/암":
        buf.append(f"- 암 그룹/종류: {meta.get('group') or '미선택/일반'} / {meta.get('cancer') or '—'}\n")
    elif mode == "소아(일상/호흡기)":
        buf.append(f"- 소아 주제: {meta.get('ped_topic')}\n")
        buf.append("\n## 소아 공통 입력\n")
        for k, v in meta.get('ped_inputs', {}).items():
            buf.append(f"- {k}: {v}\n")
    else:
        buf.append(f"- 소아 감염질환: {meta.get('infect_sel')}\n")
        for k, v in meta.get('infect_info', {}).items():
            buf.append(f"  - {k}: {v}\n")

    if mode == "일반/암":
        buf.append("\n## 입력 수치(기본)\n")
        for k in ORDER:
            v = vals.get(k)
            if v is None: 
                continue
            try:
                fv = float(v)
            except Exception:
                continue
            if k == LBL_CRP:
                buf.append(f"- {k}: {fv:.2f}\n")
            else:
                if fv.is_integer():
                    buf.append(f"- {k}: {int(fv)}\n")
                else:
                    buf.append(f"- {k}: {fv:.1f}\n")

        if compare_lines:
            buf.append("\n## 수치 변화 비교(이전 대비)\n")
            for l in compare_lines:
                buf.append(l + "\n")

        if extra_vals:
            buf.append("\n## 암별 디테일 수치\n")
            for k, v in extra_vals.items():
                if v is not None:
                    buf.append(f"- {k}: {v}\n")

        if meds_lines:
            buf.append("\n## 항암제 요약\n")
            for l in meds_lines:
                buf.append(l + "\n")

        if food_lines:
            buf.append("\n## 음식 가이드(계절/레시피 포함)\n")
            for l in food_lines:
                buf.append(l + "\n")

    if abx_lines:
        buf.append("\n## 항생제\n")
        for l in abx_lines:
            buf.append(l + "\n")

    buf.append(f"\n- ANC 장소: {meta.get('anc_place','—')}\n")
    buf.append("\n> " + DISCLAIMER + "\n")
    return "".join(buf)


def md_to_pdf_bytes_fontlocked(md_text: str) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.units import mm
        from xml.sax.saxutils import escape
    except Exception as e:
        raise RuntimeError("reportlab 미설치로 PDF 생성 불가: pip install reportlab") from e

    if not os.path.exists(FONT_PATH_REG):
        raise FileNotFoundError(f"{FONT_PATH_REG} 가 없습니다. 폰트를 넣어주세요.")

    font_name = "NanumGothic"
    pdfmetrics.registerFont(TTFont(font_name, FONT_PATH_REG))
    bold_name = None
    if os.path.exists(FONT_PATH_XB):
        try:
            pdfmetrics.registerFont(TTFont("NanumGothic-ExtraBold", FONT_PATH_XB))
            bold_name = "NanumGothic-ExtraBold"
        except Exception:
            pass
    if not bold_name and os.path.exists(FONT_PATH_B):
        try:
            pdfmetrics.registerFont(TTFont("NanumGothic-Bold", FONT_PATH_B))
            bold_name = "NanumGothic-Bold"
        except Exception:
            pass

    buf_pdf = BytesIO()
    doc = SimpleDocTemplate(buf_pdf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    # force fonts
    for s in ['Title','Heading1','Heading2','BodyText']:
        if s in styles.byName:
            styles[s].fontName = bold_name or font_name if s != 'BodyText' else font_name

    story = []
    for line in md_text.splitlines():
        line = line.rstrip("\n")
        if not line.strip():
            story.append(Spacer(1, 4*mm))
            continue
        if line.startswith("# "):
            p = Paragraph(f"<b>{escape(line[2:])}</b>", styles['Title'])
        elif line.startswith("## "):
            p = Paragraph(f"<b>{escape(line[3:])}</b>", styles['Heading2'])
        elif line.startswith("- "):
            p = Paragraph("• " + escape(line[2:]), styles['BodyText'])
        elif line.startswith("> "):
            p = Paragraph(f"<i>{escape(line[2:])}</i>", styles['BodyText'])
        else:
            p = Paragraph(escape(line), styles['BodyText'])
        story.append(p)

    doc.build(story)
    return buf_pdf.getvalue()
