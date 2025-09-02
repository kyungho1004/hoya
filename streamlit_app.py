# -*- coding: utf-8 -*-
import sys, os
# Ensure project root is first. This prevents picking up any globally installed bloodmap_app.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from bloodmap_app.app import main

if __name__ == "__main__":
    main()
