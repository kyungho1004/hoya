\
from .inputs import entered
from ..data.foods import FOODS

def _line(msg): return f"- {msg}"

def interpret_labs(vals, extras):
    lines = []
    WBC = vals.get("WBC(백혈구)")
    Hb  = vals.get("Hb(혈색소)")
    PLT = vals.get("혈소판(PLT)")
    ANC = vals.get("ANC(호중구)")
    Alb = vals.get("Albumin(알부민)")
    Ca  = vals.get("Ca(칼슘)")
    Na  = vals.get("Na(나트륨)")
    K   = vals.get("K(칼륨)")
    CRP = vals.get("CRP")
    BUN = vals.get("BUN")
    Cr  = vals.get("Creatinine(Cr)")

    if entered(ANC) and ANC < 500:
        lines.append(_line("호중구 매우 낮음 → **생야채 금지**, 모든 음식은 익혀 섭취, 남은 음식 2시간 이내 폐기"))
    if entered(Alb) and Alb < 3.5:
        lines.append(_line("알부민 낮음 → 단백질 보충 권장"))
    if entered(Ca) and Ca < 8.5:
        lines.append(_line("칼슘 낮음 → 칼슘 보충 식단 권장"))
    if entered(CRP) and CRP > 0.5:
        lines.append(_line("염증 수치 상승(의료진과 상의)"))
    if entered(BUN) and entered(Cr) and Cr>0:
        ratio = BUN/Cr
        if ratio>20: lines.append(_line("BUN/Cr 상승 → 탈수 가능성 고려"))
    diuretic = extras.get("diuretic_amt")
    if entered(diuretic):
        lines.append(_line("이뇨제 복용 중 → **저칼륨/저나트륨** 여부 주의, 어지럼/탈수 증상 모니터링"))
    if not lines:
        lines.append("입력된 값 기준 특이 소견 없음(의료진 판단 우선)")
    return lines

def compare_with_previous(nickname, current_vals):
    # 세션 기반 비교는 app.py에서 처리하므로 간단 메시지
    return []

def food_suggestions(vals, anc_place):
    recs = []
    Alb = vals.get("Albumin(알부민)")
    if entered(Alb) and Alb < 3.5:
        recs.append("**알부민 낮음** → " + ", ".join(FOODS["albumin_low"]))
    K = vals.get("K(칼륨)")
    if entered(K) and K < 3.5:
        recs.append("**칼륨 낮음** → " + ", ".join(FOODS["k_low"]))
    Hb = vals.get("Hb(혈색소)")
    if entered(Hb) and Hb < 10:
        recs.append("**Hb 낮음** → " + ", ".join(FOODS["hb_low"]) + " (⚠ 철분제는 항암 중 비권장 · 반드시 주치의와 상담)")
    Na = vals.get("Na(나트륨)")
    if entered(Na) and Na < 135:
        recs.append("**나트륨 낮음** → " + ", ".join(FOODS["na_low"]))
    Ca = vals.get("Ca(칼슘)")
    if entered(Ca) and Ca < 8.5:
        recs.append("**칼슘 낮음** → " + ", ".join(FOODS["ca_low"]))
    if anc_place == "가정" and recs:
        recs.append("_조리 시 전자레인지 30초 이상 가열 권장 · 껍질 과일은 주치의와 상담_")
    return recs

def summarize_meds(meds):
    out = []
    for k, v in meds.items():
        out.append(f"- {k}: 용량 정보 {v}")
    if not out:
        return []
    # 공통 경고
    out.append("⚠ 철분제+비타민C 병용은 흡수↑ → **항암 중은 반드시 주치의와 상의**")
    return out

def abx_summary(abx_inputs):
    if not abx_inputs: return []
    out = ["- 항생제 복용/주입 기록: " + ", ".join(f\"{k}:{v}\" for k, v in abx_inputs.items())]
    out.append("⚠ 일부 항생제는 QT 연장/광과민/와파린 상호작용이 있으므로 복용 중인 약물과 상호작용 확인")
    return out
