# -*- coding: utf-8 -*-
# Streamlit robust launcher.
# - Tries both 'bloodmap' and 'bloodmap_app' package names
# - Ensures the repo root is on sys.path
# - Falls back to local 'app.py' if packages are missing

import os, sys, importlib

HERE = os.path.abspath(os.path.dirname(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# Also add commonly-used subdirs (in case Cloud places code under src/ or app/)
for sub in ("src", "app", "code"):
    p = os.path.join(HERE, sub)
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

errors = []
for pkg in ("bloodmap", "bloodmap_app"):
    try:
        mod = importlib.import_module(f"{pkg}.app")
        if hasattr(mod, "main") and callable(mod.main):
            mod.main()
            raise SystemExit(0)
    except Exception as e:
        errors.append(f"{pkg}: {e!r}")

# Fallback: try local 'app.py' at repo root
try:
    import app as _local_app
    if hasattr(_local_app, "main") and callable(_local_app.main):
        _local_app.main()
        raise SystemExit(0)
except Exception as e:
    errors.append(f"local app.py: {e!r}")

# If we got here, nothing worked
err_msg = "Streamlit launcher could not locate your app. Tried:\n" + "\n".join(f"- {m}" for m in errors) + \
          "\n\nExpected structure (one of):\n" \
          "  project_root/streamlit_app.py + project_root/bloodmap/app.py\n" \
          "  project_root/streamlit_app.py + project_root/bloodmap_app/app.py\n" \
          "  project_root/streamlit_app.py + project_root/app.py"
raise ImportError(err_msg)
