
from datetime import datetime, date
import os
import streamlit as st

# ===== Optional deps =====
try:
    import pandas as pd
    HAS_PD = True
except Exception:
    HAS_PD = False

# ===== Page config =====
st.set_page_config(page_title="피수치 가이드 by Hoya", layout="centered")
st.title("🩸 피수치 가이드  (v3.12-labels / 암종별 약제 + 표적치료 포함)")
st.markdown("👤 **제작자: Hoya / 자문: 호야/GPT** · 📅 {} 기준".format(date.today().isoformat()))
st.markdown("[📌 **피수치 가이드 공식카페 바로가기**](https://cafe.naver.com/bloodmap)")
st.caption("✅ 직접 타이핑 입력 · 모바일 줄꼬임 방지 · PC 표 모드 · 암별/소아/희귀암 패널 + 소아 감염질환 테이블")

if "records" not in st.session_state:
    st.session_state.records = {}

# ---- Label constants (Korean-friendly) ----
LBL_WBC = "WBC(백혈구)"
LBL_Hb = "Hb(적혈구)"
LBL_PLT = "PLT(혈소판)"
LBL_ANC = "ANC(호중구,면역력)"
LBL_Ca = "Ca(칼슘)"
LBL_P = "P(인)"
LBL_Na = "Na(나트륨)"
LBL_K = "K(포타슘)"
LBL_Alb = "Albumin(알부민)"
LBL_Glu = "Glucose(혈당)"
LBL_TP = "Total Protein(총단백질)"
LBL_AST = "AST(간수치)"
LBL_ALT = "ALT(간세포수치)"
LBL_LDH = "LDH(유산탈수효소)"
LBL_CRP = "CRP(염증수치)"
LBL_Cr = "Cr(신장수치)"
LBL_UA = "UA(요산수치)"
LBL_TB = "TB(총빌리루빈)"
LBL_BUN = "BUN(신장수치)"
LBL_BNP = "BNP(심장척도)"

ORDER = [
    LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K, LBL_Alb,
    LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA,
    LBL_TB, LBL_BUN, LBL_BNP
]

DISCLAIMER = (
    "※ 본 자료는 보호자의 이해를 돕기 위한 참고용 정보입니다. "
    "진단 및 처방은 하지 않으며, 모든 의학적 판단은 의료진의 권한입니다. "
    "개발자는 이에 대한 판단·조치에 일절 관여하지 않으며, 책임지지 않습니다."
)

