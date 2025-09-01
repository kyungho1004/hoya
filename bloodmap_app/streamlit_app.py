import os, sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensure project folders are importable
for p in [BASE_DIR, os.path.join(BASE_DIR, "data"), os.path.join(BASE_DIR, "utils")]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Make 'data' and 'utils' packages if __init__.py is missing (Streamlit Cloud safe)
for pkg in ("data", "utils"):
    pkg_dir = os.path.join(BASE_DIR, pkg)
    if os.path.isdir(pkg_dir):
        init_file = os.path.join(pkg_dir, "__init__.py")
        if not os.path.exists(init_file):
            try:
                open(init_file, "a").close()
            except Exception:
                pass

# Delegate to main app
try:
    from app import main
except Exception as e1:
    # Fallback: some deployments keep code under a folder
    try:
        from bloodmap_app.app import main  # pragma: no cover
    except Exception as e2:
        import streamlit as st
        st.error("앱 엔트리포인트(main)를 찾지 못했습니다. (app.py 또는 bloodmap_app/app.py)")
        st.exception(e1)
        st.exception(e2)
        raise

if __name__ == "__main__":
    main()