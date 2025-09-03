BloodMap Deep Alias Fix
-----------------------
This pack creates compatibility aliases so environments that try to import:
  - `bloodmap`
  - `bloodmap.app_user`
and expect `main/app/run.py` under that namespace will still execute
`bloodmap_app.app.main()`.

What it adds:
- bloodmap/__init__.py                  → aliases to bloodmap_app
- bloodmap/app_user/__init__.py         → aliases to bloodmap_app
- bloodmap/app_user/main.py             → calls bloodmap_app.app.main()
- bloodmap/app_user/main/app/run.py     → calls bloodmap_app.app.main()
- (Optional) top-level main.py and main/app/run.py and streamlit_app.py

How to use:
- Drop these folders/files into your project ROOT (same level as bloodmap_app/).
- Keep your real code in bloodmap_app/ with app.py providing def main().
