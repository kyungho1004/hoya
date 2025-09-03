import streamlit as st
try:
    from bloodmap_app.app import main
except Exception as e:
    st.error(f"사용자 app 불러오기 오류: {e}")
    raise

if __name__ == "__main__":
    main()
