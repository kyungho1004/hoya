# -*- coding: utf-8 -*-
import streamlit as st
from pathlib import Path
from .utils.helpers import validate_pin, Labs, as_md_report
from .utils.food import FOOD_GUIDE, ANC_FOOD_RULE
from . import drug_data

def _css():
    css_path = Path(__file__).with_name("style.css")
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

def _hit_counter():
    st.session_state['hits'] = st.session_state.get('hits', 0) + 1
    st.caption(f"조회수(세션): {st.session_state['hits']}")

def _sidebar():
    with st.sidebar:
        st.header("세션")
        nick = st.text_input("별명", placeholder="예: Hoya")
        pin = st.text_input("PIN (4자리)", type="password", max_chars=4, placeholder="0000")
        if pin and not validate_pin(pin):
            st.error("PIN은 숫자 4자리여야 합니다.")
        mode = st.selectbox("모드", ["일반 해석","항암치료","소아 패드"])
        show_special = st.toggle("특수검사 토글 (C3/C4, 소변 등)", value=False)
        st.divider()
        st.caption("문제 발생 시 삭제 조치합니다. 개인정보는 수집하지 않습니다.")
    return nick, pin, mode, show_special

def _inputs_basic():
    st.subheader("기본 피수치 입력")
    c1,c2,c3,c4 = st.columns(4)
    with c1: WBC = st.number_input("WBC", min_value=0.0, step=0.1, format="%.1f")
    with c2: Hb  = st.number_input("Hb", min_value=0.0, step=0.1, format="%.1f")
    with c3: PLT = st.number_input("혈소판(PLT)", min_value=0.0, step=1.0, format="%.0f")
    with c4: ANC = st.number_input("ANC(호중구)", min_value=0.0, step=10.0, format="%.0f")

    c5,c6,c7,c8 = st.columns(4)
    with c5: Ca = st.number_input("Ca", min_value=0.0, step=0.1)
    with c6: Na = st.number_input("Na", min_value=0.0, step=0.1)
    with c7: K  = st.number_input("K", min_value=0.0, step=0.1)
    with c8: Albumin = st.number_input("Albumin", min_value=0.0, step=0.1)

    c9,c10,c11,c12 = st.columns(4)
    with c9: Glucose = st.number_input("Glucose", min_value=0.0, step=1.0, format="%.0f")
    with c10: CRP = st.number_input("CRP", min_value=0.0, step=0.1)
    with c11: AST = st.number_input("AST", min_value=0.0, step=1.0, format="%.0f")
    with c12: ALT = st.number_input("ALT", min_value=0.0, step=1.0, format="%.0f")

    return Labs(WBC,Hb,PLT,ANC,Ca,Na,K,Albumin,Glucose,None,AST,ALT,None,CRP,None,None,None,None,None)

def _inputs_special():
    st.subheader("🔎 특수검사")
    c1,c2,c3 = st.columns(3)
    with c1: c3v = st.number_input("보체 C3", min_value=0.0, step=0.1)
    with c2: c4v = st.number_input("보체 C4", min_value=0.0, step=0.1)
    with c3: urine = st.selectbox("소변 잠혈", ["미시행","음성","양성"])
    return {"C3":c3v,"C4":c4v,"UrineBlood":urine}

def _interpret(labs: Labs):
    notes = []
    # 핵심 경고
    if labs.ANC and labs.ANC < 500:
        notes.append("⚠️ ANC < 500: 생야채 금지/익힌 음식만/남은 음식 2시간 이후 섭취 비권장.")
    if labs.Hb and labs.Hb < 9.0:
        notes.append("⚠️ Hb 낮음: 어지럼/빈혈 주의.")
    if labs.PLT and labs.PLT < 50:
        notes.append("⚠️ 혈소판 낮음: 출혈/넘어짐 주의.")
    if labs.Albumin and labs.Albumin < 3.5:
        notes.append("⚠️ 알부민 낮음: 영양 보충 필요.")
    if labs.K and labs.K < 3.5:
        notes.append("⚠️ 칼륨 낮음: 저칼륨 증상(쇠약/부정맥) 주의.")
    if labs.Na and labs.Na < 135:
        notes.append("⚠️ 나트륨 낮음: 저나트륨 증상 주의.")
    if labs.Ca and labs.Ca < 8.5:
        notes.append("⚠️ 칼슘 낮음: 저칼슘 증상(저림/경련) 주의.")
    if labs.CRP and labs.CRP > 0.5:
        notes.append("⚠️ 염증 지표 상승(CRP): 감염/염증 확인 필요.")
    return notes

