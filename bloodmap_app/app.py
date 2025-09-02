# -*- coding: utf-8 -*-
import streamlit as st

# ---- Inline helpers (no external imports) ----
def _to_float(x):
    try:
        if x is None or str(x).strip() == "":
            return None
        return float(str(x).strip().replace(",", ""))
    except Exception:
        return None

def interpret_labs(vals, extras):
    lines = []
    anc = _to_float(vals.get("ANC"))
    if anc is not None:
        if anc < 500:
            lines.append("🚨 ANC 500 미만: 즉시 병원 상담/격리 식사 권장")
        elif anc < 1000:
            lines.append("⚠️ ANC 1000 미만: 익힌 음식·위생 철저")
        else:
            lines.append("✅ ANC 양호")
    crp = _to_float(vals.get("CRP"))
    if crp is not None and crp >= 0.5:
        lines.append("🔥 CRP 상승: 증상 모니터링 및 필요 시 진료")
    if not lines:
        lines.append("🙂 입력된 값 기준 특이 위험 신호 없음")
    return lines

def compare_with_previous(nickname, current_vals):
    if not nickname: return []
    out = []
    for k, v in current_vals.items():
        if v is not None and str(v).strip() != "":
            out.append(f"- {k}: {v}")
    return out

def food_suggestions(vals, anc_place):
    out = []
    anc = _to_float(vals.get("ANC"))
    if anc is not None and anc < 1000:
        out.append("익힌 음식 위주, 상온 보관 음식 피하기")
        if anc_place == "병원":
            out.append("병원식 권장 범위 내에서 선택")
    return out

# ---- Streamlit UI ----
def main():
    st.set_page_config(page_title="피수치 가이드 (초안정본)", layout="centered")
    st.title("🩸 피수치 가이드 (초안정본)")
    st.caption("외부 모듈 import를 모두 제거해 경로 문제 없이 동작합니다.")

    st.header("1) 기본 입력")
    nickname = st.text_input("별명(옵션)")
    anc_place = st.radio("현재 식사 장소", ["가정", "병원"], horizontal=True)

    st.header("2) 검사 수치")
    vals = {}
    c1, c2 = st.columns(2)
    with c1:
        vals["ANC"] = st.text_input("ANC", placeholder="예: 1200")
        vals["Hb"]  = st.text_input("Hb", placeholder="예: 12.5")
        vals["PLT"] = st.text_input("혈소판", placeholder="예: 150")
    with c2:
        vals["CRP"] = st.text_input("CRP", placeholder="예: 0.2")
        vals["Na"]  = st.text_input("Na", placeholder="예: 140")
        vals["K"]   = st.text_input("K",  placeholder="예: 4.1")

    st.divider()
    if st.button("🔎 해석하기", use_container_width=True):
        st.subheader("📋 해석 결과")
        for line in interpret_labs(vals, {}):
            st.write(line)

        st.markdown("### 🥗 음식 가이드")
        fs = food_suggestions(vals, anc_place)
        for f in (fs or ["입력값 기준 추가 권장 없음"]):
            st.write("- " + f)

        if nickname:
            st.markdown("### 비교(데모)")
            for l in compare_with_previous(nickname, vals):
                st.write(l)

    st.markdown("---")
    st.caption("경로 문제 해결용 초안정본. 기능 확장은 이후 단계에서 모듈만 추가하면 됩니다.")

if __name__ == "__main__":
    main()
