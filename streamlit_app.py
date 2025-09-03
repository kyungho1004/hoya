# -*- coding: utf-8 -*-
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:  # ★ 어떤 위치에서 실행해도 루트가 모듈경로에 들어가게 함
    sys.path.insert(0, str(ROOT))

import streamlit as st

def _load_main():
    # 1) 정식 경로
    try:
        from bloodmap_app.app import main as _m
        return _m
    except Exception as e1:
        st.warning(f"bloodmap_app.app 로딩 재시도: {e1}")
        # 2) 레거시 shim 경로
        from bloodmap.app_user import main as _m2
        import bloodmap.app_user as apu
        assert all(hasattr(apu, a) for a in ("main","app","run")), "bloodmap.app_user에 main/app/run 필요"
        return _m2

MAIN = _load_main()

if __name__ == "__main__":
    MAIN()
