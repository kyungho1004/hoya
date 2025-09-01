# BloodMap App (fixed package)

## Run
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

- Launcher imports `bloodmap_app.app` (no main() call).
- Imports inside package use relative form (e.g., `from .utils ...`).
- Optional: place font files in `./fonts` for PDF.
