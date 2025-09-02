# -*- coding: utf-8 -*-
"""Minimal, dependency-light helpers for the demo app."""
def interpret_labs(vals, extras):
    lines = []
    anc = vals.get("ANC")
    if anc is not None:
        try:
            v = float(anc)
            if v < 500:
                lines.append("🚨 ANC 500 미만: 즉시 병원 상담/격리 식사 권장")
            elif v < 1000:
                lines.append("⚠️ ANC 1000 미만: 익힌 음식·위생 철저")
            else:
                lines.append("✅ ANC 양호")
        except Exception:
            lines.append("ANC 값 해석 불가")
    crp = vals.get("CRP")
    if crp is not None:
        try:
            if float(crp) >= 0.5:
                lines.append("🔥 CRP 상승: 증상 모니터링 및 필요 시 진료")
        except Exception:
            pass
    if not lines:
        lines.append("🙂 입력된 값 기준 특이 위험 신호 없음")
    return lines

def compare_with_previous(nickname, current_vals):
    if not nickname:
        return []
    out = [f"- {k}: {v}" for k, v in current_vals.items() if v is not None]
    return out

def food_suggestions(vals, anc_place):
    out = []
    anc = vals.get("ANC")
    try:
        if anc is not None and float(anc) < 1000:
            out.append("익힌 음식 위주, 상온 보관 음식 피하기")
            if anc_place == "병원":
                out.append("병원식 권장 범위 내에서 선택")
    except Exception:
        pass
    return out
