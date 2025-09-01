
import streamlit as st

def _parse_numeric(raw, decimals=1):
    if raw in (None, ""): return None
    try:
        v = float(str(raw).replace(',', ''))
        if decimals is None:
            return v
        fmt = (f"{{:.{decimals}f}}").format(v)
        return float(fmt) if '.' in fmt else int(v)
    except Exception:
        return None

def num_input_generic(label, key=None, decimals=1, placeholder="", as_int=False):
    raw = st.text_input(label, key=key, placeholder=placeholder)
    v = _parse_numeric(raw, decimals=0 if as_int else decimals)
    return v

def entered(v):
    try:
        return v is not None and float(v) != 0
    except Exception:
        return v not in (None, "", 0)
