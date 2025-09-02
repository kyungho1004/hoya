
import streamlit as st
from .inputs import _parse_numeric
def interpret_labs(values: dict):
    out = []
    if not values: return out
    # Very simple rules
    wbc = _parse_numeric(values.get("WBC"))
    anc = _parse_numeric(values.get("ANC"))
    hb = _parse_numeric(values.get("Hb"))
    plt = _parse_numeric(values.get("PLT"))
    if anc is not None:
        if anc < 0.5:
            out.append("⚠️ 중증 호중구감소(ANC<0.5): 발열 시 즉시 응급 연락")
        elif anc < 1.0:
            out.append("주의: 호중구감소(ANC<1.0)")
    if hb is not None and hb < 8:
        out.append("주의: 빈혈 소견(Hb<8)")
    if plt is not None and plt < 50:
        out.append("주의: 혈소판 감소(PLT<50)")
    return out
def compare_with_previous(cur: dict, prev: dict):
    return "이전 기록과 비교: 자동 비교 베타"
def food_suggestions(values: dict):
    return ["철분↑ 음식 권장", "수분 충분히", "단백질 섭취"]
def summarize_meds(anticancer_name: str, ANTICANCER: dict):
    if not anticancer_name: return ""
    info = ANTICANCER.get(anticancer_name, {})
    aes = ", ".join(info.get("aes", [])) or "정보 없음"
    return f"{anticancer_name} 부작용: {aes}"
def abx_summary(abx_name: str, ABX_GUIDE: dict):
    if not abx_name: return ""
    key = (abx_name or '').lower()
    ent = ABX_GUIDE.get(key)
    if not ent: return "사전에 없는 항생제입니다(정보용 안내만 참고)."
    cls = ent.get("class","")
    alias = ent.get("alias","")
    notes = ", ".join(ent.get("notes", []))
    return f"{abx_name} ({alias}) · 계열:{cls} · 주의: {notes}"
