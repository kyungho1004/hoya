
import json
from datetime import datetime as dt
import datetime
import streamlit as st

try:
    import pandas as pd
    HAS_PD = True
except Exception:
    HAS_PD = False

# ================== PAGE / HEADER ==================
st.set_page_config(page_title="피수치 자동 해석기 by Hoya", layout="centered")
st.title("🩸 피수치 자동 해석기")
st.markdown("👤 **제작자: Hoya / 자문: GPT**")

# ================== CONSTANTS & TABLES ==================
ORDER = [
    "WBC","Hb","PLT","ANC","Ca","P","Na","K","Albumin",
    "Glucose","Total Protein","AST","ALT","LDH","CRP",
    "Cr","UA","TB","BUN","BNP"
]

# --- Drug dictionary (summary only) ---
ANTICANCER = {
    # Core heme
    "6-MP":{"alias":"6-머캅토퓨린","aes":["골수억제","간수치 상승","구내염","오심"],"warn":["황달/진한 소변 시 진료","감염 징후 즉시 연락"],"ix":["알로푸리놀 병용 감량","와파린 효과 변동"]},
    "MTX":{"alias":"메토트렉세이트","aes":["골수억제","간독성","신독성","구내염","광과민"],"warn":["탈수 시 독성↑","고용량 후 류코보린"],"ix":["NSAIDs/TMP-SMX 독성↑","일부 PPI"]},
    "ATRA":{"alias":"트레티노인(ATRA)","aes":["분화증후군","발열","피부/점막 건조","두통"],"warn":["분화증후군 의심 시 즉시 병원"],"ix":["테트라사이클린계와 가성뇌종양"]},
    "ATO":{"alias":"아산화비소(ATO)","aes":["QT 연장","저K/저Mg 시 위험↑","피부 반응"],"warn":["심전도·전해질 모니터"],"ix":[]},
    "ARA-C":{"alias":"시타라빈","aes":["골수억제","발열","구내염","(HDAC) 신경독성"],"warn":["HDAC 시 신경증상 즉시 보고"],"ix":["효소유도제 상호작용"]},
    "G-CSF":{"alias":"그라신(G-CSF)","aes":["골통/근육통","주사부위 반응","드물게 비장비대"],"warn":["좌상복부 통증 시 평가"],"ix":[]},
    "Hydroxyurea":{"alias":"하이드록시우레아","aes":["골수억제","피부색소침착","궤양"],"warn":["임신 회피"],"ix":[]},
    "Daunorubicin":{"alias":"도우노루비신","aes":["골수억제","심독성","오심/구토","점막염"],"warn":["누적용량·심기능"],"ix":["심독성↑ 병용 주의"]},
    "Idarubicin":{"alias":"이달루비신","aes":["골수억제","심독성","점막염"],"warn":["심기능"],"ix":[]},
    "Mitoxantrone":{"alias":"미토잔트론","aes":["골수억제","심독성","청록색 소변"],"warn":["심기능"],"ix":[]},
    "Cyclophosphamide":{"alias":"사이클로포스파미드","aes":["골수억제","출혈성 방광염","탈모"],"warn":["수분섭취·메스나"],"ix":["CYP 상호작용"]},
    "Etoposide":{"alias":"에토포사이드","aes":["골수억제","저혈압(주입)"],"warn":[],"ix":[]},
    "Topotecan":{"alias":"토포테칸","aes":["골수억제","설사"],"warn":[],"ix":[]},
    "Fludarabine":{"alias":"플루다라빈","aes":["면역억제","감염 위험↑","혈구감소"],"warn":["PCP 예방 고려"],"ix":[]},
    "Vincristine":{"alias":"빈크리스틴","aes":["말초신경병증","변비/장폐색"],"warn":["IT 투여 금지"],"ix":["CYP3A 상호작용"]},
    # Latest heme add-ons
    "Venetoclax":{"alias":"베네토클락스","aes":["종양용해증후군","혈구감소"],"warn":["용량 단계↑·수분/알로푸리놀"],"ix":["강력 CYP3A 억제제 병용 시 용량↓"]},
    "Midostaurin":{"alias":"미도스타우린(FLT3)","aes":["오심/구토","QT 연장"],"warn":["FLT3 변이 대상"],"ix":["CYP3A"]},
    "Gilteritinib":{"alias":"길테리티닛(FLT3)","aes":["간수치 상승","QT 연장"],"warn":["FLT3 변이 대상"],"ix":["CYP3A"]},
    "Ivosidenib":{"alias":"이보시데닙(IDH1)","aes":["분화증후군","QT 연장"],"warn":["IDH1 변이 대상"],"ix":["CYP3A"]},
    "Enasidenib":{"alias":"에나시데닙(IDH2)","aes":["분화증후군","고빌리루빈혈증"],"warn":["IDH2 변이 대상"],"ix":[]},
    "Azacitidine":{"alias":"아자시티딘","aes":["골수억제","주사부위 반응"],"warn":["감염 모니터"],"ix":[]},
    "Decitabine":{"alias":"데시타빈","aes":["골수억제"],"warn":["감염 모니터"],"ix":[]},
    "CPX-351":{"alias":"CPX-351(리포솜 다우노+시타라빈)","aes":["골수억제","점막염"],"warn":["고령/이차성 AML 근거"],"ix":[]},
    "GemtuzumabOzogamicin":{"alias":"겜투주맙 오조가마이신(GO)","aes":["간독성(VOD)","혈구감소"],"warn":["간기능 모니터"],"ix":[]},

    "Imatinib":{"alias":"이미티닙(TKI)","aes":["부종","근육통"],"warn":["간기능·혈구 모니터"],"ix":["CYP3A"]},
    "Dasatinib":{"alias":"다사티닙(TKI)","aes":["흉수","혈소판 감소"],"warn":["흉수 증상 모니터"],"ix":["제산제와 흡수↓"]},
    "Nilotinib":{"alias":"닐로티닙(TKI)","aes":["QT 연장","대사이상"],"warn":["공복 복용·심전도"],"ix":["CYP3A"]},
    "Bosutinib":{"alias":"보수티닙(TKI)","aes":["설사","간수치 상승"],"warn":["간기능"],"ix":["CYP3A"]},
    "Ponatinib":{"alias":"포나티닙(TKI)","aes":["혈전·동맥사건","HTN"],"warn":["T315I 변이 등"],"ix":["CYP3A"]},
    "Asciminib":{"alias":"아시미닙(STAMP)","aes":["혈구감소","췌장효소↑"],"warn":["CML 치료경험자"],"ix":["CYP3A"]},

    # Solid tumor common + targeted/immuno
    "Doxorubicin":{"alias":"독소루비신","aes":["심독성","탈모","구내염"],"warn":["누적용량·심초음파"],"ix":[]},
    "Paclitaxel":{"alias":"파클리탁셀","aes":["말초신경병증","과민반응"],"warn":["전처치 필요"],"ix":[]},
    "Docetaxel":{"alias":"도세탁셀","aes":["중성구감소","체액저류"],"warn":[],"ix":[]},
    "Carboplatin":{"alias":"카보플라틴","aes":["골수억제"],"warn":["신기능·용량계산"],"ix":[]},
    "Cisplatin":{"alias":"시스플라틴","aes":["신독성","오심/구토","신경독성"],"warn":["수액/항구토"],"ix":[]},
    "Oxaliplatin":{"alias":"옥살리플라틴","aes":["말초신경병증(한랭)"],"warn":[],"ix":[]},
    "Irinotecan":{"alias":"이리노테칸","aes":["설사","골수억제"],"warn":["UGT1A1"],"ix":[]},
    "Capecitabine":{"alias":"카페시타빈(경구 5-FU)","aes":["손발증후군","설사"],"warn":[],"ix":[]},
    "Pemetrexed":{"alias":"페메트렉시드","aes":["골수억제","피부발진"],"warn":["엽산·B12 전처치"],"ix":[]},

    "Trastuzumab":{"alias":"트라스투주맙(HER2)","aes":["심기능저하"],"warn":["심초음파"],"ix":[]},
    "Pertuzumab":{"alias":"퍼투주맙(HER2)","aes":["설사"],"warn":["HER2 양성 대상"],"ix":[]},
    "T-DM1":{"alias":"아도-트라스투주맙 엠탄신","aes":["혈구감소","간독성"],"warn":["HER2 양성"],"ix":[]},
    "T-DXd":{"alias":"트라스투주맙 데룩테칸","aes":["간질성폐질환(ILD)"],"warn":["호흡기 증상 모니터"],"ix":[]},
    "Tamoxifen":{"alias":"타목시펜(ET)","aes":["혈전증","자궁내막변화"],"warn":[],"ix":["강력 CYP 억제제 주의"]},
    "Letrozole":{"alias":"레트로졸(ET)","aes":["골다공증","관절통"],"warn":[],"ix":[]},
    "Palbociclib":{"alias":"팔보시클립(CDK4/6)","aes":["호중구감소"],"warn":[],"ix":["CYP3A"]},
    "Olaparib":{"alias":"올라파립(PARP)","aes":["빈혈","오심"],"warn":["BRCA 관련"],"ix":[]},

    "Osimertinib":{"alias":"오시머티닙(EGFR)","aes":["QT 연장","간질성폐질환"],"warn":["EGFR 변이 대상"],"ix":[]},
    "Alectinib":{"alias":"알렉티닙(ALK)","aes":["근육통","CK 상승"],"warn":["ALK 재배열"],"ix":[]},
    "Pembrolizumab":{"alias":"펨브롤리주맙(PD-1)","aes":["면역관련 이상반응"],"warn":["면역억제제 관리"],"ix":[]},
    "Nivolumab":{"alias":"니볼루맙(PD-1)","aes":["면역관련 이상반응"],"warn":[],"ix":[]},
    "Durvalumab":{"alias":"더발루맙(PD-L1)","aes":["면역관련 이상반응"],"warn":[],"ix":[]},
    "Atezolizumab":{"alias":"아테졸리주맙(PD-L1)","aes":["면역관련 이상반응"],"warn":[],"ix":[]},
    "Bevacizumab":{"alias":"베바시주맙(anti-VEGF)","aes":["고혈압","출혈","창상지연"],"warn":["수술전후 중단"],"ix":[]},
    "Cetuximab":{"alias":"세툭시맙(EGFR)","aes":["피부발진","저Mg"],"warn":["RAS 야생형만"],"ix":[]},
    "Panitumumab":{"alias":"파니투무맙(EGFR)","aes":["피부발진"],"warn":["RAS 야생형"],"ix":[]},

    "Sorafenib":{"alias":"소라페닙(HCC)","aes":["손발증후군","HTN"],"warn":[],"ix":["CYP3A"]},
    "Lenvatinib":{"alias":"렌바티닙(HCC)","aes":["HTN","단백뇨"],"warn":[],"ix":[]},
    "Regorafenib":{"alias":"레고라페닙(HCC/CRC)","aes":["손발증후군"],"warn":[],"ix":[]},

    "Gemcitabine":{"alias":"젬시타빈","aes":["골수억제","발열"],"warn":[],"ix":[]},
    "Nab-paclitaxel":{"alias":"나브-파클리탁셀","aes":["말초신경병증"],"warn":[],"ix":[]},

    "Abiraterone":{"alias":"아비라테론","aes":["저K","체액저류"],"warn":["프레드니손 병용"],"ix":["CYP3A"]},
    "Enzalutamide":{"alias":"엔잘루타마이드","aes":["피로","고혈압"],"warn":[],"ix":["CYP3A"]},
    "Apalutamide":{"alias":"아팔루타마이드","aes":["발진","갑상선이상"],"warn":[],"ix":[]},

    # --- Sarcoma specific agents ---
    "Ifosfamide":{"alias":"이포스파미드","aes":["골수억제","신경독성","출혈성 방광염"],"warn":["메스나 병용·수분섭취"],"ix":[]},
    "Dacarbazine":{"alias":"다카바진(DTIC)","aes":["오심/구토","골수억제","광과민"],"warn":[],"ix":[]},
    "Trabectedin":{"alias":"트라벡테딘","aes":["간독성","횡문근융해"],"warn":["CK·간기능 모니터"],"ix":[]},
    "Eribulin":{"alias":"에리불린","aes":["호중구감소","말초신경병증"],"warn":[],"ix":[]},
    "Pazopanib":{"alias":"파조파닙","aes":["고혈압","간독성"],"warn":["혈압·간기능"],"ix":["CYP3A"]},
    "Sunitinib":{"alias":"수니티닙","aes":["피로","HTN","손발증후군"],"warn":[],"ix":["CYP3A"]},
    "Ripretinib":{"alias":"리프레티닙","aes":["손발증후군","HTN"],"warn":[],"ix":[]},
}

