# -*- coding: utf-8 -*-
import os

APP_TITLE = "🩸 피수치 가이드 v3.16"
PAGE_TITLE = "피수치 가이드 / BloodMap"
MADE_BY = "제작: Hoya/GPT · 자문: Hoya/GPT"
CAFE_LINK_MD = "🔗 **피수치 가이드 공식카페**: https://cafe.naver.com/bloodmap"
FOOTER_CAFE = "문제 발생 시 즉시 수정/삭제하겠습니다. 개인정보는 절대 수집하지 않습니다."
DISCLAIMER = "본 자료는 보호자의 이해를 돕기 위한 참고용 정보이며, 모든 의학적 판단은 의료진의 권한입니다."
FEVER_GUIDE = "체온 38.0~38.5℃: 해열제 복용 후 경과관찰 · 38.5℃ 이상: 병원 연락 권고 · 39.0℃ 이상: 즉시 병원/응급실 방문"

LBL_WBC = "WBC(백혈구, /µL)"; LBL_Hb="Hb(혈색소, g/dL)"; LBL_PLT="혈소판(PLT, /µL)"; LBL_ANC="ANC(호중구, /µL)"
LBL_Ca="Ca(칼슘, mg/dL)"; LBL_P="P(인, mg/dL)"; LBL_Na="Na(소디움, mmol/L)"; LBL_K="K(포타슘, mmol/L)"
LBL_Alb="Albumin(알부민, g/dL)"; LBL_Glu="Glucose(혈당, mg/dL)"; LBL_TP="Total Protein(총단백, g/dL)"
LBL_AST="AST(U/L)"; LBL_ALT="ALT(U/L)"; LBL_LDH="LDH(U/L)"; LBL_CRP="CRP(mg/dL)"
LBL_Cr="Creatinine(크레아티닌, mg/dL)"; LBL_UA="Uric Acid(요산, mg/dL)"; LBL_TB="Total Bilirubin(총빌리루빈, mg/dL)"
LBL_BUN="BUN(mg/dL)"; LBL_BNP="BNP(pg/mL)"

ORDER = [LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K, LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP]

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FONT_PATH_REG = os.path.join(BASE_DIR, "fonts", "NanumGothic-Regular.ttf")
FONT_PATH_B   = os.path.join(BASE_DIR, "fonts", "NanumGothic-Bold.ttf")
FONT_PATH_EB  = os.path.join(BASE_DIR, "fonts", "NanumGothic-ExtraBold.ttf")
