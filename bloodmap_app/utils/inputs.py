
import streamlit as st

def _parse_numeric(raw, decimals=1):
    if raw is None or str(raw).strip() == "":
        return None
    s = str(raw).replace(",", "").strip()
    try:
        if decimals == 0:
            return int(float(s))
        return round(float(s), decimals)
    except Exception:
        return None

def num_input_generic(label, key=None, decimals=1, placeholder="", as_int=False):
    raw = st.text_input(label, key=key, placeholder=placeholder)
    val = _parse_numeric(raw, decimals=0 if as_int else decimals)
    return val

def entered(x):
    try:
        return x is not None and str(x) != "" and float(x) == float(x)
    except Exception:
        return False
