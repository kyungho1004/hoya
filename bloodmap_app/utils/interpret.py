
from .inputs import entered
from ..data.foods import FOODS

def _low(v, thr): 
    try: return entered(v) and float(v) < thr
    except: return False

def _high(v, thr):
    try: return entered(v) and float(v) > thr
    except: return False

def interpret_labs(vals, extras):
    out = []
    WBC = vals.get("WBC"); Hb=vals.get("Hb"); PLT=vals.get("PLT"); ANC=vals.get("ANC")
    Alb = vals.get("Albumin"); Ca = vals.get("Ca"); K = vals.get("K"); Na = vals.get("Na")
    CRP=vals.get("CRP"); AST=vals.get("AST"); ALT=vals.get("ALT"); LDH=vals.get("LDH")
    BUN=vals.get("BUN"); Cr=vals.get("Cr"); Glu=vals.get("Glucose")

    if _low(ANC, 500): out.append("🚨 호중구(ANC) 500 미만 — 생야채 금지, 익힌 음식만, 남은 음식 2시간 이내 섭취 금지, 멸균식품 권장.")
    elif _low(ANC, 1000): out.append("⚠️ 호중구(ANC) 저하 — 감염주의, 외출·군중 회피 권장.")
    if _low(PLT, 50): out.append("⚠️ 혈소판(PLT) 저하 — 출혈주의, 격한 운동/면도 주의.")
    if _low(Hb, 8): out.append("🩸 Hb 낮음 — 빈혈 증상 모니터링.")
    if _high(CRP, 0.5): out.append("🔥 CRP 상승 — 염증/감염 가능성, 발열 동반 시 병원 연락.")
    if _high(AST, 40) or _high(ALT, 40): out.append("🧪 간수치(AST/ALT) 상승 — 약물/영양 관리, 알코올 금지.")
    if _high(BUN, 23) or _high(Cr, 1.2): out.append("💧 신장부담(BUN/Cr) — 수분보충 및 단백질 과다 주의.")
    if _high(Glu, 180): out.append("🍬 고혈당 — 저당 식이 권장.")
    if _low(Alb, 3.0): out.append("🥚 알부민 낮음 — 단백질 보충 식단 필요.")
    if _low(Ca, 8.4): out.append("🦴 칼슘 낮음 — 칼슘 식품 보충.")
    if _low(K, 3.5): out.append("⚡ 칼륨 낮음 — 저칼륨 식단 교정.")
    if _low(Na, 135): out.append("🧂 나트륨 낮음 — 전해질 보충 고려.")
    if not out: out.append("✅ 입력된 범위에서 특이 위험 소견 없음(참고용).")
    return out

def compare_with_previous(nickname, current_dict):
    return [f"- {k}: 이번 {current_dict.get(k)}" for k in current_dict.keys() if entered(current_dict.get(k))]

def food_suggestions(vals, anc_place):
    recs = []
    if vals.get("Albumin") is not None and float(vals["Albumin"]) < 3.0:
        foods = FOODS.get("알부민 낮음", [])
        if foods: recs.append("**알부민 낮음 추천**: " + ", ".join(foods))
    if vals.get("K") is not None and float(vals["K"]) < 3.5:
        foods = FOODS.get("칼륨 낮음", [])
        if foods: recs.append("**칼륨 낮음 추천**: " + ", ".join(foods))
    if vals.get("Hb") is not None and float(vals["Hb"]) < 10:
        foods = FOODS.get("Hb 낮음", [])
        if foods: recs.append("**Hb 낮음 추천**: " + ", ".join(foods))
    if vals.get("Na") is not None and float(vals["Na"]) < 135:
        foods = FOODS.get("나트륨 낮음", [])
        if foods: recs.append("**나트륨 낮음 추천**: " + ", ".join(foods))
    if vals.get("Ca") is not None and float(vals["Ca"]) < 8.4:
        foods = FOODS.get("칼슘 낮음", [])
        if foods: recs.append("**칼슘 낮음 추천**: " + ", ".join(foods))
    anc = vals.get("ANC")
    try:
        if anc is not None and float(anc) < 500:
            recs.append("**ANC 식품안전**: 생채소 금지, 익힌 음식·전자레인지 30초 이상, 멸균식품 권장, 남은 음식 2시간 이후 섭취 금지, 껍질 과일은 의사와 상담.")
    except: pass
    return recs

def summarize_meds(meds: dict):
    out=[]
    for k, info in meds.items():
        base=f"- {k}"
        if "dose_or_tabs" in info: base+=f" (용량/알약: {info['dose_or_tabs']})"
        up=k.upper()
        if up in ["MTX","METHOTREXATE"]:
            out.append(base + " — 간독성/구내염/골수억제/신장독성 주의, 고용량 시 류코보린 구제 고려.")
        elif up=="ATRA":
            out.append(base + " — 분화증후군(DS)·두통·피부건조 주의, 호흡곤란/부종 시 즉시 연락.")
        elif up=="ARA-C":
            out.append(base + " — 고용량(HDAC) 시 소뇌실조, 결막염/각막염 가능.")
        elif up in ["G-CSF","FILGRASTIM"]:
            out.append(base + " — 골통·발열 반응 가능, 투여 후 일시적 WBC↑.")
        else:
            out.append(base + " — 부작용/상호작용은 보고서 참고.")
    return out

def abx_summary(abx_dict):
    _DEFAULT_ABX_TIPS = {
        "Quinolone(퀴놀론)": ["QT 연장 주의", "광과민", "힘줄염/파열 드묾"],
        "Macrolide(마크롤라이드)": ["CYP3A4 상호작용", "QT 연장"],
        "Penicillin/βLactam": ["아나필락시스 병력 주의", "설사·발진 가능"],
        "Cephalosporin": ["과민반응 병력 확인", "알코올 상호작용(일부)"],
    }
    out=[]
    for cat, amt in (abx_dict or {}).items():
        tip="; ".join(_DEFAULT_ABX_TIPS.get(cat, []))
        out.append(f"- {cat}: {tip if tip else '일반 주의'}")
    return out
