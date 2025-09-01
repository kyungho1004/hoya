
# -*- coding: utf-8 -*-
try:
    import streamlit as st
except Exception:
    class _Dummy:  # smoke-test fallback
        def __getattr__(self, k):
            def _f(*a, **kw): return None
            return _f
    st = _Dummy()

def _parse_numeric(raw, decimals=1):
    try:
        v = float(str(raw).strip())
        if decimals == 0: return int(round(v))
        return float(f"{v:.{decimals}f}")
    except Exception:
        return None

def num_input_generic(label, key, decimals=1, placeholder="", as_int=False):
    raw = st.text_input(label, key=key, placeholder=placeholder)
    return _parse_numeric(raw, decimals=0 if as_int else decimals)

def entered(v):
    try: return v is not None and str(v) != "" and float(v) == float(v)
    except Exception: return v not in (None, "", [])
