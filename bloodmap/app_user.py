# -*- coding: utf-8 -*-
def _try_targets():
    return [
        ("bloodmap_app.app", "main"),
        ("app", "main"),
        ("streamlit_app", "main"),
        ("bloodmap_app.main", "main"),
        ("main", "app"),
        ("main", "run"),
    ]

def _resolve_entry():
    last = None
    for mod, attr in _try_targets():
        try:
            m = __import__(mod, fromlist=[attr])
            fn = getattr(m, attr, None)
            if callable(fn): return fn
        except Exception as e:
            last = e
            continue
    raise RuntimeError(f"실행 가능한 엔트리포인트를 찾지 못했습니다: {last!r}")

def _run():
    try:
        fn = _resolve_entry()
        return fn()
    except Exception as e:
        try:
            import streamlit as st
            st.error(f"bloodmap.app_user 오류: {e}")
        except Exception:
            pass
        raise

def main(): return _run()
def app(): return _run()
def run(): return _run()
