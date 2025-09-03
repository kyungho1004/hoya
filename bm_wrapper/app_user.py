# bm_wrapper/app_user.py
# 런처가 bm_wrapper.app_user.main / app / run 을 호출해도
# 내부의 bloodmap_app.app.main 으로 안전하게 연결해 주는 래퍼입니다.

def main():
    try:
        from bloodmap_app.app import main as _main
        return _main()
    except Exception as e:
        try:
            import streamlit as st  # type: ignore
            st.error(f"bloodmap_app.app.main 호출 중 오류: {e}")
        except Exception:
            pass
        raise

def app():
    return main()

def run():
    return main()
