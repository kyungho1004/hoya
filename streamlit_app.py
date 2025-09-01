
# -*- coding: utf-8 -*-
import streamlit as st
from bloodmap_app.app import main

st.set_page_config(page_title="피수치 가이드 (v3.14-fixed)", page_icon="🩸", layout="centered")

if __name__ == "__main__":
    main()
