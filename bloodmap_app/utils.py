# -*- coding: utf-8 -*-
import streamlit as st

def num_input_generic(label, key=None, decimals=1, placeholder=""):
    val = st.text_input(label, key=key, placeholder=placeholder)
    return _parse_numeric(val, decimals=decimals)

def _parse_numeric(val, decimals=1):
    if val is None: 
        return None
    s = str(val).strip().replace(",", "")
    if s == "":
        return None
    try:
        f = float(s)
    except Exception:
        return None
    return round(f, decimals)

def entered(v):
    try:
        return v is not None and str(v) != "" and float(v) != 0
    except Exception:
        return False

def interpret_labs(vals, anc_place="가정"):
    out = []
    wbc = vals.get("WBC(백혈구)"); hb = vals.get("Hb(혈색소)"); plt = vals.get("혈소판(PLT)")
    anc = vals.get("ANC(호중구)"); alb = vals.get("Albumin(알부민)"); crp = vals.get("CRP")
    if anc is not None:
        if anc < 500:
            out.append("⚠️ 호중구 매우 낮음(ANC<500): 생야채 금지, 익힌 음식만, 조리 후 2시간 지난 음식 금지, 멸균/살균식품 권장.")
        elif anc < 1000:
            out.append("주의: 호중구 낮음(ANC<1000): 식중독 예방 수칙 철저.")
    if hb is not None and hb < 8.0:
        out.append("빈혈 가능성(Hb<8.0): 어지러움/호흡곤란 시 주치의 상의.")
    if plt is not None and plt < 50:
        out.append("혈소판 저하(PLT<50): 출혈/멍 주의, 넘어짐 조심.")
    if alb is not None and alb < 3.3:
        out.append("알부민 낮음: 단백질 섭취(달걀, 연두부, 흰살생선, 닭가슴살, 귀리죽).")
    if crp is not None and crp >= 1.0:
        out.append("염증 수치 상승(CRP≥1.0): 발열/증상 동반 시 진료권유.")
    if not out:
        out.append("입력한 기본 수치에서 특이 위험 신호는 없어요. 계속 관찰하세요.")
    return out

def food_suggestions(vals, anc_place="가정"):
    out = []
    alb = vals.get("Albumin(알부민)"); k = vals.get("K(포타슘)")
    if alb is not None and alb < 3.3:
        out.append("- **알부민 낮음**: 달걀, 연두부, 흰살 생선, 닭가슴살, 귀리죽")
    if k is not None and k < 3.5:
        out.append("- **칼륨 낮음**: 바나나, 감자, 호박죽, 고구마, 오렌지")
    return out

def compare_with_previous(_id, current):
    recs = st.session_state.get("records", {}).get(_id, [])
    if not recs:
        return []
    last = recs[-1].get("labs", {})
    lines = []
    for k, v in current.items():
        if v is None: 
            continue
        if k in last and last[k] is not None:
            diff = float(v) - float(last[k])
            s = f"{k}: {last[k]} → {v} ({'+' if diff>=0 else ''}{round(diff,2)})"
            lines.append(s)
    return lines

def summarize_meds(meds):
    out = []
    for k, v in meds.items():
        alias = v.get("alias") or ""
        if alias:
            out.append(f"- {k}({alias}): {v.get('dose_or_tabs') or v.get('dose') or ''}")
        else:
            out.append(f"- {k}: {v.get('dose_or_tabs') or v.get('dose') or ''}")
    if not out:
        out.append("선택된 항암제가 없습니다.")
    return out

def abx_summary(abx_dict):
    lines = []
    for k, v in abx_dict.items():
        lines.append(f"- {k}: 투여량 {v}")
    return lines

def build_report(mode, meta, vals, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines, general_special):
    md = []
    md.append(f"# BloodMap 보고서 ({mode})")
    md.append("## 메타")
    for k, v in meta.items():
        if v: md.append(f"- **{k}**: {v}")
    md.append("\n## 기본 수치(입력값만)\n")
    for k, v in vals.items():
        if v is not None and v != "": md.append(f"- {k}: {v}")
    if extra_vals:
        md.append("\n## 특수검사(암별)\n")
        for k, v in extra_vals.items():
            if v is not None and v != "": md.append(f"- {k}: {v}")
    if general_special:
        md.append("\n## 특수검사(일반·신장/면역)\n")
        for k, v in general_special.items():
            if v is not None and v != "": md.append(f"- {k}: {v}")
    if cmp_lines: md.append("\n## 이전 기록과 비교\n" + "\n".join([f"- {x}" for x in cmp_lines]))
    if meds_lines: md.append("\n## 항암제 요약\n" + "\n".join(meds_lines))
    if abx_lines: md.append("\n## 항생제 요약\n" + "\n".join(abx_lines))
    if food_lines: md.append("\n## 음식 가이드\n" + "\n".join(food_lines))
    md.append("\n---\n본 자료는 참고용이며, 모든 의학적 판단은 의료진과 상의하세요.")
    return "\n".join(md)

def render_graphs():
    st.divider(); st.header("📈 저장된 기록(세션) 개요")
    recs = st.session_state.get("records", {})
    st.caption(f"현재 세션에 저장된 별명#PIN 개수: {len(recs)}")
