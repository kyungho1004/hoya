def main():

        with st.container(border=True):
        st.markdown("### 📌 공식 카페 / 공지")
        st.markdown(CAFE_LINK_MD)
        st.caption("조회수 기반 배너 광고 영역(Placeholder) — 배너 코드 연결 시 이 영역에 노출됩니다.")

# ===== View counter (session_state-based, no decorator) =====
if "_view_counter" not in st.session_state:
    st.session_state["_view_counter"] = 0
st.session_state["_view_counter"] += 1

with st.container(border=True):
    st.markdown("**👀 현재 페이지 조회수(세션 기준):** " + str(st.session_state["_view_counter"]))
    st.caption("세션 갱신 시 증가. 서버 재시작 시 초기화될 수 있습니다.")

# ===== Cafe / Ad banner (placeholder) =====
with st.container(border=True):
    st.markdown("### 📌 공식 카페 / 공지")
    from bloodmap_app.config import CAFE_LINK_MD
    st.markdown(CAFE_LINK_MD)
    st.caption("조회수 기반 배너 광고 영역(Placeholder) — 배너 코드 연결 시 이 영역에 노출됩니다.")

if __name__ == '__main__':
    main()
