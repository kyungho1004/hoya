
import json
from datetime import datetime, date
import streamlit as st

# Optional pandas (for charts). App runs without it.
try:
    import pandas as pd
    HAS_PD = True
except Exception:
    HAS_PD = False

# -------------- Page Setup --------------
st.set_page_config(page_title="피수치 자동 해석기 by Hoya", layout="centered")
st.title("🩸 피수치 자동 해석기 (통합본 v2.9+)")
st.markdown("👤 **제작자: Hoya / 자문: GPT** · 📅 {} 기준".format(date.today().isoformat()))

# -------------- Session State --------------
if "records" not in st.session_state:
    st.session_state.records = {}

# -------------- Constants --------------
ORDER = [
    "WBC","Hb","PLT","ANC",
    "Ca","P","Na","K",
    "Albumin","Glucose","Total Protein",
    "AST","ALT","LDH","CRP",
    "Cr","UA","TB","BUN","BNP"
]

ANTICANCER = {
    "6-MP":{"alias":"6-머캅토퓨린","aes":["골수억제","간수치 상승","구내염","오심"],"warn":["황달/진한 소변 시 진료","감염 징후 즉시 연락"],"ix":["알로푸리놀 병용 감량 가능","와파린 효과 변동"]},
    "MTX":{"alias":"메토트렉세이트","aes":["골수억제","간독성","신독성","구내염","광과민"],"warn":["탈수 시 독성↑","고용량 후 류코보린"],"ix":["NSAIDs/TMP-SMX 병용 독성↑","일부 PPI 상호작용"]},
    "ATRA":{"alias":"트레티노인(베사노이드)","aes":["분화증후군","발열","피부/점막 건조","두통"],"warn":["분화증후군 의심 시 즉시 병원"],"ix":["테트라사이클린계와 가성뇌종양"]},
    "ARA-C":{"alias":"시타라빈","aes":["골수억제","발열","구내염","(HDAC) 신경독성"],"warn":["HDAC 시 신경증상 즉시 보고"],"ix":["효소유도제 상호작용"]},
    "G-CSF":{"alias":"그라신","aes":["골통/근육통","주사부위 반응","드물게 비장비대"],"warn":["좌상복부 통증 시 평가"],"ix":[]},
    "Hydroxyurea":{"alias":"하이드록시우레아","aes":["골수억제","피부색소침착","궤양"],"warn":["임신 회피"],"ix":[]},
    "Daunorubicin":{"alias":"도우노루비신","aes":["골수억제","심독성","오심/구토","점막염"],"warn":["누적용량 심기능"],"ix":["심독성↑ 병용 주의"]},
    "Idarubicin":{"alias":"이달루비신","aes":["골수억제","심독성","점막염"],"warn":["심기능"],"ix":[]},
    "Mitoxantrone":{"alias":"미토잔트론","aes":["골수억제","심독성","청록색 소변"],"warn":["심기능"],"ix":[]},
    "Cyclophosphamide":{"alias":"사이클로포스파미드","aes":["골수억제","출혈성 방광염","탈모"],"warn":["수분섭취·메스나"],"ix":["CYP 상호작용"]},
    "Etoposide":{"alias":"에토포사이드","aes":["골수억제","저혈압(주입)"],"warn":[],"ix":[]},
    "Topotecan":{"alias":"토포테칸","aes":["골수억제","설사"],"warn":[],"ix":[]},
    "Fludarabine":{"alias":"플루다라빈","aes":["면역억제","감염 위험↑","혈구감소"],"warn":["PCP 예방 고려"],"ix":[]},
    "Vincristine":{"alias":"빈크리스틴","aes":["말초신경병증","변비/장폐색"],"warn":["IT 투여 금지"],"ix":["CYP3A 상호작용"]},
    "Paclitaxel":{"alias":"파클리탁셀","aes":["말초신경병증","호중구감소"],"warn":["과민반응 예방(스테로이드 등)"],"ix":[]},
    "Docetaxel":{"alias":"도세탁셀","aes":["체액저류","호중구감소"],"warn":["전처치 스테로이드"],"ix":[]},
    "Doxorubicin":{"alias":"독소루비신","aes":["심독성","탈모","구내염"],"warn":["누적용량 주의"],"ix":[]},
    "Carboplatin":{"alias":"카보플라틴","aes":["혈구감소","신독성(경미)"],"warn":["Calvert 공식"],"ix":[]},
    "Cisplatin":{"alias":"시스플라틴","aes":["신독성","오심/구토","이독성"],"warn":["수분/항구토제"],"ix":[]},
    "Oxaliplatin":{"alias":"옥살리플라틴","aes":["말초신경병증(냉감 유발)"],"warn":["찬음식/찬바람 주의"],"ix":[]},
    "5-FU":{"alias":"플루오로우라실","aes":["점막염","설사","수족증후군"],"warn":["DPD 결핍 주의"],"ix":[]},
    "Capecitabine":{"alias":"카페시타빈","aes":["수족증후군","설사"],"warn":["신기능 따라 감량"],"ix":[]},
    "Gemcitabine":{"alias":"젬시타빈","aes":["혈구감소","발열"],"warn":[],"ix":[]},
    "Pemetrexed":{"alias":"페메트렉시드","aes":["골수억제","피부발진"],"warn":["엽산/비타민B12 보충"],"ix":[]},
    "Irinotecan":{"alias":"이리노테칸","aes":["급성/지연성 설사"],"warn":["로페라미드 지침"],"ix":[]},
    "Trastuzumab":{"alias":"트라스투주맙","aes":["심기능저하"],"warn":["좌심실 기능 모니터"],"ix":[]},
    "Ifosfamide":{"alias":"이포스파미드","aes":["골수억제","신경독성","출혈성 방광염"],"warn":["메스나 병용/수분섭취"],"ix":[]},
}

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

