
# -*- coding: utf-8 -*-
"""
Entry point for Streamlit.
Fixed imports to match the structure:
project_root/
├── streamlit_app.py
├── config.py
├── requirements.txt
└── bloodmap_app/
    ├── __init__.py
    ├── app.py
    ├── data/
    │   └── drugs.py
    ├── utils/
    │   └── __init__.py
    └── style.css
"""
from bloodmap_app.app import main

if __name__ == "__main__":
    # Allow running as a normal python file for quick smoke tests
    main()
