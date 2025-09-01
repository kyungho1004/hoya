
# -*- coding: utf-8 -*-
\"\"\"Streamlit 메인 앱 (v3.14 패키징 확인판).

요구사항:
- 반드시 main() 함수를 제공
- 모바일 줄꼬임 방지 / 경로 안전 / 즉시 실행 가능

실제 기능(그래프, 보고서 등)은 기존 프로젝트 코드에 맞춰 확장하면 됩니다.
본 패키지는 '런처/패키징 검증'에 초점을 맞춘 최소구성입니다.
\"\"\"
from __future__ import annotations
import os
import sys

try:
    import streamlit as st
except Exception as e:  # pragma: no cover
    # Streamlit 미설치 환경에서도 임포트 오류로 파일 생성을 막지 않기 위한 보호.
    raise

from . import utils
from . import drug_data

def _inject_css() -> None:
    css_path = os.path.join(os.path.dirname(__file__), "style.css")
    css = utils.load_css(css_path)
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="피수치 가이드 v3.14", layout="centered")
    _inject_css()

    st.title("🩸 피수치 가이드 v3.14 · 패키징/경로 검증판")
    st.caption("이 화면이 보이면 폴더 구조와 import 경로가 정상입니다. (모바일 줄꼬임 방지 적용)")

    with st.expander("✅ 환경 점검"):
        st.write("- `bloodmap_app.app:main()` 진입 성공")
        st.write("- `bloodmap_app.utils`, `bloodmap_app.drug_data` import 성공")
        st.write("- 스타일 시트 로드 시도 완료")

    st.subheader("간단 입력(샘플)")
    col1, col2 = st.columns(2)
    with col1:
        wbc = st.number_input("WBC(백혈구)", min_value=0.0, step=0.1, format="%.1f")
        hb = st.number_input("Hb(혈색소)", min_value=0.0, step=0.1, format="%.1f")
    with col2:
        plt = st.number_input("PLT(혈소판)", min_value=0.0, step=1.0, format="%.0f")
        anc = st.number_input("ANC(호중구)", min_value=0.0, step=10.0, format="%.0f")

    if st.button("샘플 해석"):
        result = {
            "WBC": wbc,
            "Hb": hb,
            "PLT": plt,
            "ANC": anc,
        }
        st.markdown(utils.make_kv_table(result), unsafe_allow_html=True)

    st.divider()
    st.subheader("약물 데이터(샘플)")
    st.write("항암제 키 목록:", list(drug_data.ANTICANCER.keys()))
    st.write("항생제 키 목록:", list(drug_data.ANTIBIOTICS.keys()))

    st.info("⚠️ 본 패키지는 실행 검증용 최소 구성입니다. 기존 v3.14 기능(조회수, 카테고리, 보고서 등)은 기존 코드 통합 시 붙여넣어 확장하세요.")

if __name__ == "__main__":  # pragma: no cover
    main()