# Regimen placeholders
ANTICANCER.update({
    "VDC/IE":{"alias":"빈크+다우노+사이클로 / 이포스+에토포","aes":["중증 골수억제"],"warn":["입원·지원요법"],"ix":[]},
    "MAP":{"alias":"고용량 MTX+독소루비신+시스플라틴","aes":["신독성/심독성/점막염"],"warn":["MTX 모니터·류코보린"],"ix":[]},
    "FOLFIRINOX":{"alias":"FOL+5-FU/LV+이리노+옥살리","aes":["심한 골수억제","설사","신경병증"],"warn":["상태양호 환자"],"ix":[]},
})

# --- Cancer sets (heme + solid subtypes) ---
CANCER_HEME = {
    "AML": ["ARA-C","Daunorubicin","Idarubicin","CPX-351","GemtuzumabOzogamicin","Venetoclax","Azacitidine","Decitabine","Midostaurin","Gilteritinib","Ivosidenib","Enasidenib","Hydroxyurea","G-CSF"],
    "APL": ["ATRA","ATO","Idarubicin","ARA-C","GemtuzumabOzogamicin","G-CSF"],
    "ALL": ["Vincristine","MTX","6-MP","Cyclophosphamide","Daunorubicin","Etoposide","Blinatumomab","Inotuzumab","Pegaspargase","Nelarabine","Imatinib","Dasatinib","Ponatinib","G-CSF"],
    "CML": ["Imatinib","Dasatinib","Nilotinib","Bosutinib","Ponatinib","Asciminib","Hydroxyurea","G-CSF"],
    "CLL": ["Fludarabine","Cyclophosphamide","Venetoclax","G-CSF"],
}

