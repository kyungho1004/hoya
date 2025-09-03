# BloodMap Entrypoints Fix Pack

This pack solves:
- `ModuleNotFoundError: No module named 'bloodmap'`
- Hosts that look for `main/app/run` or `main.py` automatically

## What it contains
- `streamlit_app.py` → run with `streamlit run streamlit_app.py`
- `main.py` → generic Python entrypoint
- `main/app/run.py` → compatibility path for certain PaaS/hosts
- `bloodmap_app/__init__.py` → ensures the package is importable

## How to use
1. Place this pack at your **project root** (same level as your `bloodmap_app/` folder).
2. Make sure your real UI is defined at `bloodmap_app/app.py` with a `main()` function.
3. Start locally:
   ```bash
   pip install -r requirements.txt
   streamlit run streamlit_app.py
   ```
4. If your host expects `main.py` or `main/app/run.py`, these files will call `bloodmap_app.app.main()` for you.

## Import path notes
- Keep all internal imports **package-relative**, e.g. in `bloodmap_app/app.py`:
  ```python
  from .config import ...
  from .utils.interpret import ...
  ```
  or absolute within the package:
  ```python
  from bloodmap_app.config import ...
  ```
- **Never** import `bloodmap.*` (old name) — that triggers `No module named 'bloodmap'`.

## Troubleshooting
- If you still see white screen on Streamlit Cloud, check app logs:
  - Syntax errors (e.g., unmatched parentheses)
  - Missing files (`config.py`, `data/*`, `utils/*`)
  - `reportlab` not installed for PDF export (optional)

## Footer policy banners (add in your UI footer)
- "⚠️ 문제가 생길 경우 데이터는 삭제될 수 있습니다."
- "🔒 개인정보는 절대 수집하지 않습니다."
