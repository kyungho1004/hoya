
from datetime import datetime, date
import os
import streamlit as st

from .config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE,
                    DISCLAIMER, ORDER, FEVER_GUIDE,
                    LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
                    LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP,
                    FONT_PATH_REG)
from .data.drugs import ANTICANCER, ABX_GUIDE
from .data.foods import FOODS
from .data.ped import PED_TOPICS, PED_INPUTS_INFO, PED_INFECT
from .utils.inputs import num_input_generic, entered, _parse_numeric
from .utils.interpret import interpret_labs, compare_with_previous, food_suggestions, summarize_meds, abx_summary
from .utils.reports import build_report, md_to_pdf_bytes_fontlocked
from .utils.graphs import render_graphs
from .utils.schedule import render_schedule

try:
    import pandas as pd
    HAS_PD = True
except Exception:
    HAS_PD = False

@st.cache_resource
def _usage_store():
    return {"page_views":0, "runs":0, "downloads":0, "unique_users": set(), "log":[]}
USAGE = _usage_store()

def _log(kind, payload=None):
    try:
        USAGE["log"].append({"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "kind": kind, "payload": payload or {}})
    except Exception: pass

if "__pv__" not in st.session_state:
    USAGE["page_views"] += 1
    st.session_state["__pv__"] = True
    _log("view")

def record_run(nickname):
    USAGE["runs"] += 1
    if nickname and nickname.strip():
        USAGE["unique_users"].add(nickname.strip())
    _log("run", {"nickname": nickname})

def record_download():
    USAGE["downloads"] += 1
    _log("download")

st.set_page_config(page_title=PAGE_TITLE, layout="centered")
st.title(APP_TITLE)
st.markdown(MADE_BY)
st.markdown(CAFE_LINK_MD)
st.caption("✅ 모바일 줄꼬임 방지 · 별명 저장/그래프 · 암별/소아/희귀암 패널 · PDF 한글 폰트 고정 · 수치 변화 비교 · 항암 스케줄표 · 계절 식재료/레시피 · ANC 병원/가정 구분 · 조회수 패널")

share_col1, share_col2, share_col3 = st.columns([1,1,2])
with share_col1:
    st.link_button("🔗 공유(웹앱 열기)", "https://hdzwo5ginueir7hknzzfg4.streamlit.app/", use_container_width=True)
with share_col2:
    st.page_link("https://cafe.naver.com/bloodmap", label="🧭 공식카페", icon="🌐")
with share_col3:
    with st.expander("📊 사용 현황", expanded=False):
        st.metric("조회수", USAGE["page_views"])
        st.metric("해석 실행 수", USAGE["runs"])
        st.metric("보고서 다운로드", USAGE["downloads"])
        try: st.metric("별명 수", len(USAGE["unique_users"]))
        except Exception: pass

os.makedirs("bloodmap_app/fonts", exist_ok=True)
if "records" not in st.session_state: st.session_state.records = {}
if "schedules" not in st.session_state: st.session_state.schedules = {}

st.divider(); st.header("1️⃣ 환자/암·소아 정보")

c1, c2 = st.columns(2)
with c1: nickname = st.text_input("별명(저장/그래프/스케줄용)", placeholder="예: 홍길동")
with c2: test_date = st.date_input("검사 날짜", value=date.today())
anc_place = st.radio("현재 식사 장소(ANC 가이드용)", ["가정", "병원"], horizontal=True)

mode = st.selectbox("모드 선택", ["일반/암", "소아(일상/호흡기)", "소아(감염질환)"])

group = None; cancer = None; infect_sel = None; ped_topic = None
if mode == "일반/암":
    group = st.selectbox("암 그룹 선택", ["미선택/일반", "혈액암", "고형암", "소아암", "희귀암"])
    if group == "혈액암":
        cancer = st.selectbox("혈액암 종류", ["AML","APL","ALL","CML","CLL"])
    elif group == "고형암":
        cancer = st.selectbox("고형암 종류", [
            "폐암(Lung cancer)","유방암(Breast cancer)","위암(Gastric cancer)",
            "대장암(Cololoractal cancer)","간암(HCC)","췌장암(Pancreatic cancer)",
            "담도암(Cholangiocarcinoma)","자궁내막암(Endometrial cancer)",
            "구강암/후두암","피부암(흑색종)","육종(Sarcoma)","신장암(RCC)",
            "갑상선암","난소암","자궁경부암","전립선암","뇌종양(Glioma)","식도암","방광암"
        ])
    elif group == "소아암":
        cancer = st.selectbox("소아암 종류", ["Neuroblastoma","Wilms tumor"])
    elif group == "희귀암":
        cancer = st.selectbox("희귀암 종류", [
            "담낭암(Gallbladder cancer)","부신암(Adrenal cancer)","망막모세포종(Retinoblastoma)",
            "흉선종/흉선암(Thymoma/Thymic carcinoma)","신경내분비종양(NET)",
            "간모세포종(Hepatoblastoma)","비인두암(NPC)","GIST"
        ])
    else:
        st.info("암 그룹을 선택하면 해당 암종에 맞는 **항암제 목록과 추가 수치 패널**이 자동 노출됩니다.")
elif mode == "소아(일상/호흡기)":
    st.markdown("### 🧒 소아 일상 주제 선택")
    st.caption(PED_INPUTS_INFO)
    ped_topic = st.selectbox("소아 주제", PED_TOPICS)
else:
    st.markdown("### 🧫 소아·영유아 감염질환")
    infect_sel = st.selectbox("질환 선택", list(PED_INFECT.keys()))
    st.write(f"- 핵심: {PED_INFECT[infect_sel].get('핵심','')}")
    st.write(f"- 진단: {PED_INFECT[infect_sel].get('진단','')}")
    st.write(f"- 특징: {PED_INFECT[infect_sel].get('특징','')}")

table_mode = st.checkbox("⚙️ PC용 표 모드(가로형)", help="모바일은 세로형 고정 → 줄꼬임 없음.")

meds = {}; extras = {}; vals = {}

if mode == "일반/암":
    heme_by_cancer = {"AML": ["ARA-C","Daunorubicin","Idarubicin","Cyclophosphamide","Etoposide","Fludarabine","Hydroxyurea","MTX","ATRA","G-CSF"],
                      "APL": ["ATRA","Idarubicin","Daunorubicin","ARA-C","G-CSF"],
                      "ALL": ["Vincristine","Asparaginase","Daunorubicin","Cyclophosphamide","MTX","ARA-C","Topotecan","Etoposide"],
                      "CML": ["Imatinib","Dasatinib","Nilotinib","Hydroxyurea"],
                      "CLL": ["Fludarabine","Cyclophosphamide","Rituximab"]}
    default_drugs_by_group = {
        "혈액암": heme_by_cancer.get(cancer, []),
        "고형암": ["Cisplatin","Carboplatin","Paclitaxel","Docetaxel","Gemcitabine","Pemetrexed","Bevacizumab","Pembrolizumab","Nivolumab"],
        "소아암": ["Cyclophosphamide","Ifosfamide","Doxorubicin","Vincristine","Etoposide","Carboplatin","Cisplatin","Topotecan","Irinotecan"],
        "희귀암": ["Imatinib","Sunitinib","Regorafenib","Mitotane"]
    }
    drug_list = list(dict.fromkeys(default_drugs_by_group.get(group, [])))
else:
    drug_list = []

drug_search = st.text_input("🔍 항암제 검색", key="drug_search")
drug_choices = [d for d in drug_list]
selected_drugs = st.multiselect("항암제 선택", drug_choices, default=[])

for d in selected_drugs:
    alias = ANTICANCER.get(d,{}).get("alias","")
    if d == "ATRA":
        amt = num_input_generic(f"{d} ({alias}) - 캡슐 개수", key=f"med_{d}", as_int=True, placeholder="예: 2")
    elif d == "ARA-C":
        ara_form = st.selectbox(f"{d} ({alias}) - 제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"], key=f"ara_form_{d}")
        amt = num_input_generic(f"{d} ({alias}) - 용량/일", key=f"med_{d}", decimals=1, placeholder="예: 100")
        if amt>0: meds[d] = {"form": ara_form, "dose": amt}
        continue
    else:
        amt = num_input_generic(f"{d} ({alias}) - 용량/알약", key=f"med_{d}", decimals=1, placeholder="예: 1.5")
    if amt and float(amt)>0: meds[d] = {"dose_or_tabs": amt}

st.markdown("### 🧪 항생제 선택 및 입력")
extras["abx"] = {}
abx_choices = list(__import__("bloodmap_app.data.drugs", fromlist=["ABX_GUIDE"]).ABX_GUIDE.keys())
selected_abx = st.multiselect("항생제 계열 선택", abx_choices, default=[])
for abx in selected_abx:
    extras["abx"][abx] = num_input_generic(f"{abx} - 복용/주입량", key=f"abx_{abx}", decimals=1, placeholder="예: 1")

st.markdown("### 💧 동반 약물/상태")
extras["diuretic_amt"] = num_input_generic("이뇨제(복용량/회/일)", key="diuretic_amt", decimals=1, placeholder="예: 1")

st.divider(); st.header("2️⃣ 기본 혈액 검사 수치 (입력한 값만 해석)")

for name in ["WBC(백혈구)","Hb(적혈구)","PLT(혈소판)","ANC(호중구,면역력)","Ca(칼슘)","P(인)","Na(나트륨)","K(포타슘)","Albumin(알부민)","Glucose(혈당)",
             "Total Protein(총단백질)","AST(간수치)","ALT(간세포수치)","LDH(유산탈수효소)","CRP(염증수치)","Cr(신장수치)","UA(요산수치)","TB(총빌리루빈)","BUN(신장수치)","BNP(심장척도)"]:
    decimals = 2 if name=="CRP(염증수치)" else 1
    vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=decimals, placeholder="")