CANCER_SOLID = {
    "유방암": ["Doxorubicin","Cyclophosphamide","Paclitaxel","Docetaxel","Trastuzumab","Pertuzumab","T-DM1","T-DXd","Letrozole","Tamoxifen","Palbociclib","Olaparib"],
    "폐암(NSCLC)": ["Carboplatin","Cisplatin","Paclitaxel","Pemetrexed","Osimertinib","Alectinib","Pembrolizumab","Nivolumab","Durvalumab"],
    "폐암(SCLC)": ["Carboplatin","Etoposide","Atezolizumab","Durvalumab","Topotecan"],
    "위암": ["Capecitabine","Cisplatin","Oxaliplatin","Paclitaxel","Trastuzumab","Pembrolizumab"],
    "대장암": ["Oxaliplatin","Irinotecan","Capecitabine","Bevacizumab","Cetuximab","Panitumumab","Regorafenib"],
    "간암(HCC)": ["Atezolizumab","Bevacizumab","Sorafenib","Lenvatinib","Regorafenib"],
    "췌장암": ["FOLFIRINOX","Gemcitabine","Nab-paclitaxel"],
    "난소암": ["Carboplatin","Paclitaxel","Bevacizumab","Olaparib"],
    "자궁경부암": ["Cisplatin","Paclitaxel","Bevacizumab","Pembrolizumab"],
    "전립선암": ["Docetaxel","Abiraterone","Enzalutamide","Apalutamide"],
    # Sarcoma subdivided
    "육종(연부조직)": ["Doxorubicin","Ifosfamide","Dacarbazine","Gemcitabine","Docetaxel","Trabectedin","Eribulin","Pazopanib"],
    "육종(골/뼈: 골육종)": ["MAP","Ifosfamide"],
    "육종(골/뼈: 유잉육종)": ["VDC/IE"],
    "GIST(위장관기질종양)": ["Imatinib","Sunitinib","Regorafenib","Ripretinib"],
}

