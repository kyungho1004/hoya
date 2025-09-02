from bloodmap_app.app import main

if __name__=='__main__':
    try:
        main()
    except Exception as e:
        import streamlit as st
        st.write(e)