# ===== Drug dictionaries (including targeted/IO) =====
ANTICANCER = {
    "6-MP":{"alias":"6-머캅토퓨린","aes":["골수억제","간수치 상승","구내염","오심"],
            "warn":["황달/진한 소변 시 진료","감염 징후 즉시 연락"],
            "ix":["알로푸리놀 병용 감량 가능","와파린 효과 변동"]},
    "MTX":{"alias":"메토트렉세이트","aes":["골수억제","간독성","신독성","구내염","광과민"],
           "warn":["탈수 시 독성↑","고용량 후 류코보린"],
           "ix":["NSAIDs/TMP-SMX 병용 독성↑","일부 PPI 상호작용"]},
    "ATRA":{"alias":"트레티노인(베사노이드)","aes":["분화증후군","발열","피부/점막 건조","두통"],
            "warn":["분화증후군 의심 시 즉시 병원"],
            "ix":["테트라사이클린계와 가성뇌종양"]},
    "ARA-C":{"alias":"시타라빈","aes":["골수억제","발열","구내염","(HDAC) 신경독성"],
             "warn":["HDAC 시 신경증상 즉시 보고"],"ix":["효소유도제 상호작용"]},
    "G-CSF":{"alias":"그라신","aes":["골통/근육통","주사부위 반응","드물게 비장비대"],
             "warn":["좌상복부 통증 시 평가"],"ix":[]},
    "Hydroxyurea":{"alias":"하이드록시우레아","aes":["골수억제","피부색소침착","궤양"],
                   "warn":["임신 회피"],"ix":[]},
    "Daunorubicin":{"alias":"도우노루비신","aes":["골수억제","심독성","오심/구토","점막염"],
                    "warn":["누적용량 심기능"],"ix":["심독성↑ 병용 주의"]},
    "Idarubicin":{"alias":"이달루비신","aes":["골수억제","심독성","점막염"],
                  "warn":["심기능"],"ix":[]},
    "Mitoxantrone":{"alias":"미토잔트론","aes":["골수억제","심독성","청록색 소변"],
                    "warn":["심기능"],"ix":[]},
    "Cyclophosphamide":{"alias":"사이클로포스파미드","aes":["골수억제","출혈성 방광염","탈모"],
                        "warn":["수분섭취·메스나"],"ix":["CYP 상호작용"]},
    "Etoposide":{"alias":"에토포사이드","aes":["골수억제","저혈압(주입)"],"warn":[],"ix":[]},
    "Topotecan":{"alias":"토포테칸","aes":["골수억제","설사"],"warn":[],"ix":[]},
    "Fludarabine":{"alias":"플루다라빈","aes":["면역억제","감염 위험↑","혈구감소"],
                   "warn":["PCP 예방 고려"],"ix":[]},
    "Vincristine":{"alias":"빈크리스틴","aes":["말초신경병증","변비/장폐색"],
                   "warn":["IT 투여 금지"],"ix":["CYP3A 상호작용"]},
    # Solid-tumor common
    "Paclitaxel":{"alias":"파클리탁셀","aes":["말초신경병증","호중구감소"],
                  "warn":["과민반응 예방(스테로이드 등)"],"ix":[]},
    "Docetaxel":{"alias":"도세탁셀","aes":["체액저류","호중구감소"],
                 "warn":["전처치 스테로이드"],"ix":[]},
    "Doxorubicin":{"alias":"독소루비신","aes":["심독성","탈모","구내염"],
                   "warn":["누적용량 주의"],"ix":[]},
    "Carboplatin":{"alias":"카보플라틴","aes":["혈구감소","신독성(경미)"],
                   "warn":["Calvert 공식"],"ix":[]},
    "Cisplatin":{"alias":"시스플라틴","aes":["신독성","오심/구토","이독성"],
                 "warn":["수분/항구토제"],"ix":[]},
    "Oxaliplatin":{"alias":"옥살리플라틴","aes":["말초신경병증(냉감 유발)"],
                   "warn":["찬음식/찬바람 주의"],"ix":[]},
    "5-FU":{"alias":"플루오로우라실","aes":["점막염","설사","수족증후군"],
            "warn":["DPD 결핍 주의"],"ix":[]},
    "Capecitabine":{"alias":"카페시타빈","aes":["수족증후군","설사"],
                    "warn":["신기능 따라 감량"],"ix":[]},
    "Gemcitabine":{"alias":"젬시타빈","aes":["혈구감소","발열"],"warn":[],"ix":[]},
    "Pemetrexed":{"alias":"페메트렉시드","aes":["골수억제","피부발진"],
                   "warn":["엽산/비타민B12 보충"],"ix":[]},
    "Irinotecan":{"alias":"이리노테칸","aes":["급성/지연성 설사"],
                  "warn":["로페라미드 지침"],"ix":[]},
    "Trastuzumab":{"alias":"트라스투주맙","aes":["심기능저하"],
                   "warn":["좌심실 기능 모니터"],"ix":[]},
    "Ifosfamide":{"alias":"이포스파미드","aes":["골수억제","신경독성","출혈성 방광염"],
                  "warn":["메스나 병용/수분섭취"],"ix":[]},
    # Hematologic-specific
    "Imatinib":{"alias":"이마티닙(TKI)","aes":["부종","근육통","피로","간수치 상승"],
                "warn":["간기능/혈당 모니터"],"ix":["CYP3A4 상호작용"]},
    "Dasatinib":{"alias":"다사티닙(TKI)","aes":["혈소판감소","흉막/심막 삼출","설사"],
                 "warn":["호흡곤란/흉통 시 평가"],"ix":["CYP3A4 상호작용"]},
    "Nilotinib":{"alias":"닐로티닙(TKI)","aes":["QT 연장","고혈당","간수치 상승"],
                 "warn":["공복 복용/ECG 모니터"],"ix":["CYP3A4 상호작용"]},
    "Rituximab":{"alias":"리툭시맙","aes":["주입반응","감염 위험","HBV 재활성"],
                 "warn":["HBV 스크리닝/모니터"],"ix":[]},
    "Asparaginase":{"alias":"아스파라기나제(PEG)","aes":["췌장염","혈전","간독성","과민반응"],
                    "warn":["복통/구토 시 평가"],"ix":[]},
    "ATO":{"alias":"비소 트리옥사이드(ATO)","aes":["QT 연장","분화증후군","전해질 이상"],
           "warn":["ECG/전해질 모니터"],"ix":[]},
    # Targeted / IO (일부 축약)
    "Bevacizumab":{"alias":"베바시주맙(anti-VEGF)","aes":["고혈압","단백뇨","출혈/천공(드묾)"],"warn":["수술 전후 투여 중지"],"ix":[]},
    "Cetuximab":{"alias":"세툭시맙(EGFR)","aes":["피부발진","저Mg혈증"],"warn":["KRAS/NRAS WT에서만 효과"],"ix":[]},
    "Panitumumab":{"alias":"파니투무맙(EGFR)","aes":["피부발진","저Mg혈증"],"warn":["RAS WT 필요"],"ix":[]},
    "Gefitinib":{"alias":"게피티닙(EGFR TKI)","aes":["간수치↑","설사","발진"],"warn":["간기능 모니터"],"ix":["CYP3A4 상호작용"]},
    "Erlotinib":{"alias":"얼로티닙(EGFR TKI)","aes":["발진","설사"],"warn":["흡연 시 노출↓"],"ix":["CYP3A4 상호작용"]},
    "Osimertinib":{"alias":"오시머티닙(EGFR T790M/1L)","aes":["QT 연장","간수치↑"],"warn":["ECG/간기능"],"ix":[]},
    "Alectinib":{"alias":"알렉티닙(ALK TKI)","aes":["변비","근육통","간수치↑"],"warn":["CPK/간기능"],"ix":[]},
    "Sunitinib":{"alias":"수니티닙(TKI)","aes":["고혈압","피로","손발증후군"],"warn":["혈압/갑상선"],"ix":[]},
    "Pazopanib":{"alias":"파조파닙(TKI)","aes":["간독성","고혈압"],"warn":["간기능"],"ix":[]},
    "Sorafenib":{"alias":"소라페닙(TKI)","aes":["손발증후군","설사","고혈압"],"warn":["피부/혈압 모니터"],"ix":[]},
    "Lenvatinib":{"alias":"렌바티닙(TKI)","aes":["고혈압","단백뇨"],"warn":["혈압/단백뇨 모니터"],"ix":[]},
    "Olaparib":{"alias":"올라파립(PARP)","aes":["빈혈","피로","오심"],"warn":["혈구감소 모니터"],"ix":[]},
    "Enzalutamide":{"alias":"엔잘루타마이드(AR)","aes":["피로","고혈압"],"warn":["경련 위험 드묾"],"ix":["CYP 상호작용"]},
    "Abiraterone":{"alias":"아비라테론(AR)","aes":["저K혈증","고혈압","간수치↑"],"warn":["프레드니손 병용"],"ix":["CYP 상호작용"]},
    "Cabazitaxel":{"alias":"카바지탁셀","aes":["호중구감소","설사"],"warn":["G-CSF 고려"],"ix":[]},
    "Temozolomide":{"alias":"테모졸로마이드","aes":["골수억제","오심"],"warn":["PCP 예방 고려(고용량)"],"ix":[]},
    "Lomustine":{"alias":"로무스틴(CCNU)","aes":["골수억제(지연)"],"warn":["간/혈구 모니터"],"ix":[]},
    "Pertuzumab":{"alias":"퍼투주맙(HER2)","aes":["설사","피로"],"warn":["심기능"],"ix":[]},
    "Regorafenib":{"alias":"레고라페닙(TKI)","aes":["손발증후군","고혈압"],"warn":["혈압/간기능"],"ix":[]},
    "Atezolizumab":{"alias":"아테졸리주맙(PD-L1)","aes":["면역관련 이상반응"],"warn":["면역독성 교육"],"ix":[]},
    "Mitotane":{"alias":"미토테인","aes":["피로","어지럼","구토"],"warn":["호르몬 보충 필요 가능"],"ix":[]},
    "Dacarbazine":{"alias":"다카바진","aes":["골수억제","오심"],"warn":[],"ix":[]},
    "Pembrolizumab":{"alias":"펨브롤리주맙(PD-1)","aes":["면역관련 이상반응(피부, 갑상선, 폐렴, 대장염 등)"],
                     "warn":["증상 발생 시 스테로이드 치료 고려, 지연발현 가능"],"ix":[]},
    "Nivolumab":{"alias":"니볼루맙(PD-1)","aes":["면역관련 이상반응"],"warn":["면역독성 교육/모니터"],"ix":[]},
    "Avelumab":{"alias":"아벨루맙(PD-L1)", "aes":["면역관련 이상반응"], "warn":["면역독성 교육"], "ix":[]},
    "Durvalumab":{"alias":"더발루맙(PD-L1)", "aes":["면역관련 이상반응"], "warn":["면역독성 교육"], "ix":[]},
    "Ipilimumab":{"alias":"이필리무맙(CTLA-4)", "aes":["면역관련 이상반응↑"], "warn":["고용량 스테로이드 필요 가능"], "ix":[]},
    "Tremelimumab":{"alias":"트렘엘리무맙(CTLA-4)", "aes":["면역관련 이상반응↑"], "warn":["간독성 주의"], "ix":[]},
    "Cemiplimab":{"alias":"세미플리맙(PD-1)", "aes":["면역관련 이상반응"], "warn":["면역독성 교육"], "ix":[]},
    "Dostarlimab":{"alias":"도스타를리맙(PD-1)", "aes":["면역관련 이상반응"], "warn":["MSI-H/서로표지 확인"], "ix":[]},
    "Ado-trastuzumab emtansine (T-DM1)":{"alias":"T-DM1(카드실라)", "aes":["혈소판감소", "간독성"], "warn":["심기능/간기능"], "ix":[]},
    "Trastuzumab deruxtecan (T-DXd)":{"alias":"T-DXd", "aes":["간질성폐질환(ILD)", "오심"], "warn":["호흡곤란시 즉시 중단"], "ix":[]},
    "Lapatinib":{"alias":"라파티닙(HER2 TKI)", "aes":["설사", "발진"], "warn":["간기능"], "ix":[]},
    "Tucatinib":{"alias":"투카티닙(HER2 TKI)", "aes":["간수치↑", "설사"], "warn":["간기능"], "ix":[]},
    "Dabrafenib":{"alias":"다브라페닙(BRAF)", "aes":["발열", "피부발진"], "warn":["병용 트라메티닙"], "ix":[]},
    "Trametinib":{"alias":"트라메티닙(MEK)", "aes":["심기능저하", "피부발진"], "warn":["심초음파"], "ix":[]},
    "Encorafenib":{"alias":"엔코라페닙(BRAF)", "aes":["피부독성", "관절통"], "warn":[], "ix":[]},
    "Binimetinib":{"alias":"비니메티닙(MEK)", "aes":["망막장액성", "CK 상승"], "warn":[], "ix":[]},
    "Sotorasib":{"alias":"소토라십(KRAS G12C)", "aes":["간수치↑", "설사"], "warn":["CYP 상호작용"], "ix":[]},
    "Adagrasib":{"alias":"아다가라십(KRAS G12C)", "aes":["구역/설사", "QT 연장"], "warn":[], "ix":[]},
    "Selpercatinib":{"alias":"셀퍼카티닙(RET)", "aes":["고혈압", "간수치↑"], "warn":[], "ix":[]},
    "Pralsetinib":{"alias":"프랄세티닙(RET)", "aes":["간수치↑", "고혈압"], "warn":[], "ix":[]},
    "Crizotinib":{"alias":"크리조티닙(ALK/ROS1)", "aes":["시야장애", "간수치↑"], "warn":[], "ix":[]},
    "Lorlatinib":{"alias":"롤라티닙(ALK)", "aes":["지질이상", "CNS 증상"], "warn":["지질모니터"], "ix":[]},
    "Capmatinib":{"alias":"캡마티닙(MET)", "aes":["간수치↑", "말초부종"], "warn":[], "ix":[]},
    "Tepotinib":{"alias":"테포티닙(MET)", "aes":["부종", "간수치↑"], "warn":[], "ix":[]},
    "Larotrectinib":{"alias":"라로트렉티닙(NTRK)", "aes":["피로", "어지럼"], "warn":[], "ix":[]},
    "Entrectinib":{"alias":"엔트렉티닙(NTRK/ROS1)", "aes":["어지럼", "체중증가"], "warn":[], "ix":[]},
    "Axitinib":{"alias":"악시티닙(TKI)", "aes":["고혈압", "설사"], "warn":["혈압모니터"], "ix":[]},
    "Cabozantinib":{"alias":"카보잔티닙(TKI)", "aes":["손발증후군", "설사"], "warn":["간기능"], "ix":[]},
    "Everolimus":{"alias":"에베롤리무스(mTOR)", "aes":["구내염", "고혈당"], "warn":["혈당/지질"], "ix":[]},
    "Ramucirumab":{"alias":"라무시루맙(anti-VEGFR2)", "aes":["고혈압", "출혈"], "warn":[], "ix":[]},
    "Niraparib":{"alias":"니라파립(PARP)", "aes":["혈소판감소", "피로"], "warn":["혈구감소 모니터"], "ix":[]},
    "Rucaparib":{"alias":"루카파립(PARP)", "aes":["간수치↑", "피로"], "warn":["간기능"], "ix":[]},
    "Talazoparib":{"alias":"탈라조파립(PARP)", "aes":["빈혈", "피로"], "warn":["혈구감소 모니터"], "ix":[]},
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

# ===== Pediatrics (everyday/respiratory) =====
PED_TOPICS = ["RSV/모세기관지염","영아 중이염","크룹","구토·설사(탈수)","열경련"]
PED_INPUTS_INFO = (
    "다음 공통 입력은 위험도 배너 산출에 사용됩니다.\n"
    "- 나이(개월), 체온(℃), 호흡수(/분), 산소포화도(%), 24시간 소변 횟수, "
    "함몰/견흔(0/1), 콧벌렁임(0/1), 무호흡(0/1)"
)

# ===== Pediatrics (infectious diseases) =====
PED_INFECT = {
    "RSV(세포융합바이러스)": {"핵심":"기침, 쌕쌕거림, 발열","진단":"항원검사 또는 PCR","특징":"모세기관지염 흔함, 겨울철 유행"},
    "Adenovirus(아데노바이러스)": {"핵심":"고열, 결막염, 설사","진단":"PCR","특징":"장염 + 눈충혈 동반 많음"},
    "Rotavirus(로타바이러스)": {"핵심":"구토, 물설사","진단":"항원검사","특징":"탈수 위험 가장 큼"},
    "Parainfluenza (파라인플루엔자)": {"핵심":"크룹, 쉰목소리","진단":"PCR","특징":"개짖는 기침 특징적"},
    "HFMD (수족구병)": {"핵심":"입안 궤양, 손발 수포","진단":"임상진단","특징":"전염성 매우 강함"},
    "Influenza (독감)": {"핵심":"고열, 근육통","진단":"신속검사 또는 PCR","특징":"해열제 효과 적음"},
    "COVID-19 (코로나)": {"핵심":"발열, 기침, 무증상도 흔함","진단":"PCR","특징":"아직도 드물게 유행"}
}

# ===== Cancer-specific panels =====
CANCER_SPECIFIC = {
    # Blood cancers
    "AML": [("PT","PT","sec",1),("aPTT","aPTT","sec",1),("Fibrinogen","Fibrinogen","mg/dL",1),
            ("D-dimer","D-dimer","µg/mL FEU",2),("Blasts%","말초 혈액 blasts","%",0)],
    "APL": [("PT","PT","sec",1),("aPTT","aPTT","sec",1),("Fibrinogen","Fibrinogen","mg/dL",1),
            ("D-dimer","D-dimer","µg/mL FEU",2),("DIC Score","DIC Score","pt",0)],
    "ALL": [("PT","PT","sec",1),("aPTT","aPTT","sec",1),("CNS Sx","CNS 증상 여부(0/1)","",0)],
    "CML": [("BCR-ABL PCR","BCR-ABL PCR","%IS",2),("Basophil%","기저호산구(Baso) 비율","%",1)],
    "CLL": [("IgG","면역글로불린 IgG","mg/dL",0),("IgA","면역글로불린 IgA","mg/dL",0),
            ("IgM","면역글로불린 IgM","mg/dL",0)],

    # Pediatric cancers
    "Neuroblastoma": [("VMA","요 VMA","mg/gCr",2),("HVA","요 HVA","mg/gCr",2),("MYCN","MYCN 증폭(0/1)","",0)],
    "Wilms tumor": [("Abd U/S","복부초음파 소견 점수","pt",0),("BP","혈압 백분위수(%)","%",0)],

    # Solid cancers (common)
    "폐암(Lung cancer)": [("CEA","CEA","ng/mL",1),("CYFRA 21-1","CYFRA 21-1","ng/mL",1),("NSE","Neuron-specific enolase","ng/mL",1), "Pembrolizumab", "Nivolumab"],
    "유방암(Breast cancer)": [("CA15-3","CA15-3","U/mL",1),("CEA","CEA","ng/mL",1),("HER2","HER2","IHC/FISH",0),("ER/PR","ER/PR","%",0)],
    "위암(Gastric cancer)": [("CEA","CEA","ng/mL",1),("CA72-4","CA72-4","U/mL",1),("CA19-9","CA19-9","U/mL",1), "Pembrolizumab"],
    "대장암(Cololoractal cancer)": [("CEA","CEA","ng/mL",1),("CA19-9","CA19-9","U/mL",1), "Pembrolizumab"],
    "간암(HCC)": [("AFP","AFP","ng/mL",1),("PIVKA-II","PIVKA-II(DCP)","mAU/mL",0)],
    "췌장암(Pancreatic cancer)": [("CA19-9","CA19-9","U/mL",1),("CEA","CEA","ng/mL",1)],
    "담도암(Cholangiocarcinoma)": [("CA19-9","CA19-9","U/mL",1),("CEA","CEA","ng/mL",1)],
    "자궁내막암(Endometrial cancer)": [("CA125","CA125","U/mL",1),("HE4","HE4","pmol/L",1)],
    "구강암/후두암": [("SCC Ag","SCC antigen","ng/mL",1),("CYFRA 21-1","CYFRA 21-1","ng/mL",1)],
    "피부암(흑색종)": [("S100","S100","µg/L",1),("LDH","LDH","U/L",0), "Nivolumab", "Pembrolizumab"],
    "육종(Sarcoma)": [("ALP","ALP","U/L",0),("CK","CK","U/L",0)],
    "신장암(RCC)": [("CEA","CEA","ng/mL",1),("LDH","LDH","U/L",0), "Nivolumab", "Pembrolizumab"],
    "갑상선암": [("Tg","Thyroglobulin","ng/mL",1),("Anti-Tg Ab","Anti-Tg Ab","IU/mL",1)],
    "난소암": [("CA125","CA125","U/mL",1),("HE4","HE4","pmol/L",1)],
    "자궁경부암": [("SCC Ag","SCC antigen","ng/mL",1)],
    "전립선암": [("PSA","PSA","ng/mL",1)],
    "뇌종양(Glioma)": [("IDH1/2","IDH1/2 mutation","0/1",0),("MGMT","MGMT methylation","0/1",0)],
    "식도암": [("SCC Ag","SCC antigen","ng/mL",1),("CEA","CEA","ng/mL",1), "Nivolumab", "Pembrolizumab"],
    "방광암": [("NMP22","NMP22","U/mL",1),("UBC","UBC","µg/L",1), "Pembrolizumab", "Nivolumab"],

    # Rare cancers
    "담낭암(Gallbladder cancer)": [("CA19-9","CA19-9","U/mL",1),("CEA","CEA","ng/mL",1)],
    "부신암(Adrenal cancer)": [("Cortisol","Cortisol","µg/dL",1),("DHEA-S","DHEA-S","µg/dL",1)],
    "망막모세포종(Retinoblastoma)": [("RB1 mutation","RB1 mutation","0/1",0),("Fundus exam","망막검사 점수","pt",0)],
    "흉선종/흉선암(Thymoma/Thymic carcinoma)": [("AChR Ab","AChR 항체","titer",1),("LDH","LDH","U/L",0)],
    "신경내분비종양(NET)": [("Chromogranin A","CgA","ng/mL",1),("5-HIAA(urine)","5-HIAA(소변)","mg/24h",2)],
    "간모세포종(Hepatoblastoma)": [("AFP","AFP","ng/mL",1)],
    "비인두암(NPC)": [("EBV DNA","EBV DNA","IU/mL",0),("VCA IgA","VCA IgA","titer",1)],
    "GIST": [("KIT mutation","KIT mutation","0/1",0),("PDGFRA mutation","PDGFRA mutation","0/1",0)]
}

# ===== Regimen shorthand (labels) =====
REGIMENS = {
    "FOLFOX": {"설명": "5-FU + Leucovorin + Oxaliplatin (대장암/위암 등)"},
    "AC": {"설명": "Doxorubicin + Cyclophosphamide (유방암)"},
    "AC-T": {"설명": "AC 후 Paclitaxel/Docetaxel (유방암 표준)"},
    "TCHP": {"설명": "Docetaxel + Carboplatin + Trastuzumab + Pertuzumab (HER2 유방암)"},
    "T-DM1": {"설명": "Ado-trastuzumab emtansine (HER2 유방암)"},
    "T-DXd": {"설명": "Trastuzumab deruxtecan (HER2-low 포함)"},
    "mFOLFOX6": {"설명": "Modified FOLFOX6 (대장암 등)"},
    "XELOX": {"설명": "Capecitabine + Oxaliplatin (=CAPOX)"},
    "FLOT": {"설명": "5-FU + Leucovorin + Oxaliplatin + Docetaxel (위암)"},
    "GEMCIS": {"설명": "Gemcitabine + Cisplatin (담도/담낭암 표준)"},
    "GEMOX": {"설명": "Gemcitabine + Oxaliplatin (담도암)"},
    "GP": {"설명": "Gemcitabine + Cisplatin (비인두암)"},
    "PC": {"설명": "Pemetrexed + Cisplatin (비소세포폐암)"},
    "CARBO-TAXOL": {"설명": "Carboplatin + Paclitaxel (폐암/난소암 등)"},
    "GEMNAB": {"설명": "Gemcitabine + nab-Paclitaxel (췌장암)"},
    "FOLFIRI": {"설명": "5-FU + Leucovorin + Irinotecan (대장암)"},
    "FOLFIRINOX": {"설명": "5-FU + Leucovorin + Irinotecan + Oxaliplatin (췌장암)"},
    "CAPOX": {"설명": "Capecitabine + Oxaliplatin (대장암/위암)"}
}

# ===== Helpers =====
def _parse_numeric(text, default=0.0, as_int=False, decimals=None):
    if text is None:
        return default
    s = str(text).strip()
    if s == "":
        return default
    s = s.replace(",", "")
    try:
        v = float(s)
        if as_int:
            return int(v)
        if decimals is not None:
            return float(f"{v:.{decimals}f}")
        return v
    except Exception:
        return default

def num_input_generic(label, key, placeholder="", as_int=False, decimals=None):
    raw = st.text_input(label, key=key, placeholder=placeholder, label_visibility="visible")
    return _parse_numeric(raw, as_int=as_int, decimals=decimals)

def entered(v):
    try:
        return v is not None and float(v) != 0
    except Exception:
        return False

def _fmt(name, val):
    try:
        v = float(val)
    except Exception:
        return str(val)
    if name == LBL_CRP:
        return f"{v:.2f}"
    if name in (LBL_WBC, LBL_ANC, LBL_AST, LBL_ALT, LBL_LDH, LBL_BNP, LBL_Glu):
        return f"{int(v)}" if v.is_integer() else f"{v:.1f}"
    return f"{v:.1f}"

def interpret_labs(l, extras):
    out=[]
    def add(s): out.append("- " + s)
    if entered(l.get(LBL_WBC)):
        v=l[LBL_WBC]; add(f"{LBL_WBC} {_fmt(LBL_WBC, v)}: " + ("낮음 → 감염 위험↑" if v<4 else "높음 → 감염/염증 가능" if v>10 else "정상"))
    if entered(l.get(LBL_Hb)):
        v=l[LBL_Hb]; add(f"{LBL_Hb} {_fmt(LBL_Hb, v)}: " + ("낮음 → 빈혈" if v<12 else "정상"))
    if entered(l.get(LBL_PLT)):
        v=l[LBL_PLT]; add(f"{LBL_PLT} {_fmt(LBL_PLT, v)}: " + ("낮음 → 출혈 위험" if v<150 else "정상"))
    if entered(l.get(LBL_ANC)):
        v=l[LBL_ANC]; add(f"{LBL_ANC} {_fmt(LBL_ANC, v)}: " + ("중증 감소(<500)" if v<500 else "감소(<1500)" if v<1500 else "정상"))
    if entered(l.get(LBL_Alb)):
        v=l[LBL_Alb]; add(f"{LBL_Alb} {_fmt(LBL_Alb, v)}: " + ("낮음 → 영양/염증/간질환 가능" if v<3.5 else "정상"))
    if entered(l.get(LBL_Glu)):
        v=l[LBL_Glu]; add(f"{LBL_Glu} {_fmt(LBL_Glu, v)}: " + ("고혈당(≥200)" if v>=200 else "저혈당(<70)" if v<70 else "정상"))
    if entered(l.get(LBL_CRP)):
        v=l[LBL_CRP]; add(f"{LBL_CRP} {_fmt(LBL_CRP, v)}: " + ("상승 → 염증/감염 의심" if v>0.5 else "정상"))
    if entered(l.get(LBL_BUN)) and entered(l.get(LBL_Cr)) and l[LBL_Cr]>0:
        ratio=l[LBL_BUN]/l[LBL_Cr]
        if ratio>20: add(f"BUN/Cr {ratio:.1f}: 탈수 의심")
        elif ratio<10: add(f"BUN/Cr {ratio:.1f}: 간질환/영양 고려")
    if extras.get("diuretic_amt", 0) and extras["diuretic_amt"]>0:
        if entered(l.get(LBL_Na)) and l[LBL_Na]<135: add("🧂 이뇨제 복용 중 저나트륨 → 어지럼/탈수 주의, 의사와 상의")
        if entered(l.get(LBL_K)) and l[LBL_K]<3.5: add("🥔 이뇨제 복용 중 저칼륨 → 심전도/근력저하 주의, 칼륨 보충 식이 고려")
        if entered(l.get(LBL_Ca)) and l[LBL_Ca]<8.5: add("🦴 이뇨제 복용 중 저칼슘 → 손저림/경련 주의")
    return out

def food_suggestions(l):
    foods=[]
    if entered(l.get(LBL_Alb)) and l[LBL_Alb]<3.5: foods.append("알부민 낮음 → " + ", ".join(FOODS["Albumin_low"]))
    if entered(l.get(LBL_K)) and l[LBL_K]<3.5: foods.append("칼륨 낮음 → " + ", ".join(FOODS["K_low"]))
    if entered(l.get(LBL_Hb)) and l[LBL_Hb]<12: foods.append("Hb 낮음 → " + ", ".join(FOODS["Hb_low"]))
    if entered(l.get(LBL_Na)) and l[LBL_Na]<135: foods.append("나트륨 낮음 → " + ", ".join(FOODS["Na_low"]))
    if entered(l.get(LBL_Ca)) and l[LBL_Ca]<8.5: foods.append("칼슘 낮음 → " + ", ".join(FOODS["Ca_low"]))
    if entered(l.get(LBL_ANC)) and l[LBL_ANC]<500:
        foods.append("🧼 호중구 감소: 생채소 금지, 익혀 섭취, 2시간 지난 음식 금지, 껍질 과일은 의사 상의.")
    foods.append("⚠️ 항암/백혈병 환자는 철분제는 반드시 주치의와 상의(비타민C 병용 시 흡수↑).")
    return foods

def summarize_meds(meds: dict):
    out=[]
    for k, v in meds.items():
        info=ANTICANCER.get(k)
        if not info:
            continue
        line=f"• {k} ({info['alias']}): AE {', '.join(info['aes'])}"
        if info.get("warn"): line += f" | 주의: {', '.join(info['warn'])}"
        if info.get("ix"): line += f" | 상호작용: {', '.join(info['ix'])}"
        if k == "ARA-C" and isinstance(v, dict) and v.get("form"):
            line += f" | 제형: {v['form']}"
        out.append(line)
    return out

def abx_summary(abx_dict):
    lines=[]
    for k, amt in abx_dict.items():
        try: use=float(amt)
        except Exception: use=0.0
        if use>0:
            tip=", ".join(ABX_GUIDE.get(k, []))
            shown=f"{int(use)}" if float(use).is_integer() else f"{use:.1f}"
            lines.append(f"• {k}: {shown}  — 주의: {tip}")
    return lines

# ===== Pediatrics helpers =====
def _parse_num_ped(label, key, decimals=1, placeholder=""):
    raw = st.text_input(label, key=key, placeholder=placeholder)
    return _parse_numeric(raw, decimals=decimals)

def ped_risk_banner(age_m, temp_c, rr, spo2, urine_24h, retraction, nasal_flaring, apnea):
    danger=False; urgent=False; notes=[]
    if spo2 and spo2<92: danger=True; notes.append("SpO₂<92%")
    if apnea and apnea>=1: danger=True; notes.append("무호흡")
    if rr and ((age_m and age_m<=12 and rr>60) or (age_m and age_m>12 and rr>50)): urgent=True; notes.append("호흡수 상승")
    if temp_c and temp_c>=39.0: urgent=True; notes.append("고열")
    if retraction and retraction>=1: urgent=True; notes.append("흉곽 함몰")
    if nasal_flaring and nasal_flaring>=1: urgent=True; notes.append("콧벌렁임")
    if urine_24h and urine_24h < max(3, int(24*0.25)): urgent=True; notes.append("소변 감소")
    if danger: st.error("🚑 위급 신호: 즉시 병원/응급실 평가 권고 — " + ", ".join(notes))
    elif urgent: st.warning("⚠️ 주의: 빠른 진료 필요 — " + ", ".join(notes))
    else: st.success("🙂 가정관리 가능 신호(경과관찰). 상태 변화 시 즉시 의료진과 상의")

def ped_topic_tips(topic):
    if topic == "RSV/모세기관지염":
        st.markdown("""**가정관리 핵심**
- 비강흡인/가습, 수분 조금씩 자주. 수유량 ½ 이하로 떨어지면 진료 고려.
- 해열제는 체중기반으로, 과다복용 금지. 기침약은 영아에서 권장되지 않음.
**즉시 진료 신호**: 청색증, 무호흡, SpO₂<92%, 분당 RR>60(12개월 이하), 심한 함몰/콧벌렁임.
""")
    elif topic == "영아 중이염":
        st.markdown("""**가정관리**: 진통·해열, 24–48시간 경과관찰 가능(나이·중증도에 따라).
**경고**: 6개월 미만 고열, 심한 통증/고열 지속, 반복 구토 → 진료.
""")
    elif topic == "크룹":
        st.markdown("""**특징**: 개짖는소리 기침, 흡기때 쌕쌕.
**가정관리**: 안심시키기, 수분, 찬 공기 노출 단시간 도움이 될 수 있음.
**경고**: 휴식 시 흉곽 함몰, 침흘림/삼킴곤란, 청색증 → 응급.
""")
    elif topic == "구토·설사(탈수)":
        st.markdown("""**수분**: ORS 소량·자주(5–10분마다), 우유 일시 감량 고려.
**탈수 신호**: 소변 감소, 눈물 없음, 입 마름, 처짐.
**경고**: 피 섞인 변, 지속 구토로 수분 섭취 불가, 무기력/의식저하 → 진료.
""")
    elif topic == "열경련":
        st.markdown("""**대처**: 측위, 주위 치우기, 시간 측정. 억지로 입에 것 넣지 않기.
**진료 필요**: 5분 이상 지속, 반복, 국소신경학적 징후, 6개월 미만/5세 초과 첫 발생.
""")

# ===== UI 1) Patient / Mode =====
st.divider()
st.header("1️⃣ 환자/암·소아 정보")

c1, c2 = st.columns(2)
with c1:
    nickname = st.text_input("별명(저장/그래프용)", placeholder="예: 홍길동")
with c2:
    test_date = st.date_input("검사 날짜", value=date.today())

mode = st.selectbox("모드 선택", ["일반/암", "소아(일상/호흡기)", "소아(감염질환)"])

group = None
cancer = None
infect_sel = None
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
    if HAS_PD:
        _df = pd.DataFrame([{
            "핵심": PED_INFECT[infect_sel].get("핵심",""),
            "진단": PED_INFECT[infect_sel].get("진단",""),
            "특징": PED_INFECT[infect_sel].get("특징",""),
        }], index=[infect_sel])
        st.table(_df)
    else:
        st.markdown(f"**{infect_sel}**")
        st.write(f"- 핵심: {PED_INFECT[infect_sel].get('핵심','')}")
        st.write(f"- 진단: {PED_INFECT[infect_sel].get('진단','')}")
        st.write(f"- 특징: {PED_INFECT[infect_sel].get('특징','')}")

table_mode = st.checkbox("⚙️ PC용 표 모드(가로형)", help="모바일은 세로형 고정 → 줄꼬임 없음.")

# ===== Drugs & extras =====
meds = {}
extras = {}

if mode == "일반/암" and group and group != "미선택/일반" and cancer:
    st.markdown("### 💊 항암제 입력 (0=미사용, ATRA는 정수)")

    heme_by_cancer = {
        "AML": ["ARA-C","Daunorubicin","Idarubicin","Mitoxantrone","G-CSF","Cyclophosphamide",
                "Etoposide","Fludarabine","Hydroxyurea","MTX","ATRA"],
        "APL": ["ATRA","ATO","Idarubicin","Daunorubicin","ARA-C","G-CSF"],
        "ALL": ["Vincristine","Asparaginase","Daunorubicin","Cyclophosphamide","MTX","ARA-C","Topotecan","Etoposide"],
        "CML": ["Imatinib","Dasatinib","Nilotinib","Hydroxyurea"],
        "CLL": ["Fludarabine","Cyclophosphamide","Rituximab","Mitoxantrone"]
    }

    solid_by_cancer = {
        "폐암(Lung cancer)": ["Cisplatin","Carboplatin","Paclitaxel","Docetaxel","Gemcitabine","Pemetrexed",
                           "Gefitinib","Erlotinib","Osimertinib","Alectinib","Bevacizumab", "Durvalumab", "Crizotinib", "Lorlatinib", "Selpercatinib", "Pralsetinib", "Capmatinib", "Tepotinib", "Sotorasib", "Adagrasib", "Larotrectinib", "Entrectinib"],
        "유방암(Breast cancer)": ["Doxorubicin","Cyclophosphamide","Paclitaxel","Docetaxel","Trastuzumab","Pertuzumab", "Ado-trastuzumab emtansine (T-DM1)", "Trastuzumab deruxtecan (T-DXd)", "Lapatinib", "Tucatinib"],
        "위암(Gastric cancer)": ["Cisplatin","Oxaliplatin","5-FU","Capecitabine","Paclitaxel", "Ramucirumab", "Trastuzumab", "Pembrolizumab"],
        "대장암(Cololoractal cancer)": ["5-FU","Capecitabine","Oxaliplatin","Irinotecan","Bevacizumab","Cetuximab","Panitumumab", "Regorafenib", "Ramucirumab", "Pembrolizumab"],
        "간암(HCC)": ["Doxorubicin","Sorafenib","Lenvatinib","Atezolizumab","Bevacizumab", "Durvalumab", "Tremelimumab", "Ramucirumab"],
        "췌장암(Pancreatic cancer)": ["Gemcitabine","Oxaliplatin","Irinotecan","5-FU"],
        "담도암(Cholangiocarcinoma)": ["Gemcitabine","Cisplatin","Bevacizumab"],
        "자궁내막암(Endometrial cancer)": ["Carboplatin","Paclitaxel", "Dostarlimab"],
        "구강암/후두암": ["Cisplatin","5-FU","Docetaxel"],
        "피부암(흑색종)": ["Dacarbazine","Paclitaxel", "Ipilimumab", "Dabrafenib", "Trametinib", "Encorafenib", "Binimetinib", "Cemiplimab"],
        "육종(Sarcoma)": ["Doxorubicin","Ifosfamide","Pazopanib"],
        "신장암(RCC)": ["Sunitinib","Pazopanib","Bevacizumab", "Axitinib", "Cabozantinib", "Everolimus", "Ipilimumab", "Nivolumab", "Pembrolizumab"],
        "갑상선암": ["Lenvatinib","Sorafenib", "Selpercatinib", "Pralsetinib"],
        "난소암": ["Carboplatin","Paclitaxel","Bevacizumab","Olaparib", "Niraparib", "Rucaparib", "Talazoparib"],
        "자궁경부암": ["Cisplatin","Paclitaxel","Bevacizumab"],
        "전립선암": ["Docetaxel","Cabazitaxel","Abiraterone","Enzalutamide"],
        "뇌종양(Glioma)": ["Temozolomide","Lomustine","Bevacizumab"],
        "식도암": ["Cisplatin","5-FU","Paclitaxel", "Nivolumab", "Pembrolizumab", "Ramucirumab"],
        "방광암": ["Cisplatin","Gemcitabine","Bevacizumab", "Avelumab", "Durvalumab", "Pembrolizumab", "Nivolumab"]
    }

    rare_by_cancer = {
        "담낭암(Gallbladder cancer)": ["Gemcitabine","Cisplatin"],
        "부신암(Adrenal cancer)": ["Mitotane","Etoposide","Doxorubicin","Cisplatin"],
        "망막모세포종(Retinoblastoma)": ["Vincristine","Etoposide","Carboplatin"],
        "흉선종/흉선암(Thymoma/Thymic carcinoma)": ["Cyclophosphamide","Doxorubicin","Cisplatin"],
        "신경내분비종양(NET)": ["Etoposide","Cisplatin","Sunitinib", "Everolimus"],
        "간모세포종(Hepatoblastoma)": ["Cisplatin","Doxorubicin"],
        "비인두암(NPC)": ["Cisplatin","5-FU","Gemcitabine","Bevacizumab", "Nivolumab", "Pembrolizumab"],
        "GIST": ["Imatinib","Sunitinib","Regorafenib"]
    }

    default_drugs_by_group = {
        "혈액암": heme_by_cancer.get(cancer, []),
        "고형암": solid_by_cancer.get(cancer, []),
        "소아암": ["Cyclophosphamide","Ifosfamide","Doxorubicin","Vincristine","Etoposide","Carboplatin",
                 "Cisplatin","Topotecan","Irinotecan"],
        "희귀암": rare_by_cancer.get(cancer, [])
    }

    drug_list = list(dict.fromkeys(default_drugs_by_group.get(group, [])))
    regimen_choices = []
    if group in ["고형암","희귀암"]:
        regimen_choices = st.multiselect("레짐(선택사항)", list(REGIMENS.keys()), help="예: FOLFOX/FOLFIRI/FOLFIRINOX/CAPOX 등. 보고서에 이름과 간단 설명이 포함됩니다.")
    
    if "ARA-C" in drug_list:
        st.markdown("**ARA-C (시타라빈)**")
        ara_form = st.selectbox("제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"], key="ara_form")
        ara_dose = num_input_generic("용량/일(임의 입력, 0=미사용)", key="ara_dose", decimals=1, placeholder="예: 100")
        meds["ARA-C"] = {"form": ara_form, "dose": ara_dose} if ara_dose and ara_dose>0 else {}
        st.divider()
        drug_list.remove("ARA-C")

    for d in drug_list:
        alias = ANTICANCER.get(d,{}).get("alias","")
        if d == "ATRA":
            amt = num_input_generic(f"{d} ({alias}) - 캡슐 개수(정수, 0=미사용)", key=f"med_{d}", as_int=True, placeholder="예: 2")
        else:
            amt = num_input_generic(f"{d} ({alias}) - 용량/알약 개수(0=미사용)", key=f"med_{d}", decimals=1, placeholder="예: 1.5")
        try:
            if amt and float(amt)>0:
                meds[d] = {"dose_or_tabs": amt}
        except Exception:
            pass