FEVER_GUIDE = "🌡️ 38.0~38.5℃ 해열제/경과, 38.5℃↑ 병원 연락, 39.0℃↑ 즉시 병원. (ANC<500 동반 발열=응급)"
IRON_WARN = "⚠️ 항암/백혈병 환자는 철분제는 반드시 주치의와 상의. (비타민C 병용 시 흡수↑)"

def entered(v):
    try:
        return v is not None and str(v) != "" and float(v) > 0
    except Exception:
        return False

def interpret_labs(l):
    out=[]
    def add(s): out.append("- " + s)
    if entered(l.get("WBC")): add(f"WBC {l['WBC']}: " + ("낮음 → 감염 위험↑" if l["WBC"]<4 else "높음 → 감염/염증 가능" if l["WBC"]>10 else "정상"))
    if entered(l.get("Hb")): add(f"Hb {l['Hb']}: " + ("낮음 → 빈혈" if l["Hb"]<12 else "정상"))
    if entered(l.get("PLT")): add(f"혈소판 {l['PLT']}: " + ("낮음 → 출혈 위험" if l["PLT"]<150 else "정상"))
    if entered(l.get("ANC")): add(f"ANC {l['ANC']}: " + ("중증 감소(<500)" if l["ANC"]<500 else "감소(<1500)" if l["ANC"]<1500 else "정상"))
    if entered(l.get("Albumin")): add(f"Albumin {l['Albumin']}: " + ("낮음 → 영양/염증/간질환 가능" if l["Albumin"]<3.5 else "정상"))
    if entered(l.get("Glucose")): add(f"Glucose {l['Glucose']}: " + ("고혈당(≥200)" if l["Glucose"]>=200 else "저혈당(<70)" if l["Glucose"]<70 else "정상"))
    if entered(l.get("CRP")): add(f"CRP {l['CRP']}: " + ("상승 → 염증/감염 의심" if l["CRP"]>0.5 else "정상"))
    if entered(l.get("BUN")) and entered(l.get("Cr")) and float(l["Cr"])>0:
        ratio=float(l["BUN"])/float(l["Cr"])
        if ratio>20: add(f"BUN/Cr {ratio:.1f}: 탈수 의심")
        elif ratio<10: add(f"BUN/Cr {ratio:.1f}: 간질환/영양 고려")
    return out

