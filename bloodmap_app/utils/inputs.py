import streamlit as st

def _parse_numeric(s, decimals=1):
    if s is None or s=='':
        return None
    try:
        v=float(str(s).strip())
        return round(v, decimals) if decimals is not None else v
    except Exception:
        return None

def num_input_generic(label, key=None, decimals=1, placeholder="", as_int=False):
    raw = st.text_input(label, key=key, placeholder=placeholder)
    v = _parse_numeric(raw, decimals=0 if as_int else decimals)
    if as_int and v is not None:
        try: return int(v)
        except: return None
    return v

def entered(v):
    try:
        return v is not None and str(v)!='' and float(v)!=0
    except Exception:
        return False
