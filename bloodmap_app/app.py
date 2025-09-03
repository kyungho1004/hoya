# -*- coding: utf-8 -*-
import streamlit as st
from datetime import date, datetime

# 절대 import (루트/패키지 어디서든 안전)
from config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE, DISCLAIMER,
                    ORDER, FEVER_GUIDE)
from .drug_data import (ANTICANCER, ABX_GUIDE, SOLID_BY_CANCER,
                        SARCOMA_DIAG, SARCOMA_BY_DIAG, EXTRA_TESTS_BY_CANCER,
                        GENERAL_SPECIAL_TESTS)
from .utils import (num_input_generic, entered, interpret_labs, food_suggestions,
                    compare_with_previous, summarize_meds, abx_summary, build_report, render_graphs)

def _kdrug(name):
    alias = ANTICANCER.get(name,{}).get("alias","")
    return f"{name} ({alias})" if alias else name

def main():
    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    st.title(APP_TITLE); st.markdown(MADE_BY); st.markdown(CAFE_LINK_MD)
    # 공유/링크 (main() 내부 유지)
    st.markdown("### 🔗 공유하기")
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        st.link_button("📱 카카오톡/메신저", "https://hdzwo5ginueir7hknzzfg4.streamlit.app/")
    with c2:
        st.link_button("📝 카페/블로그", "https://cafe.naver.com/bloodmap")
    with c3:
        st.code("https://hdzwo5ginueir7hknzzfg4.streamlit.app/", language="text")
    

    # 1) 사용자·모드
    st.divider(); st.header("1️⃣ 사용자 · 모드")
    c1, c2, c3 = st.columns([1,1,1])
    with c1: nickname = st.text_input("별명", placeholder="예: 홍길동")
    with c2: pin = st.text_input("PIN (4자리)", max_chars=4, placeholder="0000")
    with c3: test_date = st.date_input("검사 날짜", value=date.today())

    if pin and not (len(pin)==4 and pin.isdigit()):
        st.error("PIN은 4자리 숫자만 가능합니다."); st.stop()
    user_id = f"{(nickname or '').strip()}#{pin.strip() if pin else ''}".strip("#")

    anc_place = st.radio("현재 식사 장소(ANC 가이드용)", ["가정", "병원"], horizontal=True)
    mode = st.selectbox("모드 선택", ["일반/암", "소아(일상/호흡기)"])
    group = cancer = sarcoma = None
    if mode == "일반/암":
        group = st.selectbox("그룹 선택", ["미선택/일반", "혈액암", "고형암", "육종(진단명 분리)"])
        if group == "혈액암":
            cancer = st.selectbox("혈액암 종류", ["AML","APL","ALL","CML","CLL"])
        elif group == "고형암":
            from .drug_data import SOLID_BY_CANCER
            cancer = st.selectbox("고형암 종류", list(SOLID_BY_CANCER.keys()))
        elif group == "육종(진단명 분리)":
            from .drug_data import SARCOMA_DIAG
            sarcoma = st.selectbox("육종 진단명", SARCOMA_DIAG); cancer = "육종(Sarcoma)"
        else:
            st.info("암 그룹을 선택하면 항암제/특수검사가 자동 노출됩니다.")

    # 2) 약물
    st.divider(); st.header("2️⃣ 약물 입력"); st.caption("항암제·항생제는 **한글 표기**를 병기합니다.")
    meds = {}; extras = {"abx":{}}
    default_drugs = []
    if mode=="일반/암" and group and group!="미선택/일반":
        from .drug_data import HEME_BY_CANCER, SARCOMA_BY_DIAG
        if group=="혈액암": default_drugs = HEME_BY_CANCER.get(cancer, [])
        elif group=="고형암": default_drugs = SOLID_BY_CANCER.get(cancer, [])
        elif group=="육종(진단명 분리)": default_drugs = SARCOMA_BY_DIAG.get(sarcoma, [])
    display_map = {d:_kdrug(d) for d in default_drugs}
    selected = st.multiselect("항암제 선택", [display_map.get(d,_kdrug(d)) for d in default_drugs], default=[])
    rev = {v:k for v,k in zip([display_map.get(d,_kdrug(d)) for d in default_drugs], default_drugs)}
    for disp in selected:
        drug = rev.get(disp) or disp.split(" (")[0]
        alias = ANTICANCER.get(drug,{}).get("alias","")
        if drug == "ATRA":
            amt = num_input_generic(f"{_kdrug(drug)} · 캡슐 개수", key=f"med_{drug}", decimals=0, placeholder="예: 2")
            if amt: meds[drug] = {"dose_or_tabs": amt, "alias": alias}
        elif drug == "ARA-C":
            form = st.selectbox(f"{_kdrug(drug)} · 제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"], key=f"form_{drug}")
            amt = num_input_generic(f"{_kdrug(drug)} · 용량/일", key=f"med_{drug}", decimals=1, placeholder="예: 100")
            if amt: meds[drug] = {"dose": amt, "form": form, "alias": alias}
        else:
            amt = num_input_generic(f"{_kdrug(drug)} · 용량/알약", key=f"med_{drug}", decimals=1, placeholder="예: 1.5")
            if amt: meds[drug] = {"dose_or_tabs": amt, "alias": alias}

    st.markdown("**항생제(계열)**")
    from .drug_data import ABX_GUIDE
    abx_sel = st.multiselect("선택", list(ABX_GUIDE.keys()), default=[])
    for a in abx_sel:
        extras["abx"][a] = num_input_generic(f"{a} · 투여량", key=f"abx_{a}", decimals=1, placeholder="예: 1")

    # 3) 피검사 + 특수검사
    st.divider(); st.header("3️⃣ 피검사 입력"); st.caption("입력한 값만 해석·표시됩니다.")
    vals = {}
    for name in ORDER:
        dec = 2 if name=="CRP" else 1
        vals[name] = num_input_generic(name, key=f"lab_{name}", decimals=dec)

    extra_vals = {}
    general_vals = {}
    with st.expander("🔬 특수검사 (토글로 선택)", expanded=True):
        col1, col2 = st.columns(2)
        with col1: use_cancer = st.checkbox("암별 특수검사 사용", value=True)
        with col2: use_general = st.checkbox("일반 특수검사(신장/면역/요검) 사용", value=True)

        if use_cancer and mode=="일반/암" and (cancer or sarcoma):
            st.markdown("**암별 특수검사**")
            items = EXTRA_TESTS_BY_CANCER.get("육종(Sarcoma)", []) if group=="육종(진단명 분리)" else EXTRA_TESTS_BY_CANCER.get(cancer, [])
            if items:
                for (label, unit, dec) in items:
                    ph = "예: 0" if dec==0 else "예: 0." + ("0"*max(dec,1))
                    v = num_input_generic(f"{label}" + (f" ({unit})" if unit else ""), key=f"extra_{label}", decimals=dec, placeholder=ph)
                    extra_vals[label] = v
            else:
                st.caption("등록된 암별 특수검사가 없습니다.")

        if use_general:
            st.markdown("**일반 특수검사(신장/면역/요검)**")
            for (label, unit, dec) in GENERAL_SPECIAL_TESTS:
                ph = "예: 0" if dec==0 else "예: 0." + ("0"*max(dec,1))
                v = num_input_generic(f"{label}" + (f" ({unit})" if unit else ""), key=f"gen_{label}", decimals=dec, placeholder=ph)
                general_vals[label] = v

    # 4) 실행
    st.divider()
    run = st.button("🔎 해석하기", use_container_width=True)
    if run:
        st.subheader("📋 해석 결과")
        for l in interpret_labs(vals, anc_place): st.write(l)
        foods = food_suggestions(vals, anc_place)
        if foods: st.markdown("### 🥗 음식 가이드"); [st.markdown(f) for f in foods]
        if meds:
            st.markdown("### 💊 항암제 요약(한글 병기)")
            for line in summarize_meds(meds): st.write(line)
        if extras.get("abx"):
            st.markdown("### 🧪 항생제 요약(계열·한글)")
            for l in abx_summary(extras["abx"]): st.write(l)
        if user_id and st.session_state.get("records", {}).get(user_id):
            st.markdown("### 🔍 이전 기록과 비교")
            cmp = compare_with_previous(user_id, {k:v for k,v in vals.items() if entered(v)})
            if cmp: [st.write(c) for c in cmp]
        st.markdown("### 🌡️ 발열 가이드"); st.write(FEVER_GUIDE)

        if nickname and pin:
            rec = {
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "mode": mode, "group": group, "cancer": cancer, "sarcoma": sarcoma,
                "labs": {k:v for k,v in vals.items() if entered(v)},
                "extra": {k:v for k,v in extra_vals.items() if entered(v)},
                "general": {k:v for k,v in general_vals.items() if entered(v)},
                "meds": meds, "extras": extras,
            }
            st.session_state.setdefault("records", {}).setdefault(user_id, []).append(rec)
            st.success(f"저장 완료: {user_id}")
        else:
            st.info("별명과 4자리 PIN을 입력하면 중복 없이 저장됩니다.")

        # 보고서(.md)
        report_md = build_report(mode,
                                 {"group":group,"cancer":cancer,"sarcoma":sarcoma,"anc_place":anc_place},
                                 vals,
                                 compare_with_previous(user_id, {k:v for k,v in vals.items() if entered(v)}) if user_id else [],
                                 extra_vals,
                                 summarize_meds(meds) if meds else [],
                                 foods if foods else [],
                                 abx_summary(extras.get("abx", {})) if extras.get("abx") else [],
                                 general_vals)
        st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                           mime="text/markdown")

    render_graphs()
    st.markdown("---"); st.caption("© 2025 BloodMap · 교육/보호자 참고용"); st.markdown("> 본 내용은 의료진의 진단/진료를 대체하지 않습니다.")
