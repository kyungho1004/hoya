# -*- coding: utf-8 -*-
import streamlit as st
from .config import APP_TITLE, PAGE_TITLE

def main():
    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    st.title(APP_TITLE)
    st.success("bloodmap_app.app.main() OK")
