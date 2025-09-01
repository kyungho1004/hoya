
from datetime import date

APP_TITLE = "🩸 피수치 가이드  (v3.13 · 변화비교 · 스케줄표 · 계절 식재료 · ANC 장소별 가이드)"
PAGE_TITLE = "피수치 가이드 by Hoya (v3.13 · 변화비교/스케줄/계절식/ANC장소)"
MADE_BY = "👤 **제작자: Hoya / 자문: 호야/GPT** · 📅 {} 기준".format(date.today().isoformat())
CAFE_LINK_MD = "[📌 **피수치 가이드 공식카페 바로가기**](https://cafe.naver.com/bloodmap)"
FOOTER_CAFE = "📱 직접 타이핑 입력 / 모바일 줄꼬임 방지 / 암별·소아·희귀암 패널 + 감염질환 표 포함. 공식카페: https://cafe.naver.com/bloodmap"

DISCLAIMER = (
    "※ 본 자료는 보호자의 이해를 돕기 위한 참고용 정보입니다. "
    "진단 및 처방은 하지 않으며, 모든 의학적 판단은 의료진의 권한입니다. "
    "개발자는 이에 대한 판단·조치에 일절 관여하지 않으며, 책임지지 않습니다."
)

# ===== Label constants (Korean-friendly) =====
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

FONT_PATH_REG = "fonts/NanumGothic-Regular.ttf"
FONT_PATH_B   = "fonts/NanumGothic-Bold.ttf"
FONT_PATH_XB  = "fonts/NanumGothic-ExtraBold.ttf"

FEVER_GUIDE = "🌡️ 38.0~38.5℃ 해열제/경과, 38.5℃↑ 병원 연락, 39.0℃↑ 즉시 병원. (ANC<500 동반 발열=응급)"
