
# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime, timedelta
import re

st.set_page_config(page_title="피수치 자동 해석기 (통합본)", layout="centered")

APP_VER = "v6.1-integrated"
CREDIT = "제작: Hoya/GPT · 자문: Hoya/GPT"

st.title("🔬 피수치 자동 해석기 (통합본)")
st.caption(f"{CREDIT} | {APP_VER}")

# ============================================================
# 유틸
# ============================================================
def parse_number(s):
    if s is None:
        return 0.0
    s = str(s).strip()
    if s == "":
        return 0.0
    s = s.replace(",", "")
    try:
        return float(s)
    except Exception:
        m = re.search(r'-?\d+(?:\.\d+)?', s)
        if m:
            try:
                return float(m.group(0))
            except Exception:
                return 0.0
        return 0.0

def text_num_input(label, key, placeholder=""):
    if key not in st.session_state:
        st.session_state[key] = ""
    st.text_input(label, key=key, placeholder=placeholder)
    raw = st.session_state.get(key, "")
    val = parse_number(raw)
    st.session_state[f"{key}__val"] = val
    return val

def add_line(md_lines, text):
    md_lines.append(text)

def section(md_lines, title):
    add_line(md_lines, f"\n## {title}\n")

def bullet(md_lines, text):
    add_line(md_lines, f"- {text}")

def warn_box(text):
    st.warning(text)

def info_box(text):
    st.info(text)

def success_box(text):
    st.success(text)

# ============================================================
# 고정 가이드
# ============================================================
FOOD_RECS = {
    "albumin_low": ["달걀", "연두부", "흰살 생선", "닭가슴살", "귀리죽"],
    "k_low": ["바나나", "감자", "호박죽", "고구마", "오렌지"],
    "hb_low": ["소고기", "시금치", "두부", "달걀 노른자", "렌틸콩"],
    "na_low": ["전해질 음료", "미역국", "바나나", "오트밀죽", "삶은 감자"],
    "ca_low": ["연어통조림", "두부", "케일", "브로콜리", "참깨 제외"],
}

FEVER_GUIDE = (
    "🌡️ **발열 가이드**\n"
    "- 38.0~38.5℃: 해열제 복용 및 경과 관찰\n"
    "- **38.5℃ 이상**: 병원 연락\n"
    "- **39℃ 이상**: 즉시 병원 방문\n"
)

IRON_WARNING = (
    "⚠️ **철분제 경고**\n"
    "- 항암 치료 중이거나 백혈병 환자는 **철분제 복용을 피하는 것이 좋습니다.**\n"
    "- 철분제와 비타민C를 함께 복용하면 흡수가 촉진됩니다. **반드시 주치의와 상담 후** 복용 여부를 결정하세요."
)

NEUTROPENIA_COOKING = (
    "🧼 **호중구 낮음(ANC<500) 위생/조리 가이드**\n"
    "- 생채소 금지, 익힌 음식 또는 전자레인지 **30초 이상** 조리\n"
    "- 멸균/살균식품 권장\n"
    "- 조리 후 남은 음식은 **2시간 이후 섭취 비권장**\n"
    "- 껍질 있는 과일은 **주치의와 상담 후** 섭취"
)

DIURETIC_NOTE = (
    "💧 **이뇨제 병용 시 주의**: BUN/Cr 비, K/Na/Ca 전해질 이상 및 탈수 위험. 충분한 수분과 정기적 검사 필요."
)

# ============================================================
# 사이드바 (순서: 항암 → 항암제 → 투석 → 당뇨 → 일반)
# ============================================================
category = st.sidebar.radio(
    "카테고리 선택 (환자 유형을 골라주세요)",
    [
        "항암 환자용 (전체 수치 + 발열 해석)",
        "항암제 (약물별 부작용/주의사항)",
        "투석 환자 (소변량·전해질 중심)",
        "당뇨 (혈당·HbA1c 해석)",
        "기본(일반) (WBC/Hb/PLT/ANC + 발열, 교차 복용)"
    ],
    key="category_v5"
)