def summarize_meds(meds: dict):
    out=[]
    for k, v in meds.items():
        info = ANTICANCER.get(k, {"alias": "", "aes": [], "warn": [], "ix": []})
        line = f"• {k}" + (f" ({info['alias']})" if info.get("alias") else "") + ":"
        if info.get("aes"): line += f" AE {', '.join(info['aes'])}"
        if info.get("warn"): line += f" | 주의: {', '.join(info['warn'])}"
        if info.get("ix"): line += f" | 상호작용: {', '.join(info['ix'])}"
        if k == "ARA-C" and isinstance(v, dict) and v.get("form"):
            line += f" | 제형: {v['form']}"
        out.append(line)
    return out

def food_suggestions(l):
    foods=[]
    if entered(l.get("Albumin")) and float(l["Albumin"])<3.5: foods.append("알부민 낮음 → 달걀, 연두부, 흰살 생선, 닭가슴살, 귀리죽")
    if entered(l.get("K")) and float(l["K"])<3.5: foods.append("칼륨 낮음 → 바나나, 감자, 호박죽, 고구마, 오렌지")
    if entered(l.get("Hb")) and float(l["Hb"])<12: foods.append("Hb 낮음 → 소고기, 시금치, 두부, 달걀 노른자, 렌틸콩")
    if entered(l.get("Na")) and float(l["Na"])<135: foods.append("나트륨 낮음 → 전해질 음료, 미역국, 바나나, 오트밀죽, 삶은 감자")
    if entered(l.get("Ca")) and float(l["Ca"])<8.5: foods.append("칼슘 낮음 → 연어 통조림, 두부, 케일, 브로콜리, (참깨 제외)")
    if entered(l.get("ANC")) and float(l["ANC"])<500:
        foods.append("🧼 호중구 감소: 생채소 금지, 익혀 섭취, 2시간 지난 음식 금지, 껍질 과일은 상담 후.")
    foods.append(IRON_WARN)
    return foods

