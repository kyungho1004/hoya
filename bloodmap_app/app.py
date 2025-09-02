# -*- coding: utf-8 -*-
import streamlit as st
from datetime import date, datetime

# ========= Constants =========
APP_TITLE = "🩸 피수치 가이드 v3.15 (안정판·PDF 제외·풀기능)"
PAGE_TITLE = "피수치 가이드 v3.15 (안정판)"
MADE_BY = "制作者: Hoya/GPT · 자문: Hoya/GPT"
CAFE_LINK_MD = "[피수치 가이드 공식카페 바로가기](https://cafe.naver.com/bloodmap)"
FOOTER_CAFE = "피수치 가이드 공식카페: https://cafe.naver.com/bloodmap"
DISCLAIMER = "본 자료는 보호자의 이해를 돕기 위한 참고용입니다. 모든 의학적 판단은 반드시 의료진과 상의하세요."
FEVER_GUIDE = "38.0~38.5℃ 해열제/경과, 38.5℃ 이상 병원 연락, 39℃ 이상 즉시 병원 방문."

# Labels
LBL_WBC="WBC"; LBL_Hb="Hb"; LBL_PLT="혈소판"; LBL_ANC="ANC"; LBL_Ca="Ca"; LBL_P="P"; LBL_Na="Na"; LBL_K="K"
LBL_Alb="Albumin"; LBL_Glu="Glucose"; LBL_TP="Total Protein"; LBL_AST="AST"; LBL_ALT="ALT"; LBL_LDH="LDH"
LBL_CRP="CRP"; LBL_Cr="Cr"; LBL_UA="Uric Acid"; LBL_TB="Total Bilirubin"; LBL_BUN="BUN"; LBL_BNP="BNP"

ORDER=[LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K, LBL_Alb, LBL_Glu, LBL_TP,
       LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP]

# ========= Inline Helpers =========
def _f(x, d=1):
    try:
        if x is None: return None
        s = str(x).strip().replace(",", "")
        if s == "": return None
        return round(float(s), d)
    except Exception:
        return None

def entered(v):
    try:
        return v is not None and str(v).strip()!="" and float(str(v))!=0
    except Exception:
        return False

def num_input(label, key, decimals=1, placeholder=""):
    raw = st.text_input(label, key=key, placeholder=placeholder)
    return _f(raw, d=decimals)

# --- Interpretation / Guides ---
def interpret_labs(vals, extras):
    lines=[]
    anc = vals.get(LBL_ANC)
    if entered(anc):
        if anc < 500: lines.append("🚨 ANC 500 미만: 즉시 병원 상담/격리 식사 권장")
        elif anc < 1000: lines.append("⚠️ ANC 1000 미만: 익힌 음식·위생 철저, 상온 보관 음식 금지")
        else: lines.append("✅ ANC 양호: 일반 위생수칙 유지")
    alb = vals.get(LBL_Alb);  ca = vals.get(LBL_Ca);  plt = vals.get(LBL_PLT);  crp = vals.get(LBL_CRP)
    if entered(alb) and alb < 3.5: lines.append("🥚 알부민 낮음: 달걀·연두부·흰살생선·닭가슴살·귀리죽 권장")
    if entered(ca)  and ca  < 8.6: lines.append("🦴 칼슘 낮음: 연어통조림·두부·케일·브로콜리 권장(참깨 제외)")
    if entered(plt) and plt < 50:  lines.append("🩸 혈소판 50 미만: 넘어짐/출혈 주의, 양치 부드럽게")
    if entered(crp) and crp >= 0.5: lines.append("🔥 염증 수치 상승: 발열·증상 추적, 필요 시 진료")
    for k in (LBL_Na, LBL_K):
        v = vals.get(k); lo = 135 if k==LBL_Na else 3.5
        if entered(v) and v < lo: lines.append(f"⚠️ {k} 낮음: 전해질 보충/식이 조절")
    if not lines: lines.append("🙂 입력된 값 범위에서 특이 위험 신호 없음")
    return lines

def food_suggestions(vals, anc_place):
    fs=[]
    if entered(vals.get(LBL_Alb)) and vals[LBL_Alb] < 3.5:
        fs.append("알부민 낮음 → 고단백 부드러운 음식(달걀·연두부·흰살생선·닭가슴살·귀리죽).")
    if entered(vals.get(LBL_Ca)) and vals[LBL_Ca] < 8.6:
        fs.append("칼슘 낮음 → 연어통조림·두부·케일·브로콜리 (참깨 제외).")
    if fs and anc_place=="병원": fs.append("현재 병원 식사 → 병원식 권장 범위 내에서 선택.")
    return fs

