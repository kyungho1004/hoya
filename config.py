
# -*- coding: utf-8 -*-
APP_TITLE   = "🩸 피수치 가이드 (v3.14 · 안정화)"
PAGE_TITLE  = "피수치 가이드 by Hoya"
MADE_BY     = "제작/자문: **Hoya/GPT**"
CAFE_LINK_MD= "[피수치 가이드 공식카페](https://cafe.naver.com/bloodmap)"
FOOTER_CAFE = "공식 카페에서 최신 안내 및 업데이트 확인 가능"
DISCLAIMER  = "이 도구는 교육/보조 목적이며, 모든 의사결정은 반드시 담당 의료진의 판단을 따르세요."

# Label constants
LBL_WBC = "WBC(백혈구)"; LBL_Hb  = "Hb(적혈구)"; LBL_PLT = "PLT(혈소판)"; LBL_ANC = "ANC(호중구,면역력)"
LBL_Ca  = "Ca(칼슘)";    LBL_P   = "P(인)";        LBL_Na = "Na(소디움)";  LBL_K   = "K(포타슘)"
LBL_Alb = "Albumin(알부민)"; LBL_Glu = "Glucose(혈당)"; LBL_TP  = "Total Protein(총단백)"
LBL_AST = "AST"; LBL_ALT = "ALT"; LBL_LDH = "LDH"; LBL_CRP = "CRP(염증수치)"
LBL_Cr  = "Creatinine(크레아티닌)"; LBL_UA  = "Uric Acid(요산)"; LBL_TB = "Total Bilirubin(총빌리루빈)"
LBL_BUN = "BUN"; LBL_BNP = "BNP"

ORDER = [
    LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC,
    LBL_Ca, LBL_P, LBL_Na, LBL_K, LBL_Alb,
    LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH,
    LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP
]

FEVER_GUIDE = (
    "🌡️ **발열 가이드**\n"
    "- 38.0~38.5℃: 해열제 복용/수분 보충, 경과 관찰\n"
    "- 38.5℃ 이상: 병원 연락 권고\n"
    "- 39.0℃ 이상: 즉시 병원 방문 권고\n"
)

# PDF fonts (NanumGothic 권장) — /fonts 또는 /bloodmap_app/fonts 안에 두면 됨
FONT_PATH_REG = "fonts/NanumGothic.ttf"
FONT_PATH_B   = "fonts/NanumGothicBold.ttf"
FONT_PATH_XB  = "fonts/NanumGothicExtraBold.ttf"
