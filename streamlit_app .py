# streamlit_app.py — adapter for Streamlit Cloud
# Your repo's "Main file path" can be set to this file.
# It just imports the real app (app.py in the repo root).

# Option A: app has a main() function
try:
    from app import main as _main  # type: ignore
except Exception:
    _main = None

# Option B: app renders at import-time (top-level st.* calls)
import app  # noqa: F401

if callable(_main):
    _main()