def compare_with_previous(nickname, current_vals):
    out=[]
    for k, v in current_vals.items():
        if entered(v): out.append(f"- {k}: 이번 {v} (이전 대비 비교는 저장 이후 표시)")
    return out

def summarize_meds(meds):
    DB = {
        "ATRA": {"alias":"베사노이드(트레티노인)","aes":["분화증후군","피부 건조","간수치 상승"]},
        "ARA-C": {"alias":"시타라빈","aes":["골수억제","발열","고용량: 소뇌증상"]},
        "MTX": {"alias":"메토트렉세이트","aes":["간독성","구내염","신독성(고용량)"]},
        "Cyclophosphamide": {"alias":"사이클로포스파마이드","aes":["골수억제","출혈성 방광염"]},
        "Etoposide": {"alias":"에토포사이드","aes":["골수억제","저혈압(주입)"]},
        "Daunorubicin": {"alias":"다우노루비신","aes":["심독성","탈모","점막염"]},
        "Idarubicin": {"alias":"이다루비신","aes":["심독성","골수억제"]},
        "Imatinib": {"alias":"이미티닙","aes":["부종","근육통","간수치"]},
        "Bevacizumab": {"alias":"베바시주맙","aes":["출혈","혈전","상처치유 지연"]},
        "Pembrolizumab": {"alias":"펨브롤리주맙","aes":["면역관련 이상반응"]},
        "Nivolumab": {"alias":"니볼루맙","aes":["면역관련 이상반응"]},
    }
    out=[]
    for k, dose in meds.items():
        meta = DB.get(k, {"alias":"", "aes":[]})
        out.append(f"- {k}({meta['alias']}) · 용량/개수: {dose} → 주의: {', '.join(meta['aes']) or '—'}")
    return out or ["선택한 항암제가 없습니다."]

def abx_summary(extras_abx):
    GUIDE={
        "퀴놀론(Levo/Moxi 등)": ["힘줄염/파열", "QT 연장", "임신/소아 신중"],
        "마크롤라이드(Azithro/Clarithro)": ["CYP 상호작용", "QT 연장", "위장관 자극"],
        "세팔로스포린": ["과민반응 시 주의"],
        "페니실린/베타락탐": ["발진·아나필락시스 가능", "항응고제 상호작용 주의"],
    }
    out=[]
    for cat, amt in extras_abx.items():
        tips = ", ".join(GUIDE.get(cat, []))
        out.append(f"- {cat} · 투여량: {amt} → 주의: {tips}")
    return out

def render_graphs(nickname):
    st.markdown("#### 📈 추이 그래프 (데모)")
    if nickname and st.session_state.get("records", {}).get(nickname):
        st.line_chart([1,2,3,2,4])
    else:
        st.line_chart([1,1,1,1,1])

def render_schedule(nickname):
    st.markdown("#### 📅 항암 스케줄 (데모)")
    st.write("별명 기반 저장 후 일정 탭 확장 예정:", nickname or "미지정")