from .utils.schedule import render_schedule
render_schedule(nickname)

st.divider()
run = st.button("🔎 해석하기", use_container_width=True)
if run: record_run(nickname)
if run:
    st.subheader("📋 해석 결과")
    lines = interpret_labs(vals, extras)
    for line in lines: st.write(line)
    if nickname and "records" in st.session_state and st.session_state.records.get(nickname):
        st.markdown("### 🔍 수치 변화 비교 (이전 기록 대비)")
        cmp_lines = compare_with_previous(nickname, {k: vals.get(k) for k in ["WBC(백혈구)","Hb(적혈구)","PLT(혈소판)","CRP(염증수치)","ANC(호중구,면역력)"] if entered(vals.get(k))})
        for l in cmp_lines: st.write(l)
    fs = food_suggestions(vals, "가정")
    if fs:
        st.markdown("### 🥗 음식 가이드 (계절/레시피 포함)")
        for f in fs: st.markdown(f)
    if meds:
        st.markdown("### 💊 항암제 부작용·상호작용 요약")
        for line in summarize_meds(meds): st.write(line)
    if extras.get("abx"):
        abx_lines = abx_summary(extras["abx"])
        if abx_lines:
            st.markdown("### 🧪 항생제 주의 요약")
            for l in abx_lines: st.write(l)
    st.markdown("### 🌡️ 발열 가이드"); from .config import FEVER_GUIDE as FG; st.write(FG)
    meta = {"group": group, "cancer": cancer, "anc_place": "가정"}
    report_md = build_report("일반/암", meta, vals, [], {}, [], fs, abx_summary(extras.get("abx", {})))
    clicked_md = st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"),
                       file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                       mime="text/markdown")
    if clicked_md: record_download()

def main():
    # 앱은 import 시점에 바로 렌더되므로 여기서는 별도 로직이 필요 없습니다.
    # Streamlit Cloud가 `from bloodmap_app.app import main`을 호출해도 안전하도록 빈 main 제공.
    return
