
"""
report_exporter.py
------------------
Reusable helpers to export reports as Markdown (.md), Plain Text (.txt), and PDF (.pdf).
Designed for Streamlit apps and mobile-safe download buttons.

Dependencies:
- reportlab>=3.6 (for PDF)
- streamlit (optional, only if you use `render_download_buttons`)

PDF font note (Korean):
- To ensure Hangul renders correctly in PDFs, include a TTF/OTF font file in your repo,
  e.g., "./fonts/NanumGothic.ttf" or "./fonts/NotoSansKR-Regular.otf".
- The exporter tries these automatically. If none are found, it falls back to Helvetica,
  which may NOT render Korean text. To force a font, pass `font_paths=[...]`.
"""

from __future__ import annotations
from io import BytesIO
from typing import List, Optional
import os
import re

# ---- Optional Streamlit import (guarded) ----
try:
    import streamlit as st
except Exception:
    st = None  # allows using this module outside Streamlit

# ---- ReportLab imports ----
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# --------- Core helpers ---------

def markdown_to_text(md: str) -> str:
    """
    Very small markdown-to-text converter: strips common markdown syntax
    and keeps bullets and headings in a readable plain-text format.
    """
    if md is None:
        return ""
    text = md

    # Preserve line breaks first
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Headings: "# Title" -> "Title\n" (keep on its own line)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

    # Bold/Italic/Code markers -> just remove the markers
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)     # **bold** / __bold__
    text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)        # *italic* / _italic_
    text = re.sub(r"`([^`]+)`", r"\1", text)            # `code`

    # Links: [text](url) -> text (url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)

    # Images: ![alt](url) -> [Image: alt] (url)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r"[Image: \1] (\2)", text)

    # Remove leftover HTML tags (very naive)
    text = re.sub(r"<[^>]+>", "", text)

    # Dedent/collapse triple spaces
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def _register_korean_font(font_paths: Optional[List[str]] = None) -> str:
    """
    Try to register a Korean-capable TTF/OTF. Returns the font name to use.
    If none is found, returns 'Helvetica' (WARNING: may not render Hangul).
    """
    candidates = font_paths or []
    # Default common paths you can bundle in your repo
    candidates += [
        "fonts/NanumGothic.ttf",
        "fonts/NanumGothicCoding.ttf",
        "fonts/NotoSansKR-Regular.otf",
        "fonts/NotoSansKR-Regular.ttf",
        "NanumGothic.ttf",
        "NotoSansKR-Regular.otf",
        "NotoSansKR-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("KoreanPrimary", path))
                return "KoreanPrimary"
            except Exception:
                continue
    # Fallback
    return "Helvetica"


def markdown_to_pdf_bytes(md: str, *, font_paths: Optional[List[str]] = None, title: str = "Report") -> bytes:
    """
    Convert a markdown string into a simple, readable PDF.
    Parsing is intentionally lightweight for robustness on Streamlit Cloud.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15*mm,
        rightMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
        title=title,
    )

    font_name = _register_korean_font(font_paths)

    styles = getSampleStyleSheet()
    # Override font for existing styles
    for k in ("Normal", "Title", "Heading1", "Heading2", "Heading3"):
        if k in styles:
            styles[k].fontName = font_name

    # Create a compact body style for regular paragraphs
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=10.5,
        leading=14,
        spaceAfter=4,
    )
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, leading=20, spaceAfter=8)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14, leading=18, spaceAfter=6)
    h3 = ParagraphStyle("H3", parent=styles["Heading3"], fontSize=12, leading=16, spaceAfter=6)

    story = []

    # Naive markdown parser (headings, bullets, paragraphs)
    lines = md.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    bullet_block = []

    def flush_bullets():
        nonlocal bullet_block
        if bullet_block:
            items = [ListItem(Paragraph(re.sub(r"^\s*[-*]\s*", "", li).strip(), body_style)) for li in bullet_block]
            story.append(ListFlowable(items, bulletType="bullet", start="•", leftIndent=10, spaceAfter=6))
            bullet_block = []

    for raw in lines:
        line = raw.rstrip()

        # Blank line -> paragraph break
        if not line.strip():
            flush_bullets()
            story.append(Spacer(1, 6))
            continue

        # Headings
        if line.startswith("### "):
            flush_bullets()
            story.append(Paragraph(line[4:].strip(), h3))
            continue
        if line.startswith("## "):
            flush_bullets()
            story.append(Paragraph(line[3:].strip(), h2))
            continue
        if line.startswith("# "):
            flush_bullets()
            story.append(Paragraph(line[2:].strip(), h1))
            continue

        # Bullets
        if re.match(r"^\s*[-*]\s+", line):
            bullet_block.append(line)
            continue

        # Fallback -> paragraph
        flush_bullets()
        # Minimal inline conversions for bold/italic/code
        line_html = (
            line
            .replace("**", "<b>").replace("__", "<b>")  # quick bold (naive)
            .replace("*", "").replace("_", "")          # drop italics markers
            .replace("`", "")                           # drop inline code markers
        )
        story.append(Paragraph(line_html, body_style))

    flush_bullets()

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


# --------- Streamlit UI helper ---------

def render_download_buttons(report_md: str, base_filename: str = "report", *, font_paths: Optional[List[str]] = None, title: str = "Report"):
    """
    Render three download buttons (MD, TXT, PDF) in a vertical layout.
    Mobile-safe: uses use_container_width=True.
    """
    if st is None:
        raise RuntimeError("Streamlit not available. Install streamlit to use render_download_buttons.")

    if not report_md or not isinstance(report_md, str):
        st.info("생성된 보고서가 없습니다. 먼저 해석 결과를 만들어주세요.")
        return

    md_bytes = report_md.encode("utf-8")
    txt_bytes = markdown_to_text(report_md).encode("utf-8")
    pdf_bytes = markdown_to_pdf_bytes(report_md, font_paths=font_paths, title=title)

    st.download_button("📝 보고서(.md) 다운로드", data=md_bytes, file_name=f"{base_filename}.md", mime="text/markdown", use_container_width=True)
    st.download_button("📄 보고서(.txt) 다운로드", data=txt_bytes, file_name=f"{base_filename}.txt", mime="text/plain", use_container_width=True)
    st.download_button("🧾 보고서(.pdf) 다운로드", data=pdf_bytes, file_name=f"{base_filename}.pdf", mime="application/pdf", use_container_width=True)


# --------- Non-Streamlit convenience ---------

def make_all_bytes(report_md: str, *, font_paths: Optional[List[str]] = None, title: str = "Report"):
    """
    Return a tuple of (md_bytes, txt_bytes, pdf_bytes) for saving or testing.
    """
    md_bytes = report_md.encode("utf-8")
    txt_bytes = markdown_to_text(report_md).encode("utf-8")
    pdf_bytes = markdown_to_pdf_bytes(report_md, font_paths=font_paths, title=title)
    return md_bytes, txt_bytes, pdf_bytes
