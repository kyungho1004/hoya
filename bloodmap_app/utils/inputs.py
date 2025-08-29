
import streamlit as st
def _parse_numeric(text, default=0.0, as_int=False, decimals=None):
    if text is None: return default
    s=str(text).strip().replace(",","")
    if s=="": return default
    try:
        v=float(s)
        if as_int: return int(v)
        if decimals is not None: return float(f"{v:.{decimals}f}")
        return v
    except: return default
def num_input_generic(label, key, placeholder="", as_int=False, decimals=None):
    raw = st.text_input(label, key=key, placeholder=placeholder)
    return _parse_numeric(raw, as_int=as_int, decimals=decimals)
def entered(v):
    try: return v is not None and float(v)!=0
    except: return False