# ================== SESSION ==================
if "records" not in st.session_state:
    st.session_state.records = {}

# ================== 0) 카테고리 먼저 ==================
st.divider()
st.header("0️⃣ 카테고리 선택 (맨 위 고정)")
category = st.radio("카테고리", ["일반 해석","항암치료","항생제","투석 환자","당뇨 환자"], key="cat_radio")

meds, extras = {}, {}
if category == "항암치료":
    st.markdown("### 🧬 암 종류")
    cancer_main = st.radio("암 종류를 선택하세요", ["혈액암","고형암"], horizontal=True, key="cancer_main")
    if cancer_main == "혈액암":
        cancer_type = st.selectbox("혈액암 세부", list(CANCER_HEME.keys()), key="heme_sel")
        show_list = CANCER_HEME.get(cancer_type, [])
        extras["cancer_type"] = cancer_type
    else:
        solid_sub = st.selectbox("고형암 세부", list(CANCER_SOLID.keys()), key="solid_sel")
        show_list = CANCER_SOLID.get(solid_sub, [])
        extras["cancer_type"] = solid_sub

    st.markdown("### 💊 항암제/보조제")
    if "ARA-C" in show_list and st.checkbox("ARA-C 사용"):
        meds["ARA-C"] = {
            "form": st.selectbox("ARA-C 제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"]),
            "dose": st.number_input("ARA-C 용량/일(임의 입력)", min_value=0.0, step=0.1),
        }
    for key in [k for k in show_list if k != "ARA-C"]:
        if st.checkbox(f"{key} 사용"):
            meds[key] = {"dose_or_tabs": st.number_input(f"{key} 투여량/알약 개수(소수 허용)", min_value=0.0, step=0.1)}
    st.info("💡 선택한 암 종류에 해당하는 약만 표시됩니다.")
    st.info(FEVER_GUIDE)
    if st.checkbox("이뇨제 복용 중"):
        extras["diuretic"] = True

elif category == "항생제":
    st.markdown("### 🧪 항생제")
    ABX_GUIDE = {
        "페니실린계":["발진/설사","와파린 효과↑ 가능"],
        "세팔로스포린계":["설사","일부 알코올과 병용 시 플러싱 유사"],
        "마크롤라이드":["QT 연장","CYP 상호작용(클라리스/에리쓰)"],
        "플루오로퀴놀론":["힘줄염/파열","광과민","QT 연장"],
        "카바페넴":["경련 위험(고용량/신부전)","광범위 커버"],
        "TMP-SMX":["고칼륨혈증","골수억제","MTX와 병용 주의"],
        "메트로니다졸":["금주","금속맛/구역"],
        "반코마이신":["Red man(주입속도)","신독성(고농도)"],
    }
    extras["abx"] = st.multiselect("사용 중인 항생제", list(ABX_GUIDE.keys()))

elif category == "투석 환자":
    st.markdown("### 🫧 투석 추가 항목")
    extras["urine_ml"] = st.number_input("하루 소변량 (mL)", min_value=0.0, step=10.0)
    extras["hd_today"] = st.checkbox("오늘 투석 시행")
    extras["post_hd_weight_delta"] = st.number_input("투석 후 체중 변화 (kg)", min_value=-10.0, max_value=10.0, step=0.1)
    # NEW: Salinity measurement (soup/국물 염도)
    extras["soup_salinity_pct"] = st.number_input("염도측정 (국물/음식 염도, %)", min_value=0.0, max_value=3.0, step=0.01, help="예: 0.8% 미만 권장")
    if st.checkbox("이뇨제 복용 중", key="diuretic_on_dial"):
        extras["diuretic"] = True

elif category == "당뇨 환자":
    st.markdown("### 🍚 당뇨 지표")
    extras["FPG"] = st.number_input("식전 혈당 (mg/dL)", min_value=0.0, step=1.0)
    extras["PP1h"] = st.number_input("식후 1시간 혈당 (mg/dL)", min_value=0.0, step=1.0)
    extras["PP2h"] = st.number_input("식후 2시간 혈당 (mg/dL)", min_value=0.0, step=1.0)
    extras["HbA1c"] = st.number_input("HbA1c (%)", min_value=0.0, step=0.1, format="%.1f")