FOODS = {
    "Albumin_low": ["달걀","연두부","흰살 생선","닭가슴살","귀리죽"],
    "K_low": ["바나나","감자","호박죽","고구마","오렌지"],
    "Hb_low": ["소고기","시금치","두부","달걀 노른자","렌틸콩"],
    "Na_low": ["전해질 음료","미역국","바나나","오트밀죽","삶은 감자"],
    "Ca_low": ["연어 통조림","두부","케일","브로콜리","(참깨 제외)"],
}
FEVER_GUIDE = "🌡️ 38.0~38.5℃ 해열제/경과, 38.5℃↑ 병원 연락, 39.0℃↑ 즉시 병원. (ANC<500 동반 발열=응급)"

HEMATO = {
    "AML": {"note":"ANC 최우선 모니터링, Ara-C 사용 시 간/신장 수치 주의","extra_tests":["PT","aPTT","Fibrinogen"],"drugs":["ARA-C","Daunorubicin","Idarubicin","Mitoxantrone","G-CSF","Cyclophosphamide","Etoposide","Fludarabine","Hydroxyurea","Vincristine","MTX","ATRA"]},
    "APL": {"note":"DIC 동반 위험: PT/aPTT/피브리노겐, D-dimer; 분화증후군 주의","extra_tests":["PT","aPTT","Fibrinogen","D-dimer","DIC Score"],"drugs":["ATRA","ARA-C","Idarubicin","Daunorubicin","G-CSF","Hydroxyurea"]},
    "ALL": {"note":"CNS prophylaxis(IT MTX 등) 고려; 빈혈/혈소판 주기적 점검","extra_tests":["PT","aPTT"],"drugs":["Vincristine","MTX","Cyclophosphamide","Daunorubicin","ARA-C","G-CSF","Etoposide","Topotecan","Fludarabine","Hydroxyurea"]},
    "CML": {"note":"WBC↑↑ 가능, LDH↑; BCR-ABL PCR 추적","extra_tests":["BCR-ABL PCR"],"drugs":["Hydroxyurea","Cyclophosphamide","ARA-C","G-CSF"]},
    "CLL": {"note":"림프구 비율↑, 저감마글로불린혈증 가능","extra_tests":["면역글로불린"],"drugs":["Fludarabine","Cyclophosphamide","Mitoxantrone","Etoposide","Hydroxyurea","G-CSF"]},
}

