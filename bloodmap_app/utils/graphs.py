
import streamlit as st
import pandas as pd
def render_graphs(data=None):
    st.subheader("📈 그래프")
    if not data:
        df = pd.DataFrame({'월':[1,2,3,4], 'Hb':[8.5,9.2,9.8,10.1], 'ANC':[0.4,0.9,1.2,1.6]})
    else:
        df = data
    st.line_chart(df.set_index('월') if '월' in df.columns else df)
