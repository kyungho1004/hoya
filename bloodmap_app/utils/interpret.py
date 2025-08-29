
from datetime import date
import streamlit as st
from ..config import (LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
                      LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP,
                      LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP, ORDER, FEVER_GUIDE)
from ..data.foods import FOODS, FOODS_SEASONAL, RECIPE_LINKS
from ..data.drugs import ANTICANCER, ABX_GUIDE
from .inputs import entered

def _fmt(name, v):
    try: v=float(v)
    except: return str(v)
    return f"{v:.2f}" if name==LBL_CRP else (f"{int(v)}" if v.is_integer() else f"{v:.1f}")

def interpret_labs(l, extras):
    out=[]
    def add(s): out.append("- "+s)
    if entered(l.get(LBL_WBC)):
        v=l[LBL_WBC]; add(f"{LBL_WBC} {_fmt(LBL_WBC,v)}: "+("낮음 → 감염 위험↑" if v<4 else "높음 → 감염/염증 가능" if v>10 else "정상"))
    if entered(l.get(LBL_ANC)):
        v=l[LBL_ANC]; add(f"{LBL_ANC} {_fmt(LBL_ANC,v)}: "+("중증 감소(<500)" if v<500 else "감소(<1500)" if v<1500 else "정상"))
    if entered(l.get(LBL_CRP)):
        v=l[LBL_CRP]; add(f"{LBL_CRP} {_fmt(LBL_CRP,v)}: "+("상승 → 염증/감염 의심" if v>0.5 else "정상"))
    return out

def food_suggestions(l, anc_place):
    items=[]
    if entered(l.get(LBL_Alb)) and l[LBL_Alb]<3.5: items.append(("알부민 낮음", FOODS["Albumin_low"]))
    lines=[]
    for title, lst in items:
        lines.append("- "+title+" → "+", ".join(f"[{x}]({RECIPE_LINKS.get(x,'https://www.10000recipe.com/')})" for x in lst))
    if entered(l.get(LBL_ANC)) and l[LBL_ANC]<500:
        lines.append("- 🧼 호중구 감소: 모든 음식 완전가열/생식 금지")
    lines.append("- ⚠️ 철분제 복용 전 반드시 주치의와 상의")
    return lines

def compare_with_previous(nickname, new_labs):
    return []
def summarize_meds(meds): return [f"• {k}: AE {', '.join(ANTICANCER.get(k,{}).get('aes',[]))}" for k in meds.keys()]
def abx_summary(abx): return [f"• {k}: {v}" for k,v in abx.items() if v]