SOLID = {
    "폐암(NSCLC)": {"note":"간/신장 수치와 호중구 모니터","extra_tests":[],"drugs":["Carboplatin","Cisplatin","Paclitaxel","Docetaxel","Pemetrexed","Gemcitabine","5-FU"]},
    "유방암": {"note":"심기능 모니터(안트라사이클린/트라스투주맙)","extra_tests":[],"drugs":["Doxorubicin","Cyclophosphamide","Paclitaxel","Docetaxel","Carboplatin","Trastuzumab"]},
    "대장암": {"note":"옥살리플라틴 말초신경, 5-FU/Capecitabine 수족증후군","extra_tests":[],"drugs":["Oxaliplatin","5-FU","Capecitabine","Irinotecan"]},
    "위암": {"note":"백금계+플루오로피리미딘 조합 흔함","extra_tests":[],"drugs":["Cisplatin","Carboplatin","5-FU","Capecitabine","Paclitaxel","Docetaxel"]},
    "간암(HCC)": {"note":"간기능 악화 위험; 간수치·빌리루빈 면밀 확인","extra_tests":[],"drugs":["Doxorubicin","Cisplatin","5-FU","Gemcitabine"]},
    "췌장암": {"note":"혈구감소/영양 저하 위험; 전신 상태 관찰","extra_tests":[],"drugs":["Gemcitabine","5-FU","Oxaliplatin","Irinotecan","Capecitabine"]},
    "육종(Sarcoma)": {"note":"안트라사이클린 기반 많이 사용","extra_tests":[],"drugs":["Doxorubicin","Ifosfamide","Cyclophosphamide","Gemcitabine","Docetaxel","Paclitaxel"]},
}


# -------------- Cancer-specific Lab Panels --------------
# Solid tumor extra panels
SOLID_EXTRA_LABS = {
    "폐암(NSCLC)": [
        {"key":"CEA", "label":"CEA (ng/mL)", "type":"num", "step":0.1},
        {"key":"CYFRA21-1", "label":"CYFRA21-1 (ng/mL)", "type":"num", "step":0.1},
    ],
    "유방암": [
        {"key":"ER", "label":"ER (%)", "type":"num", "step":1.0},
        {"key":"PR", "label":"PR (%)", "type":"num", "step":1.0},
        {"key":"HER2", "label":"HER2 (IHC 0-3+)", "type":"num", "step":1.0},
        {"key":"EF", "label":"좌심실 박출률 EF (%)", "type":"num", "step":1.0},
    ],
    "대장암": [
        {"key":"CEA", "label":"CEA (ng/mL)", "type":"num", "step":0.1},
        {"key":"ALP", "label":"ALP (U/L)", "type":"num", "step":1.0},
    ],
    "위암": [
        {"key":"CEA", "label":"CEA (ng/mL)", "type":"num", "step":0.1},
        {"key":"CA19-9", "label":"CA19-9 (U/mL)", "type":"num", "step":1.0},
    ],
    "간암(HCC)": [
        {"key":"AFP", "label":"AFP (ng/mL)", "type":"num", "step":1.0},
        {"key":"PIVKA-II", "label":"PIVKA-II (mAU/mL)", "type":"num", "step":1.0},
        {"key":"Total Bilirubin", "label":"Total Bilirubin (mg/dL)", "type":"num", "step":0.1},
    ],
    "췌장암": [
        {"key":"CA19-9", "label":"CA19-9 (U/mL)", "type":"num", "step":1.0},
        {"key":"Amylase", "label":"Amylase (U/L)", "type":"num", "step":1.0},
        {"key":"Lipase", "label":"Lipase (U/L)", "type":"num", "step":1.0},
    ],
    "육종(Sarcoma)": [
        {"key":"LDH_extra", "label":"LDH (U/L)", "type":"num", "step":1.0},
        {"key":"ALP", "label":"ALP (U/L)", "type":"num", "step":1.0},
    ],
}