st.markdown("### 🧪 항생제 입력 (0=미사용)")
extras["abx"] = {}
for abx in ["페니실린계","세팔로스포린계","마크롤라이드","플루오로퀴놀론",
            "카바페넴","TMP-SMX","메트로니다졸","반코마이신"]:
    extras["abx"][abx] = num_input_generic(f"{abx} - 복용/주입량 또는 횟수(0=미사용)", key=f"abx_{abx}", decimals=1, placeholder="예: 1")

st.markdown("### 💧 동반 약물/상태")
extras["diuretic_amt"] = num_input_generic("이뇨제(복용량/회/일, 0=미복용)", key="diuretic_amt", decimals=1, placeholder="예: 1")

# ===== UI 2) Inputs =====
st.divider()
if mode == "일반/암":
    st.header("2️⃣ 기본 혈액 검사 수치 (입력한 값만 해석)")
elif mode == "소아(일상/호흡기)":
    st.header("2️⃣ 소아 공통 입력")
else:
    st.header("2️⃣ (감염질환은 별도 수치 입력 없음)")

vals = {}

def render_inputs_vertical():
    st.markdown("**기본 패널**")
    for name in ORDER:
        if name == LBL_CRP:
            vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=2, placeholder="예: 0.12")
        elif name in (LBL_WBC, LBL_ANC, LBL_AST, LBL_ALT, LBL_LDH, LBL_BNP, LBL_Glu):
            vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=1, placeholder="예: 1200")
        else:
            vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=1, placeholder="예: 3.5")

