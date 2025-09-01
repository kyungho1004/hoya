
# -*- coding: utf-8 -*-
try:
    import streamlit as st
except Exception:
    class _Dummy:
        def __getattr__(self, k):
            def _f(*a, **kw): return None
            return _f
    st = _Dummy()

from config import (LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
                    LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP,
                    LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP, ORDER, FEVER_GUIDE)
from bloodmap_app.data.foods import FOODS, FOODS_SEASONAL, RECIPE_LINKS
from bloodmap_app.data.drugs import ANTICANCER, ABX_GUIDE
from bloodmap_app.utils.inputs import entered

def _fmt(name, val):
    try: v = float(val)
    except Exception: return str(val)
    if name == LBL_CRP: return f"{v:.2f}"
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
    if extras.get("diuretic_amt", 0):
        if entered(l.get(LBL_Na)) and l[LBL_Na]<135: add("🧂 이뇨제 복용 중 저나트륨 → 어지럼/탈수 주의, 의사와 상의")
        if entered(l.get(LBL_K)) and l[LBL_K]<3.5: add("🥔 이뇨제 복용 중 저칼륨 → 심전도/근력저하 주의, 칼륨 보충 식이 고려")
        if entered(l.get(LBL_Ca)) and l[LBL_Ca]<8.5: add("🦴 이뇨제 복용 중 저칼슘 → 손저림/경련 주의")
    return out

def food_suggestions(l, anc_place):
    foods=[]
    if entered(l.get(LBL_Alb)) and l[LBL_Alb]<3.5: foods.append(("알부민 낮음", FOODS["Albumin_low"]))
    if entered(l.get(LBL_K)) and l[LBL_K]<3.5: foods.append(("칼륨 낮음", FOODS["K_low"]))
    if entered(l.get(LBL_Hb)) and l[LBL_Hb]<12: foods.append(("Hb 낮음", FOODS["Hb_low"]))
    if entered(l.get(LBL_Na)) and l[LBL_Na]<135: foods.append(("나트륨 낮음", FOODS["Na_low"]))
    if entered(l.get(LBL_Ca)) and l[LBL_Ca]<8.5: foods.append(("칼슘 낮음", FOODS["Ca_low"]))
    lines = []
    for title, lst in foods:
        linked = [f"[{x}]({RECIPE_LINKS.get(x,'https://www.10000recipe.com/')})" for x in lst]
        lines.append(f"- {title} → " + ', '.join(linked))
    if entered(l.get(LBL_ANC)) and l[LBL_ANC]<500:
        if anc_place == "병원":
            lines.append("- 🧼 (병원) 호중구 감소: 멸균/살균 처리식 권장, 외부 음식 반입 제한, 병원 조리식 우선.")
        else:
            lines.append("- 🧼 (가정) 호중구 감소: 생채소 금지, 완전가열, 조리 후 2시간 경과 음식 금지.")
    lines.append("- ⚠️ 항암 환자는 철분제는 반드시 주치의와 상의.")
    return lines

def summarize_meds(meds: dict):
    out=[]
    for k, v in meds.items():
        info=ANTICANCER.get(k); 
        if not info: continue
        line=f"• {k} ({info.get('alias','')}): AE {', '.join(info.get('aes', []))}"
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

def compare_with_previous(nickname: str, cur_labs: dict):
    try:
        recs = (st.session_state.get("records") or {}).get(nickname, [])
    except Exception:
        recs = []
    if not recs: return []
    prev = None
    for r in reversed(recs):
        prev = r.get("labs") or {}
        if prev: break
    if not prev: return []
    lines = []
    for k, v in cur_labs.items():
        if k in prev:
            try: dv = float(v) - float(prev[k])
            except Exception: continue
            arrow = "↑" if dv>0 else ("↓" if dv<0 else "→")
            if k == "CRP(염증수치)":
                lines.append(f"- {k}: {float(v):.2f} ({arrow}{abs(dv):.2f} vs. 이전)")
            else:
                if float(v).is_integer() and float(prev[k]).is_integer():
                    lines.append(f"- {k}: {int(v)} ({arrow}{int(abs(dv))} vs. 이전)")
                else:
                    lines.append(f"- {k}: {float(v):.1f} ({arrow}{abs(dv):.1f} vs. 이전)")
    return lines