# Define extra labs per hematologic cancer and simple thresholds for interpretation
CANCER_EXTRA_LABS = {
    "AML": [
        {"key":"PT", "label":"PT (sec)", "type":"num", "step":0.1},
        {"key":"aPTT", "label":"aPTT (sec)", "type":"num", "step":0.1},
        {"key":"Fibrinogen", "label":"Fibrinogen (mg/dL)", "type":"num", "step":1.0},
    ],
    "APL": [
        {"key":"PT", "label":"PT (sec)", "type":"num", "step":0.1},
        {"key":"aPTT", "label":"aPTT (sec)", "type":"num", "step":0.1},
        {"key":"Fibrinogen", "label":"Fibrinogen (mg/dL)", "type":"num", "step":1.0},
        {"key":"D-dimer", "label":"D-dimer (µg/mL FEU)", "type":"num", "step":0.1},
        {"key":"DIC Score", "label":"DIC Score (점수)", "type":"num", "step":1.0},
    ],
    "ALL": [
        {"key":"PT", "label":"PT (sec)", "type":"num", "step":0.1},
        {"key":"aPTT", "label":"aPTT (sec)", "type":"num", "step":0.1},
    ],
    "CML": [
        {"key":"BCR-ABL PCR", "label":"BCR-ABL PCR (%IS)", "type":"num", "step":0.01},
        {"key":"LDH", "label":"LDH", "type":"alias"},  # already in base ORDER, alias to emphasize
    ],
    "CLL": [
        {"key":"IgG", "label":"IgG (mg/dL)", "type":"num", "step":10.0},
        {"key":"IgA", "label":"IgA (mg/dL)", "type":"num", "step":10.0},
        {"key":"IgM", "label":"IgM (mg/dL)", "type":"num", "step":5.0},
    ],
    ,
    # ---- SOLID TUMORS ----
    "폐암(NSCLC)": [
        {"key":"CEA", "label":"CEA (ng/mL)", "type":"num", "step":0.1},
        {"key":"CYFRA21-1", "label":"CYFRA 21-1 (ng/mL)", "type":"num", "step":0.1},
    ],
    "유방암": [
        {"key":"ER", "label":"ER 상태", "type":"select", "options":["Unknown","Negative","Positive"]},
        {"key":"PR", "label":"PR 상태", "type":"select", "options":["Unknown","Negative","Positive"]},
        {"key":"HER2", "label":"HER2 상태", "type":"select", "options":["Unknown","0/1- (음성)","2+ (경계)","3+ (양성)"]},
        {"key":"LVEF", "label":"좌심실 구혈률 LVEF (%)", "type":"num", "step":1.0},
    ],
    "대장암": [
        {"key":"CEA", "label":"CEA (ng/mL)", "type":"num", "step":0.1},
        {"key":"ALP", "label":"ALP (U/L)", "type":"num", "step":1.0},
    ],
    "위암": [
        {"key":"CEA", "label":"CEA (ng/mL)", "type":"num", "step":0.1},
        {"key":"CA19-9", "label":"CA 19-9 (U/mL)", "type":"num", "step":1.0},
    ],
    "간암(HCC)": [
        {"key":"AFP", "label":"AFP (ng/mL)", "type":"num", "step":1.0},
        {"key":"PIVKA-II", "label":"PIVKA-II (mAU/mL)", "type":"num", "step":1.0},
        {"key":"TB_alias", "label":"(참고) 총빌리루빈 TB는 기본 패널에 있음", "type":"alias"},
    ],
    "췌장암": [
        {"key":"CA19-9", "label":"CA 19-9 (U/mL)", "type":"num", "step":1.0},
        {"key":"Amylase", "label":"Amylase (U/L)", "type":"num", "step":1.0},
        {"key":"Lipase", "label":"Lipase (U/L)", "type":"num", "step":1.0},
    ],
    "육종(Sarcoma)": [
        {"key":"LDH_alias", "label":"(참고) LDH는 기본 패널에 있음", "type":"alias"},
        {"key":"ALP", "label":"ALP (U/L)", "type":"num", "step":1.0},
    ]
}

def get_extra_panel(group, cancer):
    if group == "고형암":
        return SOLID_EXTRA_LABS.get(cancer, [])

    if group != "혈액암": 
        return []
    return CANCER_EXTRA_LABS.get(cancer, [])