def _food_reco(labs: Labs):
    recos = []
    if labs.ANC and labs.ANC < 500:
        recos.append(("호중구 낮음 안전식", ANC_FOOD_RULE))
    if labs.Albumin and labs.Albumin < 3.5:
        recos.append(("알부민 낮음 추천", FOOD_GUIDE["albumin_low"]))
    if labs.K and labs.K < 3.5:
        recos.append(("칼륨 낮음 추천", FOOD_GUIDE["k_low"]))
    if labs.Hb and labs.Hb < 9.0:
        recos.append(("Hb 낮음 추천", FOOD_GUIDE["hb_low"]))
    if labs.Na and labs.Na < 135:
        recos.append(("나트륨 낮음 추천", FOOD_GUIDE["na_low"]))
    if labs.Ca and labs.Ca < 8.5:
        recos.append(("칼슘 낮음 추천", FOOD_GUIDE["ca_low"]))
    return recos

def _section_chemo():
    st.subheader("항암치료")
    selected = st.multiselect("항암제", options=drug_data.CHEMO)
    abx = st.multiselect("항생제", options=drug_data.ABX)
    for k,v in drug_data.WARNINGS.items():
        if k in selected:
            st.info(f"{k}: {v}")
    st.caption("※ 철분제는 백혈병 환자에게 해로울 수 있어 **권장하지 않습니다**. 필요 시 반드시 의료진과 상의.")

def _section_peds():
    st.subheader("소아 패드")
    st.caption("연결 확인용 간단 섹션입니다. (RSV/로타 등 상세 패널은 추후 연결)")    

def main():
    st.set_page_config(page_title="피수치 가이드 v3.20 Full", page_icon="🩸", layout="centered")
    _css()
    st.title("🩸 피수치 가이드 v3.20 (Full)")
    st.caption("제작/자문: Hoya/GPT · 모바일 최적화 · 개인정보 미수집")
    _hit_counter()

    nick, pin, mode, show_special = _sidebar()
    labs = _inputs_basic()
    special = _inputs_special() if show_special else None

    st.subheader("결과 요약")
    notes = _interpret(labs)
    if notes:
        for n in notes:
            st.warning(n)
    else:
        st.success("특이 위험 신호 없음 (입력값 기준).")

    # 음식 추천
    recos = _food_reco(labs)
    if recos:
        st.subheader("추천 음식/안전식 가이드")
        for title, items in recos:
            st.write(f"**{title}**")
            st.write(", ".join(items))

    if mode == "항암치료":
        _section_chemo()
    elif mode == "소아 패드":
        _section_peds()

    st.divider()
    save_ok = bool(nick and validate_pin(pin))
    if st.button("결과 저장(세션)", disabled=not save_ok):
        st.session_state.setdefault("records", [])
        st.session_state["records"].append({"nick":nick,"pin":pin,"notes":notes})
        st.success("세션에 저장되었습니다.")

    # 보고서 다운로드(.md)
    meta = {"nick":nick or "-", "pin":pin or "-"}
    md_bytes = as_md_report(meta, notes)
    st.download_button("보고서(.md) 다운로드", data=md_bytes, file_name="bloodmap_report.md", mime="text/markdown")

    # 기록 보기
    if st.session_state.get("records"):
        st.subheader("저장된 기록(세션)")
        for i,r in enumerate(reversed(st.session_state["records"]), start=1):
            st.write(f"{i}. {r['nick']} / {', '.join(r['notes']) if r['notes'] else '특이사항 없음'}")
