
import streamlit as st
from ..config import (LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_Alb, LBL_Na, LBL_K, LBL_CRP)

def _num(v):
    try:
        return float(v) if v is not None and str(v) != "" else None
    except Exception:
        return None

def _warn_block(msg, level="warn"):
    if level == "error":
        st.error(msg)
    elif level == "success":
        st.success(msg)
    else:
        st.warning(msg)

def interpret_labs(vals, extras, anc_place="가정"):
    """Return list of interpretation lines and also render critical banners (ANC/Albumin/Ca)."""
    lines = []
    WBC = _num(vals.get(LBL_WBC))
    Hb = _num(vals.get(LBL_Hb))
    PLT = _num(vals.get(LBL_PLT))
    ANC = _num(vals.get(LBL_ANC))
    Ca = _num(vals.get(LBL_Ca))
    Alb = _num(vals.get(LBL_Alb))
    Na = _num(vals.get(LBL_Na))
    K = _num(vals.get(LBL_K))
    CRP = _num(vals.get(LBL_CRP))

    # ----- ANC banners (집/병원 분기)
    if ANC is not None:
        if ANC < 500:
            guide = "즉시 병원 평가·격리/항생제 고려" if anc_place == "가정" else "격리수칙 준수·의료진 지시 따르기"
            _warn_block(f"🚑 ANC 매우 낮음(<500). {guide} · 생야채/반숙 금지 · 조리 후 2시간 지난 음식 금지 · 멸균식품 권장.", level="error")
            lines.append("ANC<500: 즉시 의료평가 권고, 외출 금지, 익힌 음식만, 멸균식품 권장.")
        elif ANC < 1000:
            guide = "외출/대중장소 자제, 감염 주의" if anc_place == "가정" else "보호자·면회 제한, 병원 내 위생 강화"
            _warn_block(f"⚠️ ANC 낮음(500~999). {guide} · 생야채 금지 · 익힌 음식만(전자레인지 30초+).", level="warn")
            lines.append("ANC 500~999: 감염주의, 생채소 금지, 익힌 음식만.")
        else:
            _warn_block("🙂 ANC 안정 범위(≥1000). 위생관리 지속, 증상 변동 시 연락.", level="success")
            lines.append("ANC≥1000: 안정 범위. 표준 위생수칙 유지.")

    # ----- Albumin low
    if Alb is not None and Alb < 3.5:
        _warn_block("⚠️ 알부민 낮음(<3.5): 부종/회복력 저하 → 고단백 식이 권장(달걀·연두부·흰살생선·닭가슴살·귀리죽).", level="warn")
        lines.append("알부민 낮음: 고단백 식사 및 칼로리 보충 필요.")

    # ----- Calcium low
    if Ca is not None and Ca < 8.5:
        _warn_block("⚠️ 칼슘 낮음(<8.5): 근경련/손발저림 가능 → 칼슘 식품(연어통조림·두부·케일·브로콜리) 권장.", level="warn")
        lines.append("칼슘 낮음: 칼슘 함유 식품 섭취, 증상 시 상담.")

    # ----- Sodium/Potassium trends
    if Na is not None and Na < 135:
        lines.append("나트륨 낮음: 전해질 보충음료·염분 보충 고려.")
    if K is not None and K < 3.5:
        lines.append("칼륨 낮음: 바나나/감자/호박죽/고구마/오렌지 권장.")
    if CRP is not None and CRP >= 0.5:
        lines.append("CRP 상승: 염증 가능성. 발열/증상 동반 시 진료 권고.")

    # ----- Platelet/Hb quick
    if PLT is not None and PLT < 50:
        lines.append("혈소판 <50: 멍/출혈 주의, 넘어짐/양치 출혈 주의.")
    if Hb is not None and Hb < 8.0:
        lines.append("Hb <8: 빈혈 증상 시 수혈/평가 고려 (철분제는 권장하지 않음).")

    # ----- Diuretic flag
    diu = extras.get("diuretic_amt")
    try:
        diu = float(diu) if diu not in (None, "") else None
    except Exception:
        diu = None
    if diu and diu > 0:
        lines.append("이뇨제 복용: BUN/Cr·전해질 변동 모니터링 및 탈수 관리 필요.")

    # 철분제 경고 (고정 문구)
    lines.append("⚠️ 주의: 항암 치료 중 철분제 복용은 권장되지 않습니다. 필요 시 반드시 주치의와 상의하세요.")

    return lines