# ============================================================
# 항암 환자용
# ============================================================
if category.startswith("항암 환자용"):
    st.header("🧬 항암 환자용 해석")
    LABS_FULL = [
        ("WBC (백혈구)", "wbc"), ("Hb (헤모글로빈)", "hb"), ("혈소판 (PLT)", "plt"),
        ("ANC (호중구)", "anc"), ("Ca²⁺ (칼슘)", "ca"), ("Na⁺ (소디움)", "na"),
        ("K⁺ (포타슘)", "k"), ("Albumin (알부민)", "alb"), ("Glucose (혈당)", "glu"),
        ("Total Protein", "tp"), ("AST", "ast"), ("ALT", "alt"), ("LDH", "ldh"),
        ("CRP", "crp"), ("Creatinine (Cr)", "cr"), ("Total Bilirubin (TB)", "tb"),
        ("BUN", "bun"), ("BNP", "bnp"), ("UA (요산)", "ua"),
    ]
    cols = st.columns(3)
    for i, (label, slug) in enumerate(LABS_FULL):
        with cols[i % 3]:
            text_num_input(label, key=f"hx_{slug}_v5", placeholder="예: 3.5")
    fever_c = text_num_input("현재 체온(℃)", key="hx_fever_temp_c_v5", placeholder="예: 38.2")
    st.divider()
    if st.button("해석하기", key="btn_cancer_v5"):
        md = []
        add_line(md, f"# 항암 환자 해석 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
        add_line(md, CREDIT)
        entered = {}
        for _, slug in LABS_FULL:
            val = float(st.session_state.get(f"hx_{slug}_v5__val", 0) or 0)
            if val != 0: entered[slug] = val
        temp = float(st.session_state.get("hx_fever_temp_c_v5__val", 0) or 0)
        if entered:
            section(md, "입력한 수치")
            for k, v in entered.items():
                bullet(md, f"**{k.upper()}**: {v}")
        if temp: bullet(md, f"**체온**: {temp:.1f}℃")
        section(md, "요약 해석")
        anc = entered.get("anc")
        if anc is not None and anc < 500:
            st.error("호중구 낮음(ANC<500): 감염위험 매우 높음")
            add_line(md, NEUTROPENIA_COOKING)
        alb = entered.get("alb")
        if alb and alb < 3.3: bullet(md, f"알부민 낮음 → {' · '.join(FOOD_RECS['albumin_low'])}")
        hb = entered.get("hb")
        if hb and hb < 10:
            bullet(md, f"Hb 낮음 → {' · '.join(FOOD_RECS['hb_low'])}")
            add_line(md, IRON_WARNING)
        if temp:
            if temp >= 39.0: st.error("체온 39.0℃ 이상: 즉시 내원")
            elif temp >= 38.5: st.warning("체온 38.5℃ 이상: 병원 연락")
            elif temp >= 38.0: st.info("체온 38.0~38.5℃: 해열제 복용 및 경과관찰")
            add_line(md, FEVER_GUIDE)
        st.success("✅ 항암 환자 해석 완료.")
        report = "\n".join(md)
        st.download_button("📥 항암 환자 보고서(.md) 다운로드", data=report,
                           file_name="blood_cancer_interpretation.md", mime="text/markdown")

# ============================================================
# 항암제
# ============================================================
elif category.startswith("항암제"):
    st.header("💊 항암제 해석 (숫자 직접 입력)")
    DRUGS = [
        ("6-MP", "6mp"), ("MTX", "mtx"), ("베사노이드", "vesa"),
        ("ARA-C (IV)", "arac_iv"), ("ARA-C (SC)", "arac_sc"), ("ARA-C (HDAC)", "arac_hdac"),
        ("G-CSF", "gcsf"), ("하이드록시우레아", "hydroxyurea"), ("비크라빈", "vcrabine"),
        ("도우노루비신", "daunorubicin"), ("이달루시신", "idarubicin"),
        ("미토잔트론", "mitoxantrone"), ("Cyclophosphamide", "cyclophosphamide"),
        ("Etoposide", "etoposide"), ("Topotecan", "topotecan"), ("Fludarabine", "fludarabine"),
    ]
    cols = st.columns(2)
    for i, (label, slug) in enumerate(DRUGS):
        with cols[i % 2]:
            text_num_input(f"{label} (용량/개수)", key=f"dose_{slug}_v5", placeholder="예: 1 / 2.5 / 50")
    st.checkbox("최근 이뇨제 사용", key="flag_diuretic_v5")
    if st.button("항암제 해석하기", key="btn_chemo_v5"):
        md = []
        add_line(md, f"# 항암제 해석 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
        add_line(md, CREDIT)
        used_any = False
        for _, slug in DRUGS:
            v = float(st.session_state.get(f"dose_{slug}_v5__val", 0) or 0)
            if v != 0:
                used_any = True
                st.write(f"• **{slug.upper()}**: {v}")
        if not used_any:
            st.info("입력된 항암제 용량이 없습니다.")
        if float(st.session_state.get("dose_vesa_v5__val", 0) or 0) > 0:
            warn_box("베사노이드: 피부/점막 증상, 광과민, **설사** 가능.")
        if float(st.session_state.get("dose_arac_hdac_v5__val", 0) or 0) > 0:
            warn_box("HDAC: 신경독성/소뇌 증상, 점막염↑.")
        if float(st.session_state.get("dose_gcsf_v5__val", 0) or 0) > 0:
            warn_box("G-CSF: 골통/발열 반응 가능.")
        if st.session_state.get("flag_diuretic_v5", False):
            info_box(DIURETIC_NOTE)
        section(md, "상세 부작용/주의사항")
        bullet(md, "베사노이드: 피부/점막, 설사.")
        bullet(md, "ARA-C HDAC: 신경독성, 점막염↑.")
        bullet(md, "G-CSF: 골통, 발열 반응.")
        bullet(md, "MTX: 구내염, 간수치 상승.")
        bullet(md, "6-MP: 간독성·골수억제.")
        bullet(md, "Cyclophosphamide: 방광염, 수분섭취.")
        report = "\n".join(md)
        st.download_button("📥 항암제 보고서(.md)", data=report,
                           file_name="chemo_interpretation.md", mime="text/markdown")

# ============================================================
# 투석 환자
# ============================================================
elif category.startswith("투석 환자"):
    st.header("🫁 투석 환자 해석")
    text_num_input("하루 소변량(ml)", key="urine_ml_v5", placeholder="예: 500")
    for label, slug in [("K⁺", "k"), ("Na⁺", "na"), ("Ca²⁺", "ca"), ("BUN", "bun"),
                        ("Creatinine (Cr)", "cr"), ("UA", "ua"), ("Hb", "hb"), ("Albumin", "alb")]:
        text_num_input(label, key=f"dx_{slug}_v5")
    if st.button("해석하기", key="btn_dialysis_v5"):
        md = []
        add_line(md, f"# 투석 환자 해석 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
        add_line(md, CREDIT)
        urine = float(st.session_state.get("urine_ml_v5__val", 0) or 0)
        add_line(md, f"- 소변량: {int(urine)} ml/day")
        report = "\n".join(md)
        st.download_button("📥 투석 보고서(.md)", data=report,
                           file_name="dialysis_interpretation.md", mime="text/markdown")

# ============================================================
# 당뇨
# ============================================================
elif category.startswith("당뇨"):
    st.header("🍚 당뇨 해석")
    fpg = text_num_input("식전 혈당", key="dm_fpg_v5")
    ppg = text_num_input("식후 혈당", key="dm_ppg_v5")
    a1c = text_num_input("HbA1c (%)", key="dm_hba1c_v5")
    if st.button("해석하기", key="btn_dm_v5"):
        md = []
        add_line(md, f"# 당뇨 해석 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
        add_line(md, CREDIT)
        if fpg: bullet(md, f"식전: {fpg}")
        if ppg: bullet(md, f"식후: {ppg}")
        if a1c: bullet(md, f"HbA1c: {a1c}%")
        report = "\n".join(md)
        st.download_button("📥 당뇨 보고서(.md)", data=report,
                           file_name="diabetes_interpretation.md", mime="text/markdown")

# ============================================================
# 기본(일반)
# ============================================================
elif category.startswith("기본(일반)"):
    st.header("🩸 기본(일반)")
    LABS_SIMPLE = [("WBC", "wbc"), ("Hb", "hb"), ("혈소판", "plt"), ("ANC", "anc")]
    cols = st.columns(4)
    for i, (label, slug) in enumerate(LABS_SIMPLE):
        with cols[i % 4]:
            text_num_input(label, key=f"lab_{slug}_v5")
    fever_c = text_num_input("체온", key="fever_temp_c_v5")
    if st.button("해석하기", key="btn_general_simple_v5"):
        md = []
        add_line(md, f"# 일반 해석 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
        add_line(md, CREDIT)
        report = "\n".join(md)
        st.download_button("📥 일반 보고서(.md)", data=report,
                           file_name="blood_simple_interpretation.md", mime="text/markdown")

# ============================================================
# 하단 면책
# ============================================================
st.markdown("""
> ⚠️ 이 도구는 교육/자가관리 보조용입니다.  
> **최종 의사결정은 반드시 주치의가 승인**해야 합니다.
""")