def interpret_cancer_specific(cancer, vals, group):
    notes = []
    def add(s): notes.append("- " + s)
    v = vals.get
    # Common coag thresholds
    if cancer in ("AML","APL","ALL"):
        if v("PT") is not None and v("PT") != "":
            try:
                if float(v("PT")) > 15: add(f"PT {v('PT')}: 연장 → 응고장애/DIC 고려")
            except: pass
        if v("aPTT") is not None and v("aPTT") != "":
            try:
                if float(v("aPTT")) > 40: add(f"aPTT {v('aPTT')}: 연장")
            except: pass
    if cancer in ("AML","APL"):
        try:
            if vals.get("Fibrinogen") is not None and float(vals["Fibrinogen"]) < 150:
                add(f"Fibrinogen {vals['Fibrinogen']}: 감소 → DIC 위험")
        except: pass
    if cancer == "APL":
        try:
            if vals.get("D-dimer") is not None and float(vals["D-dimer"]) > 0.5:
                add(f"D-dimer {vals['D-dimer']}: 상승 → DIC 의심")
        except: pass
        try:
            if vals.get("DIC Score") is not None and float(vals["DIC Score"]) >= 5:
                add(f"DIC Score {vals['DIC Score']}: DIC 가능성↑ (즉시 보고)")
        except: pass
    if cancer == "CML":
        try:
            if vals.get("BCR-ABL PCR") is not None:
                add(f"BCR-ABL PCR: {vals['BCR-ABL PCR']} %IS (치료반응 추적 지표)")
        except: pass
    if cancer == "CLL":
        # Simple lower bounds for hypogammaglobulinemia
        try:
            for k, th in [("IgG",700),("IgA",70),("IgM",40)]:
                if vals.get(k) is not None and float(vals[k]) < th:
                    add(f"{k} {vals[k]}: 낮음 → 감염 위험↑ (IVIG 고려 상황 상담)")
        except: pass
    
    if group == "고형암":
        if cancer == "폐암(NSCLC)":
            try:
                if vals.get("CEA") and float(vals["CEA"]) > 5:
                    add(f"CEA {vals['CEA']}: 상승 → 재발/전이 가능성")
            except: pass
        if cancer == "유방암":
            try:
                if vals.get("HER2") and float(vals["HER2"]) >= 3:
                    add("HER2 3+: 표적치료(Trastuzumab 등) 적합 가능")
            except: pass
            try:
                if vals.get("EF") and float(vals["EF"]) < 50:
                    add(f"EF {vals['EF']}%: 심기능 저하 → Trastuzumab 주의")
            except: pass
        if cancer == "간암(HCC)":
            try:
                if vals.get("AFP") and float(vals["AFP"]) > 400:
                    add(f"AFP {vals['AFP']}: 상승 → 간암 진행 의심")
            except: pass
            try:
                if vals.get("Total Bilirubin") and float(vals["Total Bilirubin"]) > 2:
                    add(f"Total Bilirubin {vals['Total Bilirubin']}: 상승 → 간기능 저하")
            except: pass
        if cancer == "췌장암":
            try:
                if vals.get("CA19-9") and float(vals["CA19-9"]) > 37:
                    add(f"CA19-9 {vals['CA19-9']}: 상승 → 진행/재발 가능성")
            except: pass
    # ---- SOLID Tumors ----
    if cancer == "폐암(NSCLC)":
        try:
            if vals.get("CEA") is not None and float(vals["CEA"]) > 5:
                add(f"CEA {vals['CEA']}: 상승 (재발/진행 평가 참고)")
        except: pass
        try:
            if vals.get("CYFRA21-1") is not None and float(vals["CYFRA21-1"]) > 3.3:
                add(f"CYFRA 21-1 {vals['CYFRA21-1']}: 상승 (편평상피암/진행 지표 참고)")
        except: pass
    if cancer == "유방암":
        er, pr, her2 = vals.get("ER"), vals.get("PR"), vals.get("HER2")
        status = []
        if er: status.append(f"ER: {er}")
        if pr: status.append(f"PR: {pr}")
        if her2: status.append(f"HER2: {her2}")
        if status: add(" / ".join(status))
        try:
            if vals.get("LVEF") is not None and float(vals["LVEF"]) < 50:
                add(f"LVEF {vals['LVEF']}%: 낮음 → 안트라/트라스투주맙 사용 시 심기능 주의")
        except: pass
    if cancer == "대장암" or cancer == "위암":
        try:
            if vals.get("CEA") is not None and float(vals["CEA"]) > 5:
                add(f"CEA {vals['CEA']}: 상승")
        except: pass
        if cancer == "위암":
            try:
                if vals.get("CA19-9") is not None and float(vals["CA19-9"]) > 37:
                    add(f"CA 19-9 {vals['CA19-9']}: 상승")
            except: pass
        if cancer == "대장암":
            try:
                if vals.get("ALP") is not None and float(vals["ALP"]) > 120:
                    add(f"ALP {vals['ALP']}: 상승 (간/골 전이 평가 참고)")
            except: pass
    if cancer == "간암(HCC)":
        try:
            if vals.get("AFP") is not None and float(vals["AFP"]) >= 200:
                add(f"AFP {vals['AFP']}: 고수치")
        except: pass
        try:
            if vals.get("PIVKA-II") is not None and float(vals["PIVKA-II"]) > 40:
                add(f"PIVKA-II {vals['PIVKA-II']}: 상승")
        except: pass
    if cancer == "췌장암":
        try:
            if vals.get("CA19-9") is not None and float(vals["CA19-9"]) > 37:
                add(f"CA 19-9 {vals['CA19-9']}: 상승")
        except: pass
        for k, th in [("Amylase",100),("Lipase",60)]:
            try:
                if vals.get(k) is not None and float(vals[k]) > th:
                    add(f"{k} {vals[k]}: 상승 (췌장염/담도 병변 감별)")
            except: pass
    if cancer == "육종(Sarcoma)":
        try:
            if vals.get("ALP") is not None and float(vals["ALP"]) > 120:
                add(f"ALP {vals['ALP']}: 상승 (골성 병변/전이 평가 참고)")
        except: pass
    return notes


