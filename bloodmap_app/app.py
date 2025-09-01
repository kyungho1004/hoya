import streamlit as st
from bloodmap_app.config import ORDER, EXPLAIN, ALIAS

def main():
    st.title("피수치 가이드 실행 중")
    st.write("ORDER:", ORDER)
    st.write("EXPLAIN:", EXPLAIN)
    st.write("ALIAS:", ALIAS)