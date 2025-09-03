# -*- coding: utf-8 -*-
from .inputs import entered
from ..config import (ORDER, LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Alb, LBL_K, LBL_Na, LBL_Ca)

def _line(msg): return f"- {msg}"

def interpret_labs(vals, extras):
    out = []
    wbc = vals.get(LBL_WBC); hb = vals.get(LBL_Hb); plt = vals.get(LBL_PLT); anc = vals.get(LBL_ANC)
    alb = vals.get(LBL_Alb); k = vals.get(LBL_K); na = vals.get(LBL_Na); ca = vals.get(LBL_Ca)

    if entered(anc) and anc < 500:
        out.append(_line("ANC < 500: 감염 고위험 — 생야채 금지, 익힌 음식/멸균식품 권장, 남은 음식 2시간 이후 섭취 금지"))
    if entered(hb) and hb < 8.0:
        out.append(_line("빈혈 가능: 어지럼/호흡곤란 체크, 필요 시 의료진과 수혈 상의"))
    if entered(plt) and plt < 50000:
        out.append(_line("혈소판 저하: 출혈 주의, 칫솔은 부드러운 것 사용, 면도기 전기식 권장"))
    if entered(alb) and alb < 3.5:
        out.append(_line("알부민 낮음: 단백질 보충 식단 권장 (달걀/연두부/흰살생선/닭가슴살/귀리죽)"))
    if entered(k) and k < 3.4:
        out.append(_line("저칼륨: 바나나·감자·호박죽·고구마·오렌지 등으로 보충"))
    if entered(na) and na < 135:
        out.append(_line("저나트륨: 전해질 음료/미역국/삶은 감자 등 권장"))
    if entered(ca) and ca < 8.5:
        out.append(_line("저칼슘: 연어통조림·두부·케일·브로콜리 권장(참깨 제외)"))
    if extras.get("diuretic_amt"):
        out.append(_line("이뇨제 복용: 탈수/전해질 이상 주의 (BUN/Cr 비, K/Na/Ca 점검)"))
    return out or [_line("입력된 수치가 부족합니다. 필요한 항목을 더 입력하세요.")]

def compare_with_previous(nickname_key, latest_vals):
    # 간단 비교: 최근 1개와 비교
    import streamlit as st
    recs = st.session_state.get("records", {}).get(nickname_key, [])
    if not recs:
        return []
    prev = recs[-1].get("labs", {})
    lines = []
    for k, v in latest_vals.items():
        if v is None: continue
        pv = prev.get(k)
        if pv is None: continue
        diff = v - pv
        if abs(diff) > 0:
            arrow = "↑" if diff > 0 else "↓"
            lines.append(f"- {k}: {pv} → {v} ({arrow}{abs(diff):.1f})")
    return lines

def food_suggestions(vals, anc_place):
    from ..data.foods import FOODS
    out = []
    alb = vals.get("Albumin(알부민, g/dL)")
    if alb and alb < 3.5:
        out.append("**알부민 낮음 권장 식품(5)**: " + ", ".join(FOODS["알부민 낮음"]))
    # ANC 장소별 가이드
    if anc_place == "가정":
        out.append("가정용 위생 가이드: 손씻기·음식 충분가열·조리도구 분리")
    else:
        out.append("병원 식사 가이드: 병원 지침 준수, 외부음식 반입 자제")
    return out

def summarize_meds(meds):
    from ..data.drugs import ANTICANCER
    out = []
    for k, v in meds.items():
        alias = ANTICANCER.get(k, {}).get("alias", "")
        out.append(f"- {k}({alias}) 투여: {v}")
    return out

def abx_summary(abx_map):
    out = []
    for k, v in abx_map.items():
        out.append(f"- {k}: 용량 {v}")
    return out