# -------------- Helpers --------------
def entered(v):
    try:
        return v is not None and float(v) != 0
    except Exception:
        return False

def interpret_labs(l, extras):
    out=[]
    def add(s): out.append("- " + s)

    if entered(l.get("WBC")):
        add(f"WBC {l['WBC']}: " + ("낮음 → 감염 위험↑" if l["WBC"]<4 else "높음 → 감염/염증 가능" if l["WBC"]>10 else "정상"))
    if entered(l.get("Hb")):
        add(f"Hb {l['Hb']}: " + ("낮음 → 빈혈" if l["Hb"]<12 else "정상"))
    if entered(l.get("PLT")):
        add(f"혈소판 {l['PLT']}: " + ("낮음 → 출혈 위험" if l["PLT"]<150 else "정상"))
    if entered(l.get("ANC")):
        add(f"ANC {l['ANC']}: " + ("중증 감소(<500)" if l["ANC"]<500 else "감소(<1500)" if l["ANC"]<1500 else "정상"))
    if entered(l.get("Albumin")):
        add(f"Albumin {l['Albumin']}: " + ("낮음 → 영양/염증/간질환 가능" if l["Albumin"]<3.5 else "정상"))
    if entered(l.get("Glucose")):
        add(f"Glucose {l['Glucose']}: " + ("고혈당(≥200)" if l["Glucose"]>=200 else "저혈당(<70)" if l["Glucose"]<70 else "정상"))
    if entered(l.get("CRP")):
        add(f"CRP {l['CRP']}: " + ("상승 → 염증/감염 의심" if l["CRP"]>0.5 else "정상"))
    if entered(l.get("BUN")) and entered(l.get("Cr")) and l["Cr"]>0:
        ratio=l["BUN"]/l["Cr"]
        if ratio>20: add(f"BUN/Cr {ratio:.1f}: 탈수 의심")
        elif ratio<10: add(f"BUN/Cr {ratio:.1f}: 간질환/영양 고려")

    if extras.get("diuretic"):
        if entered(l.get("Na")) and l["Na"]<135:
            add("🧂 이뇨제 복용 중 저나트륨 → 어지럼/탈수 주의, 의사와 상의")
        if entered(l.get("K")) and l["K"]<3.5:
            add("🥔 이뇨제 복용 중 저칼륨 → 심부정맥/근력저하 주의, 칼륨 보충 식이 고려")
        if entered(l.get("Ca")) and l["Ca"]<8.5:
            add("🦴 이뇨제 복용 중 저칼슘 → 손저림/경련 주의")
    return out

def food_suggestions(l):
    foods=[]
    if entered(l.get("Albumin")) and l["Albumin"]<3.5: foods.append("알부민 낮음 → " + ", ".join(FOODS["Albumin_low"]))
    if entered(l.get("K")) and l["K"]<3.5: foods.append("칼륨 낮음 → " + ", ".join(FOODS["K_low"]))
    if entered(l.get("Hb")) and l["Hb"]<12: foods.append("Hb 낮음 → " + ", ".join(FOODS["Hb_low"]))
    if entered(l.get("Na")) and l["Na"]<135: foods.append("나트륨 낮음 → " + ", ".join(FOODS["Na_low"]))
    if entered(l.get("Ca")) and l["Ca"]<8.5: foods.append("칼슘 낮음 → " + ", ".join(FOODS["Ca_low"]))
    if entered(l.get("ANC")) and l["ANC"]<500:
        foods.append("🧼 호중구 감소: 생채소 금지, 익혀 섭취(전자레인지 30초 이상), 2시간 지난 음식 금지, 껍질 과일은 의사 상의.")
    foods.append("⚠️ 항암/백혈병 환자는 철분제는 반드시 주치의와 상의(비타민C 병용 시 흡수↑).")
    return foods

