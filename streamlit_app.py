# -*- coding: utf-8 -*-
# Force-load local bloodmap_app/app.py by file path to avoid conflicts with
# any installed package/module named `bloodmap_app` on the system.
import os, sys, types
from importlib.machinery import SourceFileLoader

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_FILE = os.path.join(BASE_DIR, "bloodmap_app", "app.py")

# Ensure local dir is first on sys.path (good practice)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Dynamically load the local app.py under a unique module name
modname = "bloodmap_app_local_app"
loader = SourceFileLoader(modname, APP_FILE)
app = types.ModuleType(modname)
loader.exec_module(app)

# Run
if __name__ == "__main__":
    app.main()
