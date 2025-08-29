
from datetime import date
import streamlit as st
from xml.sax.saxutils import escape

from ..config import (LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
                      LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP,
                      LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP, ORDER, FEVER_GUIDE)
from ..foods import FOODS, FOODS_SEASONAL, RECIPE_LINKS
from ..data.drugs import ANTICANCER, ABX_GUIDE
from .inputs import entered

def _fmt(name, val):
    try:
        v = float(val)
    except Exception:
        return str(val)
    if name == LBL_CRP:
        return f"{v:.2f}"
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
    if extras.get("diuretic_amt", 0) and extras["diuretic_amt"]>0:
        if entered(l.get(LBL_Na)) and l[LBL_Na]<135: add("🧂 이뇨제 복용 중 저나트륨 → 어지럼/탈수 주의, 의사와 상의")
        if entered(l.get(LBL_K)) and l[LBL_K]<3.5: add("🥔 이뇨제 복용 중 저칼륨 → 심전도/근력저하 주의, 칼륨 보충 식이 고려")
        if entered(l.get(LBL_Ca)) and l[LBL_Ca]<8.5: add("🦴 이뇨제 복용 중 저칼슘 → 손저림/경련 주의")
    return out

def _arrow(delta):
    if delta > 0: return "↑"
    if delta < 0: return "↓"
    return "→"

def compare_with_previous(nickname, new_labs):
    rows = st.session_state.records.get(nickname, []) if "records" in st.session_state else []
    if not rows:
        return []
    prev = rows[-1].get("labs", {})
    out = []
    for k in ORDER:
        if entered(new_labs.get(k)) and entered(prev.get(k)):
            try:
                cur = float(new_labs[k])
                old = float(prev[k])
                delta = cur - old
                sign = _arrow(delta)
                if k == LBL_CRP:
                    dtxt = f"{delta:+.2f}"
                elif k in (LBL_WBC, LBL_ANC, LBL_AST, LBL_ALT, LBL_LDH, LBL_BNP, LBL_Glu):
                    dtxt = f"{delta:+.1f}"
                else:
                    dtxt = f"{delta:+.1f}"
                out.append(f"- {k}: {_fmt(k, cur)} ({sign} {dtxt} vs { _fmt(k, old) })")
            except Exception:
                pass
    return out

def seasonal_food_section():
    m = date.today().month
    if m in (3,4,5): season="봄"
    elif m in (6,7,8): season="여름"
    elif m in (9,10,11): season="가을"
    else: season="겨울"
    st.markdown(f"#### 🥗 계절 식재료 ({season})")
    items = FOODS_SEASONAL.get(season, [])
    if items:
        st.write("· " + ", ".join(items))
    st.caption("간단 레시피는 아래 추천 목록의 각 식재료 링크를 눌러 참고하세요.")

def food_suggestions(l, anc_place):
    from .inputs import entered as _entered
    foods=[]
    seasonal_food_section()

    if _entered(l.get(LBL_Alb)) and l[LBL_Alb]<3.5: foods.append(("알부민 낮음", FOODS["Albumin_low"]))
    if _entered(l.get(LBL_K)) and l[LBL_K]<3.5: foods.append(("칼륨 낮음", FOODS["K_low"]))
    if _entered(l.get(LBL_Hb)) and l[LBL_Hb]<12: foods.append(("Hb 낮음", FOODS["Hb_low"]))
    if _entered(l.get(LBL_Na)) and l[LBL_Na]<135: foods.append(("나트륨 낮음", FOODS["Na_low"]))
    if _entered(l.get(LBL_Ca)) and l[LBL_Ca]<8.5: foods.append(("칼슘 낮음", FOODS["Ca_low"]))

    if _entered(l.get(LBL_ANC)) and l[LBL_ANC]<500:
        if anc_place == "병원":
            anc_line = "🧼 (병원) 호중구 감소: 멸균/살균 처리식 권장, 외부 음식 반입 제한, 병원 조리식 우선."
        else:
            anc_line = "🧼 (가정) 호중구 감소: 생채소 금지, 모든 음식 완전가열(전자레인지 30초+), 조리 후 2시간 경과 음식 금지, 껍질 과일은 의료진과 상의."
    else:
        anc_line = None

    lines = []
    for title, lst in foods:
        linked = []
        for x in lst:
            url = RECIPE_LINKS.get(x, "https://www.10000recipe.com/")
            linked.append(f"[{x}]({url})")
        lines.append(f"- {title} → " + ", ".join(linked))
    if anc_line:
        lines.append("- " + anc_line)
    lines.append("- ⚠️ 항암/백혈병 환자는 철분제는 반드시 주치의와 상의(비타민C 병용 시 흡수↑).")
    return lines

def summarize_meds(meds: dict):
    out=[]
    for k, v in meds.items():
        info=ANTICANCER.get(k)
        if not info:
            continue
        line=f"• {k} ({info['alias']}): AE {', '.join(info['aes'])}"
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
            from ..data.drugs import ABX_GUIDE
            tip=", ".join(ABX_GUIDE.get(k, []))
            shown=f"{int(use)}" if float(use).is_integer() else f"{use:.1f}"
            lines.append(f"• {k}: {shown}  — 주의: {tip}")
    return lines
