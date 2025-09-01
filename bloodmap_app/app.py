# -*- coding: utf-8 -*-
"""피수치 가이드 v3.14 - 경량 런처
- main() 필수 존재
- 모바일 UI에서 줄꼬임 방지
- 상대경로 import 정확
"""
from __future__ import annotations
import os
import streamlit as st

from .drug_data import ANTICANCER, ANTIBIOTICS, FEVER_RULES, FOOD_NEUTROPENIA
from .utils import safe_float, anc_risk_badge, fmt_number, kcal_reco

CSS_PATH = os.path.join(os.path.dirname(__file__), "style.css")

def _inject_css():
    try:
        with open(CSS_PATH, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass

def _sidebar():
    st.sidebar.title("⚙️ 옵션")
    st.sidebar.markdown("v3.14 · 안정화 테스트 빌드")
    st.sidebar.markdown("[피수치 가이드 공식카페](https://cafe.naver.com)")

def _input_section():
    st.subheader("🧪 기본 수치 입력")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        wbc = safe_float(st.text_input("WBC", value=""))
    with c2:
        hb = safe_float(st.text_input("Hb(혈색소)", value=""))
    with c3:
        plt = safe_float(st.text_input("혈소판(PLT)", value=""))
    with c4:
        anc = safe_float(st.text_input("ANC(호중구)", value=""))

    st.subheader("🧫 간/염증/신장")
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        ast = safe_float(st.text_input("AST", value=""))
    with c6:
        alt = safe_float(st.text_input("ALT", value=""))
    with c7:
        crp = safe_float(st.text_input("CRP", value=""))
    with c8:
        cr  = safe_float(st.text_input("Cr", value=""))

    return dict(wbc=wbc, hb=hb, plt=plt, anc=anc, ast=ast, alt=alt, crp=crp, cr=cr)

def _summary(vals: dict):
    st.markdown("### 📊 요약")
    badge_text, badge_cls = anc_risk_badge(vals.get("anc"))
    st.markdown(f"호중구 상태: <span class='{badge_cls}'>{badge_text}</span>", unsafe_allow_html=True)
    st.caption(f"WBC: {fmt_number(vals.get('wbc'))} · Hb: {fmt_number(vals.get('hb'))} · PLT: {fmt_number(vals.get('plt'))} · CRP: {fmt_number(vals.get('crp'))}")

def _drug_section():
    st.markdown("### 💊 약물 간단 보기")
    q = st.text_input("약물 검색(별칭 포함)", value="")
    def match(name, meta):
        ql = q.lower().strip()
        if not ql: return True
        return (ql in name.lower()) or (ql in meta.get("alias","").lower())
    with st.expander("항암제", expanded=True):
        for k, v in ANTICANCER.items():
            if match(k, v):
                st.markdown(f"- **{k}** — {v.get('notes','')}  
  _aka: {v.get('alias','')}_")
    with st.expander("항생제", expanded=False):
        for k, v in ANTIBIOTICS.items():
            if match(k, v):
                st.markdown(f"- **{k}** — {v.get('notes','')}  
  _aka: {v.get('alias','')}_")

def _guides(vals: dict):
    st.markdown("### 🍚 식이/생활 가이드")
    st.write("• ", kcal_reco(vals.get("hb")))  # 간단 예시
    badge_text, _ = anc_risk_badge(vals.get("anc"))
    if "감소" in badge_text:
        st.write("• 호중구감소 시 식이 주의사항:")
        for tip in FOOD_NEUTROPENIA:
            st.write("  - ", tip)
    st.write("### 🌡️ 발열 대응")
    for rule in FEVER_RULES:
        st.write("• ", rule)

def main():
    _inject_css()
    _sidebar()
    st.title("🩸 피수치 가이드 v3.14 (안정화 패키지)")
    vals = _input_section()
    st.divider()
    _summary(vals)
    st.divider()
    _drug_section()
    st.divider()
    _guides(vals)
    st.markdown("---")
    st.caption("制作者: Hoya/GPT · 자문: Hoya/GPT")