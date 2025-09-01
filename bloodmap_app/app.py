def main():

    # ===== View counter (server-runtime unique sessions) =====
    from uuid import uuid4
    @st.cache_resource
    def _view_store():
        return {"total": 0, "seen": set()}
    if "_view_id" not in st.session_state:
        st.session_state["_view_id"] = str(uuid4())
    _vs = _view_store()
    if st.session_state["_view_id"] not in _vs["seen"]:
        _vs["seen"].add(st.session_state["_view_id"])
        _vs["total"] += 1

    with st.container(border=True):
        st.markdown("**👀 현재 서버 런타임 조회수:** " + str(_vs["total"]))
        st.caption("동일 세션은 1회만 카운트. 서버 재시작 시 초기화될 수 있습니다.")

    # ===== Cafe / Ad banner (placeholder) =====
    with st.container(border=True):
        st.markdown("### 📌 공식 카페 / 공지")
        st.markdown(CAFE_LINK_MD)
        st.caption("조회수 기반 배너 광고 영역(Placeholder) — 배너 코드 연결 시 이 영역에 노출됩니다.")

if __name__ == '__main__':
    main()