def summarize_meds(meds: dict):
    out=[]
    for k, v in meds.items():
        info = ANTICANCER.get(k)
        if info:
            line = f"• {k} ({info['alias']}): AE {', '.join(info['aes'])}"
            if info.get("warn"): line += f" | 주의: {', '.join(info['warn'])}"
            if info.get("ix"): line += f" | 상호작용: {', '.join(info['ix'])}"
            if k == "ARA-C" and isinstance(v, dict) and v.get("form"):
                line += f" | 제형: {v['form']}"
            out.append(line)
    return out

# -------------- UI --------------
st.divider()
st.header("1️⃣ 환자/암 정보")

col1, col2 = st.columns(2)
with col1:
    nickname = st.text_input("별명(저장/그래프용)", placeholder="예: 홍길동")
with col2:
    test_date = st.date_input("검사 날짜", value=date.today())

group = st.selectbox("암 그룹 선택", ["미선택/일반", "혈액암", "고형암"])
cancer = None
catalog = None
if group == "혈액암":
    cancer = st.selectbox("혈액암 종류", list(HEMATO.keys()))
    catalog = HEMATO[cancer]
elif group == "고형암":
    cancer = st.selectbox("고형암 종류", list(SOLID.keys()))
    catalog = SOLID[cancer]
else:
    st.info("암 그룹을 선택하면 해당 암종에 맞는 **항암제 목록과 주의 검사**가 자동 노출됩니다.")

if catalog:
    st.markdown(f"🧾 **암종류 노트:** {catalog['note']}")
    if catalog.get("extra_tests"):
        st.markdown("🔎 **추가 권장 검사:** " + ", ".join(catalog["extra_tests"]))

    # ===== Clickable sections under cancer info =====
    meds = {}
    extras = {}

    with st.expander("💊 항암제 선택", expanded=True):
        st.markdown("암종류에 맞는 항암제를 선택하세요.")
        med_list = list(catalog.get("drugs", []))
        if "ARA-C" in med_list:
            use = st.checkbox("ARA-C 사용")
            if use:
                meds["ARA-C"] = {
                    "form": st.selectbox("ARA-C 제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"]),
                    "dose": st.number_input("ARA-C 용량/일(임의 입력)", min_value=0.0, step=0.1),
                }
            med_list = [d for d in med_list if d != "ARA-C"]
        for key in med_list:
            if st.checkbox(f"{key} 사용"):
                meds[key] = {"dose_or_tabs": st.number_input(f"{key} 투여량/알약 개수(소수 허용)", min_value=0.0, step=0.1)}
        st.markdown("### 🧪 동반 약물")
        extras["diuretic"] = st.checkbox("이뇨제 복용 중")

    with st.expander("🧫 항생제 선택", expanded=False):
        st.caption("해당되는 항생제를 선택하세요.")
        extras.setdefault("abx", [])
        extras["abx"] = st.multiselect("사용 중인 항생제", list(ABX_GUIDE.keys()))
else:
    meds = {}
    extras = {}
    extras["diuretic"] = st.checkbox("이뇨제 복용 중 (암 미선택)")
    with st.expander("🧫 항생제 선택", expanded=False):
        extras["abx"] = st.multiselect("사용 중인 항생제", list(ABX_GUIDE.keys()))

st.divider()

st.header("2️⃣ 혈액 검사 수치 입력 (입력한 값만 해석)")

vals = {}

# Base panel
st.markdown("**기본 패널**")
for name in ORDER:
    if name == "CRP":
        vals[name] = st.number_input(f"{name}", step=0.01, format="%.2f")
    elif name in ("WBC","ANC","AST","ALT","LDH","BNP","Glucose"):
        vals[name] = st.number_input(f"{name}", step=1.0)
    else:
        vals[name] = st.number_input(f"{name}", step=0.1)

