
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import json, os, time, hashlib, pathlib, re
from datetime import datetime

st.set_page_config(page_title="소아 패드 v3.25.4", page_icon="🍼", layout="centered")

# ---- Shared storage (same as main app) ----
HOME = str(pathlib.Path.home())
STORE_DIR = os.path.join(HOME, ".bloodmap")
STORE_PATH = os.path.join(STORE_DIR, "data_store.json")

def ensure_store_dir():
    try:
        os.makedirs(STORE_DIR, exist_ok=True)
        return True, None
    except Exception as e:
        return False, str(e)

def load_store():
    ok, err = ensure_store_dir()
    if not ok:
        st.error(f"저장 경로 생성 실패: {err}")
        return {}
    if not os.path.exists(STORE_PATH):
        return {}
    try:
        with open(STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"저장 파일 읽기 실패: {e}")
        return {}

def save_store(store: dict):
    ok, err = ensure_store_dir()
    if not ok:
        st.error(f"저장 경로 생성 실패: {err}")
        return False
    try:
        with open(STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"저장 실패: {e}")
        return False

def pin_hash(pin: str) -> str:
    return hashlib.sha256((pin or '').encode('utf-8')).hexdigest()

def composite_key(nickname: str, pin: str) -> str:
    return f"{nickname.strip()}::{pin_hash(pin)}"

def valid_pin(pin: str) -> bool:
    return bool(re.fullmatch(r"\d{4}", pin or ""))

