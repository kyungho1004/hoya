import streamlit as st

def num_input_generic(label, key=None, decimals=1, placeholder="", as_int=False):
    raw = st.text_input(label, key=key, placeholder=placeholder)
    if raw is None or str(raw).strip() == "":
        return None
    try:
        if as_int:
            return int(float(raw))
        return round(float(raw), decimals)
    except Exception:
        return None

def entered(val):
    return val is not None and str(val).strip() != ""

def _parse_numeric(raw, decimals=1):
    try:
        return round(float(raw), decimals)
    except Exception:
        return None
