
# Re-export helpers from flat utils.py if available; else provide fallbacks
try:
    from ..utils import num_input_generic, entered, _parse_numeric
except Exception:
    import streamlit as st
    def _parse_numeric(raw, decimals=1):
        try:
            v = float(str(raw).strip())
            return round(v, decimals)
        except Exception:
            return None
    def entered(v): 
        try: return v is not None and str(v) != "" and float(v) != 0
        except: return False
    def num_input_generic(label, key=None, decimals=1, placeholder=""):
        raw = st.text_input(label, key=key, placeholder=placeholder)
        return _parse_numeric(raw, decimals=decimals)