# Load CSS if exists
try:
    with open("style.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

st.markdown("### 🍼 소아 패드 v3.25.4 (단독 실행용)")

# ---- Auth ----
with st.container():
    c1, c2, c3 = st.columns([2,1,1])
    with c1:
        nickname = st.text_input("별명", max_chars=30, placeholder="예: 코비, 하늘123", key="nick")
    with c2:
        pin = st.text_input("PIN(4자리 숫자)", type="password", max_chars=4, placeholder="••••", key="pin")
    with c3:
        if st.button("프로필 연결/만들기", key="connect"):
            if not nickname:
                st.error("별명을 입력하세요.")
            elif not valid_pin(pin):
                st.error("PIN은 숫자 4자리여야 합니다.")
            else:
                st.session_state["active_key"] = composite_key(nickname, pin)
                store = load_store()
                ak = st.session_state["active_key"]
                if ak not in store:
                    store[ak] = {"meta": {"nickname": nickname, "created_at": time.time()}, "peds_pad": {}}
                    if save_store(store):
                        st.success("새 프로필 생성 완료(별명+PIN).")
                else:
                    st.success("프로필 연결 완료.")
st.caption("※ PIN은 해시로 저장하며, 같은 별명이라도 PIN이 다르면 서로 다른 사용자로 분리됩니다.")

if "active_key" not in st.session_state:
    st.info("상단에서 별명 + PIN을 먼저 연결하세요.")
    st.stop()

# ---- Quick Pad form ----
st.markdown("#### 기본 정보")
col1, col2, col3 = st.columns(3)
with col1:
    age_m = st.number_input("나이(개월)", min_value=0, max_value=216, value=12, step=1, key="age_m")
with col2:
    weight = st.number_input("체중(kg)", min_value=0.0, max_value=200.0, value=10.0, step=0.1, key="wt")
with col3:
    visit_time = st.text_input("방문시각", value=datetime.now().strftime("%Y-%m-%d %H:%M"), key="visit_t")

st.markdown("#### 활력/호흡")
c1, c2, c3, c4 = st.columns(4)
with c1:
    temp = st.number_input("체온(℃)", min_value=34.0, max_value=42.5, value=37.2, step=0.1, key="temp")
with c2:
    rr = st.number_input("호흡수(/min)", min_value=0, max_value=120, value=32, step=1, key="rr")
with c3:
    spo2 = st.number_input("SpO₂(%)", min_value=50, max_value=100, value=98, step=1, key="spo2")
with c4:
    urine = st.number_input("소변 횟수(하루)", min_value=0, max_value=20, value=6, step=1, key="urine")

c5, c6, c7 = st.columns(3)
with c5:
    retractions = st.checkbox("흉곽 함몰", value=False, key="ret")
with c6:
    nasal_flare = st.checkbox("콧벌렁임", value=False, key="nasal")
with c7:
    apnea = st.checkbox("무호흡", value=False, key="apnea")

# Risk banner
def ped_risk_banner(age_month, temp, rr, spo2, urine, retractions, nasal_flare, apnea):
    danger = False; caution = False; notes = []
    if spo2 is not None and spo2 < 92: danger=True; notes.append("SpO₂ < 92%")
    if apnea: danger=True; notes.append("무호흡")
    if temp is not None and age_month is not None and temp >= 39.0 and age_month < 3:
        danger=True; notes.append("3개월 미만 고열")
    if retractions or nasal_flare: caution=True; notes.append("호흡곤란 징후")
    if urine is not None and urine <= 2: caution=True; notes.append("소변 감소(탈수 의심)")
    if danger:
        st.markdown('<div class="risk-danger">🚨 위급</div>', unsafe_allow_html=True)
    elif caution:
        st.markdown('<div class="risk-caution">⚠️ 주의</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="risk-ok">✅ 가정관리 가능</div>', unsafe_allow_html=True)

st.markdown("#### 위험도")
ped_risk_banner(st.session_state.get("age_m"), st.session_state.get("temp"), st.session_state.get("rr"),
                st.session_state.get("spo2"), st.session_state.get("urine"),
                st.session_state.get("ret"), st.session_state.get("nasal"), st.session_state.get("apnea"))

st.markdown("#### 증상/메모")
symptoms = st.text_area("주요 증상", placeholder="예: 기침, 콧물, 고열 39.2℃, 수유량 감소 ...", key="sym")
notes = st.text_area("추가 메모", placeholder="검사/처치/교육 메모", key="note")

# ---- Save/Load in profile ----
def save_pad():
    store = load_store()
    ak = st.session_state["active_key"]
    entry = {
        "age_m": st.session_state.get("age_m"),
        "weight": st.session_state.get("wt"),
        "visit_time": st.session_state.get("visit_t"),
        "temp": st.session_state.get("temp"),
        "rr": st.session_state.get("rr"),
        "spo2": st.session_state.get("spo2"),
        "urine": st.session_state.get("urine"),
        "retractions": st.session_state.get("ret"),
        "nasal_flare": st.session_state.get("nasal"),
        "apnea": st.session_state.get("apnea"),
        "symptoms": st.session_state.get("sym"),
        "notes": st.session_state.get("note"),
        "saved_at": time.time()
    }
    store.setdefault(ak, {}).setdefault("peds_pad", {})
    store[ak]["peds_pad"] = entry
    if save_store(store):
        st.success("소아 패드 저장 완료")
        return True
    return False

def load_pad():
    store = load_store()
    ak = st.session_state["active_key"]
    return store.get(ak, {}).get("peds_pad", {})

cbtn1, cbtn2, cbtn3 = st.columns(3)
with cbtn1:
    if st.button("저장(별명+PIN)", key="save"):
        save_pad()
with cbtn2:
    if st.button("불러오기", key="load"):
        data = load_pad()
        if not data:
            st.warning("저장된 패드가 없습니다.")
        else:
            for k, v in data.items():
                st.session_state[k] = v
            st.success("불러오기 완료")

with cbtn3:
    # Export section
    def to_markdown(data: dict) -> str:
        lines = [
            "# 🍼 소아 패드 내보내기",
            f"- 저장시각: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"- 나이(개월): {data.get('age_m','')}",
            f"- 체중(kg): {data.get('weight','')}",
            f"- 방문시각: {data.get('visit_time','')}",
            f"- 체온: {data.get('temp','')} ℃",
            f"- 호흡수: {data.get('rr','')} /min",
            f"- SpO₂: {data.get('spo2','')} %",
            f"- 소변 횟수: {data.get('urine','')} /일",
            f"- 흉곽 함몰: {'있음' if data.get('retractions') else '없음'}",
            f"- 콧벌렁임: {'있음' if data.get('nasal_flare') else '없음'}",
            f"- 무호흡: {'있음' if data.get('apnea') else '없음'}",
            "",
            "## 증상",
            data.get('symptoms',''),
            "",
            "## 메모",
            data.get('notes','')
        ]
        return "\n".join(lines)

    export_data = {
        "age_m": st.session_state.get("age_m"),
        "weight": st.session_state.get("wt"),
        "visit_time": st.session_state.get("visit_t"),
        "temp": st.session_state.get("temp"),
        "rr": st.session_state.get("rr"),
        "spo2": st.session_state.get("spo2"),
        "urine": st.session_state.get("urine"),
        "retractions": st.session_state.get("ret"),
        "nasal_flare": st.session_state.get("nasal"),
        "apnea": st.session_state.get("apnea"),
        "symptoms": st.session_state.get("sym"),
        "notes": st.session_state.get("note"),
    }
    md_text = to_markdown(export_data)
    st.download_button("⬇️ 내보내기(Markdown)", data=md_text, file_name="peds_pad_export.md", mime="text/markdown", key="dl_md")

    # CSV export
    import io, csv
    csv_buf = io.StringIO()
    writer = csv.writer(csv_buf)
    writer.writerow(["field","value"])
    for k,v in export_data.items():
        writer.writerow([k, v])
    st.download_button("⬇️ 내보내기(CSV)", data=csv_buf.getvalue(), file_name="peds_pad_export.csv", mime="text/csv", key="dl_csv")

st.caption("※ 본 도구는 참고 용이며, 최종 판단은 의료진의 임상적 판단에 따릅니다.")