# Cancer-specific extra panel
extra_panel = get_extra_panel(group, cancer)
if extra_panel:
    st.markdown("**암종류 추가 패널**")
    for item in extra_panel:
        if item["type"] == "num":
            vals[item["key"]] = st.number_input(item["label"], step=item.get("step", 0.1))
        elif item.get("type") == "select":
            opts = item.get("options", ["Unknown","Negative","Positive"])
            vals[item["key"]] = st.selectbox(item["label"], opts)
        elif item.get("type") == "text":
            vals[item["key"]] = st.text_input(item["label"])
        else:
            # alias/no input
            pass

st.divider()
run = st.button("🔎 해석하기", use_container_width=True)


# -------------- RUN --------------
if run:
    st.subheader("📋 해석 결과")

    
lines = interpret_labs(vals, extras)
for line in lines: st.write(line)
# Cancer-specific interpretations
if cancer:
    cs = interpret_cancer_specific(cancer, vals, group)
    if cs:
        st.markdown("### 🧬 암종류 특이 해석")
        for c in cs: st.write(c)


    # 음식 가이드
    fs = food_suggestions(vals)
    if fs:
        st.markdown("### 🥗 음식 가이드")
        for f in fs: st.write("- " + f)

    # 항암제 요약
    if meds:
        st.markdown("### 💊 항암제 부작용·상호작용 요약")
        for line in summarize_meds(meds): st.write(line)

    # 항생제 요약
    if extras.get("abx"):
        st.markdown("### 🧪 항생제 주의 요약")
        for a in extras["abx"]: st.write(f"• {a}: {', '.join(ABX_GUIDE[a])}")

    # 발열 가이드
    st.markdown("### 🌡️ 발열 가이드")
    st.write(FEVER_GUIDE)

    # 보고서 (입력값만)
    buf = [f"# BloodMap 보고서 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n",
           f"- 제작자/자문: Hoya / GPT\n"]
    if group != "미선택/일반":
        buf.append(f"- 암 그룹/종류: {group} / {cancer}\n")
    else:
        buf.append(f"- 암 그룹/종류: 미선택\n")
    buf.append("- 검사일: {}\n".format(test_date.isoformat()))
    buf.append("\n## 입력 수치\n")
    for k in ORDER:
        v = vals[k]
        if entered(v):
            if k == "CRP":
                buf.append(f"- {k}: {v:.2f}\n")
            else:
                buf.append(f"- {k}: {v}\n")
    if meds:
        buf.append("\n## 항암제 요약\n")
        for line in summarize_meds(meds): buf.append(line + "\n")
    if extras.get("abx"):
        buf.append("\n## 항생제\n")
        for a in extras["abx"]: buf.append(f"- {a}: {', '.join(ABX_GUIDE[a])}\n")
    report_md = "".join(buf)

    st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"),
                       file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                       mime="text/markdown")

    # 저장 (별명 있을 때만)
    if nickname.strip():
        rec = {
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "group": group,
            "cancer": cancer,
            "labs": {k: vals[k] for k in ORDER if entered(vals[k])},
            "meds": meds,
            "extras": extras,
        }
        st.session_state.records.setdefault(nickname, []).append(rec)
        st.success("저장되었습니다. 아래 그래프에서 추이를 확인하세요.")
    else:
        st.info("별명을 입력하면 추이 그래프를 사용할 수 있어요.")

# -------------- GRAPHS --------------
st.markdown("---")
st.subheader("📈 별명별 추이 그래프 (WBC, Hb, PLT, CRP, ANC)")
if not HAS_PD:
    st.info("그래프는 pandas 설치 시 활성화됩니다. (pip install pandas)")
else:
    if st.session_state.records:
        sel = st.selectbox("별명 선택", sorted(st.session_state.records.keys()))
        rows = st.session_state.records.get(sel, [])
        if rows:
            data = [{"ts": r["ts"], **{k: r["labs"].get(k) for k in ["WBC","Hb","PLT","CRP","ANC"]}} for r in rows]
            df = pd.DataFrame(data).set_index("ts")
            st.line_chart(df.dropna(how="all"))
        else:
            st.info("선택한 별명의 저장 기록이 없습니다.")
    else:
        st.info("아직 저장된 기록이 없습니다.")

st.caption("✅ 모바일/PC 모두 한 줄 한 줄 **세로 정렬** 고정. CRP는 0.01 단위로 입력됩니다.")

