
import io
import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .counter import log_event, count_downloads
def build_report(text: str):
    text = text or "BloodMap Report"
    return f"# Report\n\n{text}\n"
def md_to_pdf_bytes_fontlocked(md_text: str):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    try:
        pdfmetrics.registerFont(TTFont("NanumGothic", "fonts/NanumGothic-Regular.ttf"))
        c.setFont("NanumGothic", 12)
    except Exception:
        c.setFont("Helvetica", 12)
    y = 800
    for line in (md_text or "").splitlines():
        c.drawString(40, y, line[:110])
        y -= 16
        if y < 50:
            c.showPage(); y = 800
    c.save()
    buf.seek(0)
    return buf.read()
# helper wrappers to count downloads in app-side if used here
def download_buttons(md):
    st.write("보고서 다운로드")
    if st.download_button("MD 다운로드", md.encode("utf-8"), file_name="report.md"):
        log_event("download","md")
    if st.download_button("TXT 다운로드", md.encode("utf-8"), file_name="report.txt"):
        log_event("download","txt")
    pdf_bytes = md_to_pdf_bytes_fontlocked(md)
    if st.download_button("PDF 다운로드", pdf_bytes, file_name="report.pdf"):
        log_event("download","pdf")
    st.caption(f"📥 총 다운로드: {count_downloads()} (MD:{count_downloads('md')}, TXT:{count_downloads('txt')}, PDF:{count_downloads('pdf')})")