# ================== 1) 환자 정보 ==================
st.divider()
st.header("1️⃣ 환자 정보 입력")
name = st.text_input("별명 또는 환자 이름을 입력하세요")
date = st.date_input("검사 날짜", value=datetime.date.today())

# ================== 2) 혈액 수치 입력 ==================
st.divider()
st.header("2️⃣ 혈액 검사 수치 입력")
st.markdown("🧪 아래 수치는 모두 선택 입력입니다. 입력한 수치만 해석 결과에 반영됩니다.")
WBC = st.number_input("WBC (백혈구)", step=0.1)
Hb = st.number_input("Hb (혈색소)", step=0.1)
PLT = st.number_input("PLT (혈소판)", step=0.1)
ANC = st.number_input("ANC (호중구)", step=1.0)
Ca = st.number_input("Ca (칼슘)", step=0.1)
P = st.number_input("P (인)", step=0.1)
Na = st.number_input("Na (소디움)", step=0.1)
K = st.number_input("K (포타슘)", step=0.1)
Albumin = st.number_input("Albumin (알부민)", step=0.1)
Glucose = st.number_input("Glucose (혈당)", step=1.0)
Total_Protein = st.number_input("Total Protein (총단백)", step=0.1)
AST = st.number_input("AST", step=1.0)
ALT = st.number_input("ALT", step=1.0)
LDH = st.number_input("LDH", step=1.0)
CRP = st.number_input("CRP", step=0.01, format="%.2f")
Cr = st.number_input("Creatinine (Cr)", step=0.1)
UA = st.number_input("Uric Acid (요산)", step=0.1)
TB = st.number_input("Total Bilirubin (TB)", step=0.1)
BUN = st.number_input("BUN", step=0.1)
BNP = st.number_input("BNP (선택)", step=1.0)

labs = {
    "WBC": WBC, "Hb": Hb, "PLT": PLT, "ANC": ANC, "Ca": Ca, "P": P, "Na": Na, "K": K,
    "Albumin": Albumin, "Glucose": Glucose, "Total Protein": Total_Protein, "AST": AST,
    "ALT": ALT, "LDH": LDH, "CRP": CRP, "Cr": Cr, "UA": UA, "TB": TB, "BUN": BUN, "BNP": BNP
}

nickname = st.text_input("별명(저장/그래프용)", placeholder="예: 홍길동")

# ================== 3) 해석 실행 및 결과 ==================
st.divider()
run = st.button("🔎 해석하기", use_container_width=True)

def render_dialysis_salinity(sal_pct: float):
    if not sal_pct or sal_pct <= 0:
        return None, None
    if sal_pct >= 1.0:
        status = "높음"
        tip = "국·찌개 염도 낮추기(물 추가, 건더기 위주), 외식 국물은 남기기, 나트륨 섭취 제한 강화."
    elif sal_pct >= 0.8:
        status = "경계"
        tip = "가능하면 0.8% 미만으로 조정. 인스턴트/젓갈/장아찌 빈도 줄이기."
    else:
        status = "양호"
        tip = "현재 유지. 체중증가/부종 있으면 추가로 조절."
    return status, tip