# ========= UI =========
def main():
    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    st.title(APP_TITLE)
    st.markdown(MADE_BY); st.markdown(CAFE_LINK_MD)

    # 공유
    st.markdown("### 🔗 공유하기")
    c1,c2,c3 = st.columns([1,1,2])
    with c1:
        st.link_button("📱 카카오톡/메신저", "https://hdzwo5ginueir7hknzzfg4.streamlit.app/")
    with c2:
        st.link_button("📝 카페/블로그", "https://cafe.naver.com/bloodmap")
    with c3:
        st.code("https://hdzwo5ginueir7hknzzfg4.streamlit.app/", language="text")
    st.caption("✅ 모바일 줄꼬임 방지 · 별명 저장/그래프 · 암/소아/희귀암 패널 · 수치 변화 비교 · 항암 스케줄(데모) · PDF 제외")

    if "records" not in st.session_state: st.session_state.records={}

    # ===== 1) 환자/모드 =====
    st.divider()
    st.header("1️⃣ 환자/모드")

    c1,c2 = st.columns(2)
    with c1:
        nickname = st.text_input("별명(저장/그래프/스케줄용)", placeholder="예: 홍길동")
    with c2:
        test_date = st.date_input("검사 날짜", value=date.today())

    anc_place = st.radio("현재 식사 장소(ANC 가이드용)", ["가정","병원"], horizontal=True)

    mode = st.selectbox("모드 선택", ["일반/암", "소아(일상/호흡기)", "소아(감염질환)", "희귀암"])

    group=None; cancer=None; infect_sel=None; ped_topic=None

    if mode == "일반/암":
        group = st.selectbox("암 그룹 선택", ["미선택/일반","혈액암","고형암","소아암"])
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
    elif mode == "소아(일상/호흡기)":
        st.caption("기본 징후(체온/호흡수/SpO₂ 등) 입력 후 위험 배너 확인")
        ped_topic = st.selectbox("소아 주제", ["영아 수유/수면", "감기 관리", "기관지염/천식 악화"])
    elif mode == "소아(감염질환)":
        infect_sel = st.selectbox("질환 선택", ["RSV", "Adenovirus", "Rotavirus"])
    else:  # 희귀암
        cancer = st.selectbox("희귀암", [
            "담낭암(Gallbladder cancer)","부신암(Adrenal cancer)","망막모세포종(Retinoblastoma)",
            "흉선종/흉선암(Thymoma/Thymic carcinoma)","신경내분비종양(NET)",
            "간모세포종(Hepatoblastoma)","비인두암(NPC)","GIST"
        ])

    # ===== 2) 항암제/항생제 =====
    st.divider()
    st.header("2️⃣ 항암제/항생제")

    heme_by_cancer = {
        "AML": ["ARA-C","Daunorubicin","Idarubicin","Cyclophosphamide","Etoposide","Fludarabine","Hydroxyurea","MTX","ATRA","G-CSF"],
        "APL": ["ATRA","Idarubicin","Daunorubicin","ARA-C","G-CSF"],
        "ALL": ["Vincristine","Asparaginase","Daunorubicin","Cyclophosphamide","MTX","ARA-C","Topotecan","Etoposide"],
        "CML": ["Imatinib","Dasatinib","Nilotinib","Hydroxyurea"],
        "CLL": ["Fludarabine","Cyclophosphamide","Rituximab"],
    }
    solid_by_cancer = {
        "폐암(Lung cancer)": ["Cisplatin","Carboplatin","Paclitaxel","Docetaxel","Gemcitabine","Pemetrexed",
                           "Gefitinib","Erlotinib","Osimertinib","Alectinib","Bevacizumab","Pembrolizumab","Nivolumab"],
        "유방암(Breast cancer)": ["Doxorubicin","Cyclophosphamide","Paclitaxel","Docetaxel","Trastuzumab","Bevacizumab"],
        "위암(Gastric cancer)": ["Cisplatin","Oxaliplatin","5-FU","Capecitabine","Paclitaxel","Trastuzumab","Pembrolizumab"],
        "대장암(Cololoractal cancer)": ["5-FU","Capecitabine","Oxaliplatin","Irinotecan","Bevacizumab"],
        "간암(HCC)": ["Sorafenib","Lenvatinib","Bevacizumab","Pembrolizumab","Nivolumab"],
        "췌장암(Pancreatic cancer)": ["Gemcitabine","Oxaliplatin","Irinotecan","5-FU"],
        "담도암(Cholangiocarcinoma)": ["Gemcitabine","Cisplatin","Bevacizumab"],
        "자궁내막암(Endometrial cancer)": ["Carboplatin","Paclitaxel"],
        "구강암/후두암": ["Cisplatin","5-FU","Docetaxel"],
        "피부암(흑색종)": ["Dacarbazine","Paclitaxel","Nivolumab","Pembrolizumab"],
        "육종(Sarcoma)": ["Doxorubicin","Ifosfamide","Pazopanib"],
        "신장암(RCC)": ["Sunitinib","Pazopanib","Bevacizumab","Nivolumab","Pembrolizumab"],
        "갑상선암": ["Lenvatinib","Sorafenib"],
        "난소암": ["Carboplatin","Paclitaxel","Bevacizumab"],
        "자궁경부암": ["Cisplatin","Paclitaxel","Bevacizumab"],
        "전립선암": ["Docetaxel","Cabazitaxel"],
        "뇌종양(Glioma)": ["Temozolomide","Bevacizumab"],
        "식도암": ["Cisplatin","5-FU","Paclitaxel","Nivolumab","Pembrolizumab"],
        "방광암": ["Cisplatin","Gemcitabine","Bevacizumab","Pembrolizumab","Nivolumab"],
    }
    rare_by_cancer = {
        "담낭암(Gallbladder cancer)": ["Gemcitabine","Cisplatin"],
        "부신암(Adrenal cancer)": ["Mitotane","Etoposide","Doxorubicin","Cisplatin"],
        "망막모세포종(Retinoblastoma)": ["Vincristine","Etoposide","Carboplatin"],
        "흉선종/흉선암(Thymoma/Thymic carcinoma)": ["Cyclophosphamide","Doxorubicin","Cisplatin"],
        "신경내분비종양(NET)": ["Etoposide","Cisplatin","Sunitinib"],
        "간모세포종(Hepatoblastoma)": ["Cisplatin","Doxorubicin"],
        "비인두암(NPC)": ["Cisplatin","5-FU","Gemcitabine","Bevacizumab","Nivolumab","Pembrolizumab"],
        "GIST": ["Imatinib","Sunitinib","Regorafenib"],
    }

    # Default drug list by selection
    drug_list = []
    if mode == "일반/암" and group and group != "미선택/일반" and cancer:
        default_drugs_by_group = {
            "혈액암": heme_by_cancer.get(cancer, []),
            "고형암": solid_by_cancer.get(cancer, []),
            "소아암": ["Cyclophosphamide","Ifosfamide","Doxorubicin","Vincristine","Etoposide","Carboplatin","Cisplatin","Topotecan","Irinotecan"],
        }
        drug_list = list(dict.fromkeys(default_drugs_by_group.get(group, [])))
    elif mode == "희귀암" and cancer:
        drug_list = rare_by_cancer.get(cancer, [])

    # Drugs UI
    drug_search = st.text_input("🔍 항암제 검색", key="drug_search")
    drug_choices = [d for d in drug_list if not drug_search or drug_search.lower() in d.lower()]
    selected_drugs = st.multiselect("항암제 선택", drug_choices, default=[])

    meds = {}
    for d in selected_drugs:
        amt = num_input(f"{d} 용량/개수", key=f"med_{d}", decimals=1, placeholder="예: 1.5")
        if entered(amt): meds[d] = amt

    # ABX UI
    st.markdown("### 🧪 항생제 선택")
    abx_guide = ["퀴놀론(Levo/Moxi 등)", "마크롤라이드(Azithro/Clarithro)", "세팔로스포린", "페니실린/베타락탐"]
    abx_sel = st.multiselect("항생제 계열", abx_guide, default=[])
    abx_vals = {}
    for a in abx_sel:
        v = num_input(f"{a} 투여량", key=f"abx_{a}", decimals=1, placeholder="예: 1")
        if entered(v): abx_vals[a] = v

    # ===== 3) 검사 수치 =====
    st.divider()
    st.header("3️⃣ 기본 혈액 검사 수치 (입력한 값만 해석)")
    vals={}
    left, right = st.columns(2)
    half=(len(ORDER)+1)//2
    for i, col in enumerate((left, right)):
        with col:
            for name in ORDER[i*half:(i+1)*half]:
                ph = "예: 0.12" if name==LBL_CRP else "예: 3.5"
                vals[name] = num_input(name, key=f"v_{name}_{i}", decimals=(2 if name==LBL_CRP else 1), placeholder=ph)

    # ===== 4) 실행 =====
    st.divider()
    if st.button("🔎 해석하기", use_container_width=True):
        st.subheader("📋 해석 결과")
        for line in interpret_labs(vals, {}):
            st.write(line)

        if nickname and st.session_state.get("records", {}).get(nickname):
            st.markdown("### 🔍 수치 변화 비교(이전 기록 대비)")
            cmp_lines = compare_with_previous(nickname, {k: vals.get(k) for k in ORDER if entered(vals.get(k))})
            if cmp_lines:
                for l in cmp_lines: st.write(l)
            else:
                st.info("비교할 이전 기록이 없거나 값이 부족합니다.")

        shown = [(k, v) for k, v in vals.items() if entered(v)]
        if shown:
            st.markdown("### 🧬 입력 요약")
            for k, v in shown: st.write(f"- {k}: {v}")

        fs = food_suggestions(vals, anc_place)
        if fs:
            st.markdown("### 🥗 음식 가이드")
            for f in fs: st.markdown(f"- {f}")

        if meds:
            st.markdown("### 💊 항암제 주의 요약")
            for line in summarize_meds(meds): st.write(line)

        if abx_vals:
            st.markdown("### 🧪 항생제 주의 요약")
            for l in abx_summary(abx_vals): st.write(l)

        st.markdown("### 🌡️ 발열 가이드")
        st.write(FEVER_GUIDE)

        # Save session record
        if nickname and nickname.strip():
            rec = {
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "mode": mode, "group": group, "cancer": cancer, "infect": infect_sel,
                "labs": {k: vals.get(k) for k in ORDER if entered(vals.get(k))},
                "meds": meds, "abx": abx_vals,
            }
            st.session_state.records.setdefault(nickname, []).append(rec)
            st.success("저장되었습니다. 아래 그래프에서 추이를 확인하세요.")
        else:
            st.info("별명을 입력하면 추이 그래프를 사용할 수 있어요.")

    # ===== 5) 그래프/스케줄 =====
    render_graphs(nickname)
    render_schedule(nickname)

    st.markdown("---")
    st.caption(FOOTER_CAFE)
    st.markdown("> " + DISCLAIMER)

if __name__ == "__main__":
    main()
