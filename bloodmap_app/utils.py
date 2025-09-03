# -*- coding: utf-8 -*-
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import streamlit as st
from .config import FONT_PATH_REG, FONT_PATH_B, FONT_PATH_EB

def parse_float(raw, decimals=1):
    if raw is None or raw == "":
        return None
    try:
        v = float(str(raw).replace(',', '').strip())
        if decimals is None:
            return v
        fmt = f"{{:.{decimals}f}}"
        return float(fmt.format(v))
    except Exception:
        return None

def num_input(label, key=None, decimals=1, placeholder="", as_int=False):
    raw = st.text_input(label, key=key, placeholder=placeholder)
    v = parse_float(raw, decimals=0 if as_int else decimals)
    if as_int and v is not None:
        try:
            return int(v)
        except Exception:
            return None
    return v

def entered(v):
    try:
        return v is not None and str(v) != "" and float(v) != 0
    except Exception:
        return v is not None and str(v) != ""

def nickname_key(nick, pin):
    pin = (pin or "").strip()
    if len(pin) == 4 and pin.isdigit():
        return f"{nick.strip()}#{pin}"
    return nick.strip()

def md_to_pdf_bytes(md_text):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    y = H - 20*mm
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        pdfmetrics.registerFont(TTFont("NanumGothic", FONT_PATH_REG))
        try:
            pdfmetrics.registerFont(TTFont("NanumGothic-Bold", FONT_PATH_B))
            pdfmetrics.registerFont(TTFont("NanumGothic-ExtraBold", FONT_PATH_EB))
        except Exception:
            pass
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
    c.showPage(); c.save()
    return buf.getvalue()
