import sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parent
# ⚙️ 안전: 현재 디렉토리를 Python 경로에 추가
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

def _load_main():
    # 1) 정식 패키지
    try:
        from bloodmap_app.app import main as _m
        return _m
    except Exception as e1:
        st.warning(f"bloodmap_app.app 로딩 재시도: {e1}")
        # 2) 레거시 shim
        try:
            from bloodmap.app_user import main as _m2
            # main/app/run 존재 확인
            import bloodmap.app_user as apu
            for attr in ("main","app","run"):
                if not hasattr(apu, attr):
                    raise AttributeError(f"bloodmap.app_user에 '{attr}' 없음")
            return _m2
        except Exception as e2:
            st.error(f"사용자 app 불러오기 오류: {e2}")
            raise

MAIN = _load_main()

if __name__ == "__main__":
    MAIN()
