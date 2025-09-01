# -*- coding: utf-8 -*-
# Utility adapter for app.py expectations
from .inputs import num_input_generic, entered, _parse_numeric
from .interpret import food_suggestions as food_recommendations, interpret_labs, compare_with_previous
from .graphs import render_graphs
from .schedule import render_schedule

def number_or_none(value, decimals=None):
    try:
        v = _parse_numeric(value, default=None, decimals=decimals)
    except Exception:
        v = None
    return v

def only_entered_values(d: dict) -> dict:
    out = {}
    for k, v in (d or {}).items():
        try:
            if entered(v):
                out[k] = v
        except Exception:
            if v not in (None, "", [], {}):
                out[k] = v
    return out

def apply_css(path: str = "style.css"):
    try:
        import os, streamlit as st
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass
