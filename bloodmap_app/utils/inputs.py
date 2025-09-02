
import streamlit as st
def _parse_numeric(x):
    try:
        return float(x)
    except Exception:
        return None
def num_input_generic(label, key=None, unit=None, default=None, step=0.1):
    val = st.number_input(label if not unit else f"{label} ({unit})", key=key, value=float(default) if default is not None else 0.0, step=step)
    return _parse_numeric(val)
def entered(keys=None):
    keys = keys or []
    for k in keys:
        if k in st.session_state and st.session_state[k] not in (None, "", 0):
            return True
    return False
