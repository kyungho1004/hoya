
import os, json, time, streamlit as st

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "visits.jsonl")

def bump_counter():
    # in-session
    st.session_state.setdefault("visit_count", 0)
    st.session_state.visit_count += 1
    # to file (append jsonl)
    try:
        rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "ip":"-", "ua":"-", "count": st.session_state.visit_count}
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return st.session_state.visit_count