if run:
    st.subheader("📋 해석 결과")
    lines = interpret_labs(labs)
    for line in lines: st.write(line)

    fs = food_suggestions(labs)
    if fs:
        st.markdown("### 🥗 음식 가이드")
        for f in fs: st.write("- " + f)

    if category == "항암치료" and meds:
        st.markdown("### 💊 항암제 부작용·상호작용 요약")
        st.write(f"선택한 암 종류: **{extras.get('cancer_type','-')}**")
        for line in summarize_meds(meds): st.write(line)

    if category == "항생제" and extras.get("abx"):
        st.markdown("### 🧪 항생제 주의 요약")
        for a in extras["abx"]: st.write(f"• {a}")

    if category == "투석 환자":
        st.markdown("### 🫧 투석 특이 해석")
        # Salinity block
        sal = extras.get("soup_salinity_pct", 0.0)
        status, tip = render_dialysis_salinity(sal)
        if status:
            st.write(f"• 염도측정: {sal:.2f}% → **{status}**")
            st.write(f"  - 권장: {tip}")
            st.caption("일반 권장치: 국/찌개 염도 **0.8% 미만**을 목표로 합니다.")
        # Interdialytic weight and sodium tie-in
        if entered(labs.get("Na")) and labs["Na"]>145:
            st.write("• 혈중 나트륨 상승 → 수분 제한/염도 조절 필요.")
        if extras.get("post_hd_weight_delta") is not None:
            st.write(f"• 투석 후 체중 변화: {extras['post_hd_weight_delta']} kg")

    st.markdown("### 🌡️ 발열 가이드")
    st.write("ANC<500 + 발열은 응급입니다.")
    st.write(FEVER_GUIDE)

    # 보고서(.md)
    buf = [f"# BloodMap 보고서 ({dt.now().strftime('%Y-%m-%d %H:%M:%S')})\n", f"- 카테고리: {category}\n"]
    if 'extras' in locals() and extras.get("cancer_type"): buf.append(f"- 암 종류: {extras['cancer_type']}\n")
    buf.append("\n## 입력 수치\n")
    for name, v in labs.items():
        if entered(v): buf.append(f"- {name}: {v}\n")
    if meds:
        buf.append("\n## 항암제 요약\n")
        for m in summarize_meds(meds): buf.append(m + "\n")
    if 'extras' in locals() and extras.get("abx"):
        buf.append("\n## 항생제 주의\n")
        for a in extras["abx"]: buf.append(f"- {a}\n")
    if category == "투석 환자":
        buf.append("\n## 투석 특이 해석\n")
        sal = extras.get("soup_salinity_pct", 0.0)
        status, tip = render_dialysis_salinity(sal)
        if status:
            buf.append(f"- 염도측정: {sal:.2f}% → {status}\n")
            buf.append(f"  - 권장: {tip}\n")
        if entered(labs.get("Na")) and labs["Na"]>145:
            buf.append("- 혈중 나트륨 상승 → 수분 제한/염도 조절 필요.\n")
        if extras.get("post_hd_weight_delta") is not None:
            buf.append(f"- 투석 후 체중 변화: {extras['post_hd_weight_delta']} kg\n")

    buf.append("\n## 발열 가이드\n" + FEVER_GUIDE + "\n")
    buf.append("\n---\n제작: Hoya / 자문: GPT\n")
    report_md = "".join(buf)

    st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"),
                       file_name=f"bloodmap_report_{dt.now().strftime('%Y%m%d_%H%M%S')}.md",
                       mime="text/markdown")

    if nickname.strip():
        if st.checkbox("📝 이 별명으로 저장", value=True):
            rec = {"ts": dt.now().strftime("%Y-%m-%d %H:%M:%S"),
                   "category": category,
                   "labs": {k:v for k,v in labs.items() if entered(v)},
                   "meds": meds,
                   "extras": extras}
            st.session_state.records.setdefault(nickname, []).append(rec)
            st.success("저장되었습니다. 아래 그래프에서 추이를 확인하세요.")
    else:
        st.info("별명을 입력하면 추이 그래프를 사용할 수 있어요.")

# ================== 4) 그래프 ==================
st.markdown("---")
st.subheader("📈 별명별 추이 그래프 (WBC, Hb, PLT, CRP, ANC)")
if not HAS_PD:
    st.info("그래프는 pandas 설치 시 활성화됩니다. (pip install pandas)")
else:
    if st.session_state.records:
        sel = st.selectbox("별명 선택", sorted(st.session_state.records.keys()))
        rows = st.session_state.records.get(sel, [])
        if rows:
            data = []
            for r in rows:
                row = {"ts": r["ts"]}
                for k in ["WBC","Hb","PLT","CRP","ANC"]:
                    row[k] = r["labs"].get(k)
                data.append(row)
            import pandas as pd
            df = pd.DataFrame(data).set_index("ts")
            st.line_chart(df.dropna(how="all"))
        else:
            st.info("선택한 별명의 저장 기록이 없습니다.")
    else:
        st.info("아직 저장된 기록이 없습니다.")