def render_inputs_table():
    st.markdown("**기본 패널 (표 모드)**")
    left, right = st.columns(2)
    half = (len(ORDER)+1)//2
    with left:
        for name in ORDER[:half]:
            if name == LBL_CRP:
                vals[name] = num_input_generic(f"{name}", key=f"l_{name}", decimals=2, placeholder="예: 0.12")
            elif name in (LBL_WBC, LBL_ANC, LBL_AST, LBL_ALT, LBL_LDH, LBL_BNP, LBL_Glu):
                vals[name] = num_input_generic(f"{name}", key=f"l_{name}", decimals=1, placeholder="예: 1200")
            else:
                vals[name] = num_input_generic(f"{name}", key=f"l_{name}", decimals=1, placeholder="예: 3.5")
    with right:
        for name in ORDER[half:]:
            if name == LBL_CRP:
                vals[name] = num_input_generic(f"{name}", key=f"r_{name}", decimals=2, placeholder="예: 0.12")
            elif name in (LBL_WBC, LBL_ANC, LBL_AST, LBL_ALT, LBL_LDH, LBL_BNP, LBL_Glu):
                vals[name] = num_input_generic(f"{name}", key=f"r_{name}", decimals=1, placeholder="예: 1200")
            else:
                vals[name] = num_input_generic(f"{name}", key=f"r_{name}", decimals=1, placeholder="예: 3.5")

