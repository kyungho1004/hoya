
def interpret_labs(vals, extras):
    lines = []
    # 아주 간단한 예시 해석
    wbc = vals.get("WBC(백혈구)")
    anc = vals.get("호중구(ANC)")
    if anc is not None and anc < 500:
        lines.append("⚠️ 호중구 저하: 생채소 금지 / 익힌 음식 권장 / 남은 음식 2시간 이후 섭취 금지")
    if wbc is not None and wbc < 3.0:
        lines.append("⚠️ 백혈구 감소: 감염 예방 수칙 강화")
    if not lines:
        lines.append("정상범위 내 항목 위주이며, 세부 해석은 주치의 지시를 따르세요.")
    return lines

def compare_with_previous(nickname, cur_vals):
    return []

def food_suggestions(vals, anc_place):
    return []

def summarize_meds(meds):
    out = []
    for k, info in meds.items():
        out.append(f"- {k}: 부작용/주의사항은 약물 사전을 참고하세요.")
    return out

def abx_summary(extras_abx):
    if not extras_abx: return []
    return [f"- {k}: 용량 입력 {v}" for k, v in extras_abx.items()]
