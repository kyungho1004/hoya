
import os, json, time, streamlit as st
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
LOG_PATH = os.path.join(LOG_DIR, "events.jsonl")
os.makedirs(LOG_DIR, exist_ok=True)
def _append(rec: dict):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
def bump():
    if not st.session_state.get("_view_bumped"):
        _append({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "type": "view"})
        st.session_state["_view_bumped"] = True
def count():
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            return sum(1 for line in f if '"type": "view"' in line)
    except FileNotFoundError:
        return 0
def log_event(kind: str, detail: str = ""):
    _append({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "type": kind, "detail": detail})
def count_downloads(detail: str = None):
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            if detail is None:
                return sum(1 for line in f if '"type": "download"' in line)
            c = 0
            for line in f:
                if '"type": "download"' in line and f'"detail": "{detail}"' in line:
                    c += 1
            return c
    except FileNotFoundError:
        return 0