if mode == "일반/암":
    if st.checkbox("⚙️ PC용 표 모드(가로형)", help="모바일은 세로형 고정 → 줄꼬임 없음."):
        render_inputs_table()
    else:
        render_inputs_vertical()
elif mode == "소아(일상/호흡기)":
    age_m        = _parse_num_ped("나이(개월)", key="ped_age", decimals=0, placeholder="예: 18")
    temp_c       = _parse_num_ped("체온(℃)", key="ped_temp", decimals=1, placeholder="예: 38.2")
    rr           = _parse_num_ped("호흡수(/분)", key="ped_rr", decimals=0, placeholder="예: 42")
    spo2         = _parse_num_ped("산소포화도(%)", key="ped_spo2", decimals=0, placeholder="예: 96")
    urine_24h    = _parse_num_ped("24시간 소변 횟수", key="ped_u", decimals=0, placeholder="예: 6")
    retraction   = _parse_num_ped("흉곽 함몰(0/1)", key="ped_ret", decimals=0, placeholder="0 또는 1")
    nasal_flaring= _parse_num_ped("콧벌렁임(0/1)", key="ped_nf", decimals=0, placeholder="0 또는 1")
    apnea        = _parse_num_ped("무호흡(0/1)", key="ped_ap", decimals=0, placeholder="0 또는 1")

