# bloodmap_app/app.py — fixed version (share block inside main, guard added)
def main():
    import os, sys
    from datetime import datetime, date
    import streamlit as st

    try:
        from .config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE,
                            DISCLAIMER, ORDER, FEVER_GUIDE,
                            LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
                            LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP,
                            FONT_PATH_REG)
        from .utils import counter as _bm_counter
    except Exception:
        from config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE,
                            DISCLAIMER, ORDER, FEVER_GUIDE,
                            LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
                            LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP,
                            FONT_PATH_REG)
        import utils.counter as _bm_counter

    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    st.title(APP_TITLE)
    st.markdown(MADE_BY)
    st.markdown(CAFE_LINK_MD)

    # ✅ 공유하기 블록 main() 안으로 이동
    st.markdown("### 🔗 공유하기")
    c1, c2, c3 = st.columns([1,1,2])
    with c1:
        st.link_button("📱 카카오톡/메신저", "https://hdzwo5ginueir7hknzzfg4.streamlit.app/")
    with c2:
        st.link_button("📝 카페/블로그", "https://cafe.naver.com/bloodmap")
    with c3:
        st.code("https://hdzwo5ginueir7hknzzfg4.streamlit.app/", language="text")
    st.caption("✅ 모바일 줄꼬임 방지 · 별명 저장/그래프 · 암별/소아/희귀암 패널 · PDF 한글 폰트 고정 · 수치 변화 비교 · 항암 스케줄표 · 계절 식재료/레시피 · ANC 병원/가정 구분")

    os.makedirs("fonts", exist_ok=True)
    try:
        _bm_counter.bump()
        st.caption(f"👀 조회수(방문): {_bm_counter.count()}")
    except Exception:
        pass

    # ... 이하 기존 main() 코드 계속 ...

if __name__ == "__main__":
    main()
