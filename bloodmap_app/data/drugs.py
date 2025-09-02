
ANTICANCER = {
    "Imatinib": {"alias":"글리벡","category":"CML","aes":["부종","근육통","피로"]},
    "Dasatinib": {"alias":"스프라이셀","category":"CML","aes":["혈소판감소","흉막삼출","호흡곤란"]},
    "Nilotinib": {"alias":"타시그나","category":"CML","aes":["QT연장","고혈당","간수치상승"]},
    "Gefitinib": {"alias":"이레사","category":"폐암(EGFR)","aes":["피부발진","설사","간수치상승"]},
    "Osimertinib": {"alias":"타그리소","category":"폐암(EGFR)","aes":["QT연장","심근염 드묾","설사"]},
    "Trastuzumab": {"alias":"허셉틴","category":"유방암(HER2)","aes":["심기능저하","주입반응"]},
    "Bevacizumab": {"alias":"아바스틴","category":"고형암(혈관)","aes":["출혈","고혈압","상처치유지연"]},
}
for k,v in list(ANTICANCER.items()):
    v.setdefault("category","기타")

ABX_GUIDE = {
    "amoxicillin": {"class":"beta_lactam","alias":"아목사","notes":["발진","설사"]},
    "amoxicillin/clavulanate":{"class":"beta_lactam","alias":"아목클","notes":["발진","설사","간기능 이상 드묾"]},
    "ceftriaxone":{"class":"cephalosporin","alias":"세프트리악손","notes":["설사","과민반응"]},
    "piperacillin/tazobactam":{"class":"beta_lactam","alias":"피펫/타조","notes":["설사","발진","나트륨부담"]},
    "levofloxacin":{"class":"fluoroquinolone","alias":"레보플록사신","notes":["힘줄통증/파열 드묾","어지럼","광과민"]},
    "ciprofloxacin":{"class":"fluoroquinolone","alias":"시프로","notes":["힘줄통증/파열 드묾","어지럼","광과민"]},
    "azithromycin":{"class":"macrolide","alias":"아지스로마이신","notes":["위장관 증상","QT연장 소인 주의"]},
    "vancomycin":{"class":"glycopeptide","alias":"반코마이신","notes":["주입반응","신장 부담"]},
}