# ===== UI 3) Cancer-specific extras or Pediatric tips =====
extra_vals = {}
if mode == "일반/암" and group and group != "미선택/일반" and cancer:
    items = CANCER_SPECIFIC.get(cancer, [])
    if items:
        st.divider()
        st.header("3️⃣ 암별 디테일 수치")
        st.caption("해석은 주치의 판단을 따르며, 값 기록/공유를 돕기 위한 입력 영역입니다.")
        for it in items:
            if isinstance(it, tuple):
                key, label, unit, decs = it
                ph = f"예: {('0' if decs==0 else '0.'+('0'*decs))}" if decs is not None else ""
                val = num_input_generic(f"{label}" + (f" ({unit})" if unit else ""), key=f"extra_{key}", decimals=decs, placeholder=ph)
                extra_vals[key] = val
elif mode == "소아(일상/호흡기)":
    st.divider()
    st.header("3️⃣ 소아 생활 가이드")
    ped_topic_tips(ped_topic)
else:
    st.divider()
    st.header("3️⃣ 감염질환 요약")
    st.info("표는 위 선택창에서 자동 생성됩니다.")

# ===== Run =====
st.divider()
run = st.button("🔎 해석하기", use_container_width=True)

if run:
    st.subheader("📋 해석 결과")

    if mode == "일반/암":
        lines = interpret_labs(vals, extras)
        for line in lines: st.write(line)

        shown = [ (k, v) for k, v in (extra_vals or {}).items() if entered(v) ]
        if shown:
            st.markdown("### 🧬 암별 디테일 수치")
            for k, v in shown:
                st.write(f"- {k}: {v}")

        fs = food_suggestions(vals)
        if fs:
            st.markdown("### 🥗 음식 가이드")
            for f in fs: st.write("- " + f)
    elif mode == "소아(일상/호흡기)":
        ped_risk_banner(age_m, temp_c, rr, spo2, urine_24h, retraction, nasal_flaring, apnea)
    else:
        st.success("선택한 감염질환 요약을 보고서에 포함했습니다.")

    if 'meds' in locals() and meds:
        st.markdown("### 💊 항암제 부작용·상호작용 요약")
        for line in summarize_meds(meds): st.write(line)

    if extras.get("abx"):
        abx_lines = abx_summary(extras["abx"])
        if abx_lines:
            st.markdown("### 🧪 항생제 주의 요약")
            for l in abx_lines: st.write(l)

    st.markdown("### 🌡️ 발열 가이드")
    st.write(FEVER_GUIDE)

    buf = [f"# BloodMap 보고서 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n",
           f"- 제작자/자문: Hoya / GPT\n",
           "[피수치 가이드 공식카페](https://cafe.naver.com/bloodmap)\n"]
    if mode == "일반/암":
        if group != "미선택/일반":
            buf.append(f"- 암 그룹/종류: {group} / {cancer}\n")
        else:
            buf.append(f"- 암 그룹/종류: 미선택\n")
    elif mode == "소아(일상/호흡기)":
        buf.append(f"- 소아 주제: {ped_topic}\n")
    else:
        buf.append(f"- 소아 감염질환: {infect_sel}\n")
        info = PED_INFECT.get(infect_sel, {})
        buf.append("  - 핵심: " + info.get("핵심","") + "\n")
        buf.append("  - 진단: " + info.get("진단","") + "\n")
        buf.append("  - 특징: " + info.get("특징","") + "\n")
    buf.append("- 검사일: {}\n".format(test_date.isoformat()))
    try:
        if mode == "일반/암" and group in ["고형암","희귀암"] and 'regimen_choices' in locals() and regimen_choices:
            buf.append("\n## 레짐(요약)\n")
            for rname in regimen_choices:
                desc = REGIMENS.get(rname, {}).get("설명","")
                buf.append(f"- {rname}: {desc}\n")
    except Exception:
        pass

    if mode == "일반/암":
        buf.append("\n## 입력 수치(기본)\n")
        for k in ORDER:
            v = vals.get(k)
            if entered(v):
                if k == LBL_CRP: buf.append(f"- {k}: {float(v):.2f}\n")
                else: buf.append(f"- {k}: {_fmt(k, v)}\n")
        if extra_vals:
            buf.append("\n## 암별 디테일 수치\n")
            for k, v in extra_vals.items():
                if entered(v): buf.append(f"- {k}: {v}\n")
        if 'meds' in locals() and meds:
            buf.append("\n## 항암제 요약\n")
            for line in summarize_meds(meds): buf.append(line + "\n")
        _foods_for_report = food_suggestions(vals)
        if _foods_for_report:
            buf.append("\n## 음식 가이드\n")
            for f in _foods_for_report:
                buf.append("- " + f + "\n")
    elif mode == "소아(일상/호흡기)":
        buf.append("\n## 소아 공통 입력\n")
        def _ent(x):
            try: return x is not None and float(x)!=0
            except: return False
        if _ent(age_m): buf.append(f"- 나이(개월): {int(age_m)}\n")
        if _ent(temp_c): buf.append(f"- 체온: {float(temp_c):1.1f}℃\n")
        if _ent(rr): buf.append(f"- 호흡수: {int(rr)}/분\n")
        if _ent(spo2): buf.append(f"- SpO₂: {int(spo2)}%\n")
        if _ent(urine_24h): buf.append(f"- 24시간 소변 횟수: {int(urine_24h)}\n")
        if _ent(retraction): buf.append(f"- 흉곽 함몰: {int(retraction)}\n")
        if _ent(nasal_flaring): buf.append(f"- 콧벌렁임: {int(nasal_flaring)}\n")
        if _ent(apnea): buf.append(f"- 무호흡: {int(apnea)}\n")

    if extras.get("abx"):
        buf.append("\n## 항생제\n")
        for l in abx_summary(extras["abx"]): buf.append(l + "\n")

    buf.append("\n> " + DISCLAIMER + "\n")
    report_md = "".join(buf)

    # Downloads (PDF 비활성화)
    st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"),
                       file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                       mime="text/markdown")

    st.download_button("📝 보고서(.txt) 다운로드", data=report_md.encode("utf-8-sig"),
                       file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                       mime="text/plain")

    # Save session record
    if nickname and nickname.strip():
        rec = {
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": mode,
            "group": group,
            "cancer": cancer,
            "infect": infect_sel,
            "labs": {k: vals.get(k) for k in ORDER if entered(vals.get(k))},
            "extra": {k: v for k, v in (extra_vals or {}).items() if entered(v)},
            "meds": locals().get("meds", {}),
            "extras": extras,
        }
        st.session_state.records.setdefault(nickname, []).append(rec)
        st.success("저장되었습니다. 아래 그래프에서 추이를 확인하세요.")
    else:
        st.info("별명을 입력하면 추이 그래프를 사용할 수 있어요.")

# ===== Graphs =====
st.markdown("---")
st.subheader("📈 별명별 추이 그래프 (WBC, Hb, PLT, CRP, ANC)")
if not HAS_PD:
    st.info("그래프는 pandas 설치 시 활성화됩니다. (pip install pandas)")
else:
    if st.session_state.records:
        sel = st.selectbox("별명 선택", sorted(st.session_state.records.keys()))
        rows = st.session_state.records.get(sel, [])
        if rows:
            data = [ {"ts": r["ts"], **{k: r["labs"].get(k) for k in [LBL_WBC, LBL_Hb, LBL_PLT, LBL_CRP, LBL_ANC]}} for r in rows ]
            import pandas as pd
            df = pd.DataFrame(data).set_index("ts")
            st.line_chart(df.dropna(how="all"))
        else:
            st.info("선택한 별명의 저장 기록이 없습니다.")
    else:
        st.info("아직 저장된 기록이 없습니다.")

# ===== Sticky disclaimer =====
st.caption("📱 직접 타이핑 입력 / 모바일 줄꼬임 방지 / 암별·소아·희귀암 패널 + 감염질환 표 포함. 공식카페: https://cafe.naver.com/bloodmap")
st.markdown("> " + DISCLAIMER)
