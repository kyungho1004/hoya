
# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime, timedelta
import re

st.set_page_config(page_title="피수치 자동 해석기 (통합본)", layout="centered")

APP_VER = "v6.0-integrated"
CREDIT = "제작: Hoya/GPT · 자문: Hoya/GPT"

st.title("🔬 피수치 자동 해석기 (통합본)")
st.caption(f"{CREDIT} | {APP_VER}")

# ============================================================
# 유틸
# ============================================================
def parse_number(s):
    """텍스트에서 숫자만 파싱."""
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
    """텍스트로 숫자 직접 입력. 파싱된 값은 key+'__val'에 저장."""
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
# 사이드바
# ============================================================
category = st.sidebar.radio(
    "카테고리 선택",
    [
        "항암 환자용 (전체 수치 + 발열 해석)",
        "기본(일반) (WBC/Hb/PLT/ANC + 발열, 교차 복용)",
        "항암제 (약물별 부작용/주의사항)",
        "투석 환자 (소변량·전해질 중심)",
        "당뇨 (혈당·HbA1c 해석)"
    ],
    key="category_v5"
)
# ============================================================
# 기본(일반) : WBC/Hb/PLT/ANC + 발열 + 교차 복용
# ============================================================
if category == "기본(일반)":
    st.header("🩸 기본(일반)")

    LABS_SIMPLE = [
        ("WBC (백혈구)", "wbc"),
        ("Hb (헤모글로빈)", "hb"),
        ("혈소판 (PLT)", "plt"),
        ("ANC (호중구)", "anc"),
    ]

    cols = st.columns(4)
    for i, (label, slug) in enumerate(LABS_SIMPLE):
        with cols[i % 4]:
            text_num_input(label, key=f"lab_{slug}_v5", placeholder="예: 3.4 / 10.2 / 80")

    fever_c = text_num_input("현재 체온(℃)", key="fever_temp_c_v5", placeholder="예: 38.3")

    st.divider()
    left, right = st.columns([1,1])

    with left:
        if st.button("해석하기", key="btn_general_simple_v5"):
            md = []
            add_line(md, f"# 간단 해석 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
            add_line(md, CREDIT)

            entered = {}
            for _, slug in LABS_SIMPLE:
                val = float(st.session_state.get(f"lab_{slug}_v5__val", 0) or 0)
                if val != 0:
                    entered[slug] = val
            temp = float(st.session_state.get("fever_temp_c_v5__val", 0) or 0)

            if entered:
                add_line(md, "## 입력한 수치")
                for k, v in entered.items():
                    add_line(md, f"- **{k.upper()}**: {v}")
            if temp:
                add_line(md, f"- **체온**: {temp:.1f}℃")

            add_line(md, "\n## 요약 해석")
            anc = entered.get("anc")
            if anc is not None and anc < 500:
                st.warning("호중구 낮음(ANC<500): 감염위험 매우 높음 → 즉시 위생/조리 가이드 준수 & 병원 지침 따르기")
                add_line(md, "ANC < 500: 감염위험 매우 높음 → 위생/조리 가이드 준수.")
                add_line(md, NEUTROPENIA_COOKING)

            if temp:
                if temp >= 39.0:
                    st.error("체온 39.0℃ 이상: **즉시 의료기관 방문 권장.**")
                elif temp >= 38.5:
                    st.warning("체온 38.5℃ 이상: **병원 연락 권장.**")
                elif temp >= 38.0:
                    st.info("체온 38.0~38.5℃: 해열제 복용 및 경과 관찰.")
                add_line(md, FEVER_GUIDE)

            st.success("✅ 간단 해석 완료.")
            report = "\n".join(md)
            st.download_button("📥 간단 보고서(.md) 다운로드", data=report,
                               file_name="blood_simple_interpretation.md", mime="text/markdown")

    with right:
        if st.button("🕒 교차 복용 타임테이블(12h) 생성", key="btn_antipyretic_plan_v6"):
            now = datetime.now().replace(second=0, microsecond=0)
            plan = []
            labels = ["아세트아미노펜", "이부프로펜"]
            for i in range(5):  # 0h, 3h, 6h, 9h, 12h
                t = now + timedelta(hours=3*i)
                drug = labels[i % 2]
                plan.append(f"- {t.strftime('%H:%M')} · **{drug}**")

            st.subheader("교차 복용 12시간 예시")
            for line in plan:
                st.write(line)

            st.info(
                "💊 **성인(OTC) 일반 가이드**\n"
                "- 아세트아미노펜: 500–1,000mg 1회, **최대 4,000mg/일** (간질환·음주 시 감량)\n"
                "- 이부프로펜: 200–400mg 1회, **최대 1,200mg/일(OTC)**\n"
                "\n👶 **소아(≥6개월)**\n"
                "- 아세트아미노펜: **10–15 mg/kg** q4–6h\n"
                "- 이부프로펜: **10 mg/kg** q6–8h (탈수·신장질환·위장관 출혈 위험 시 **피함**)\n"
                "\n⚠️ **주의**: 기저질환·복용약·항암치료 중인 경우 반드시 **주치의 지침** 우선."
            )

    st.markdown("""
> ℹ️ **팁**: 항암 치료/호중구 감소 중이라면, 이 화면 대신 좌측 **‘항암 환자용’** 또는 **‘항암제’** 카테고리를 사용하세요.
""")

# ============================================================
# 항암 환자용 : 전체 수치 20개 + 발열 + 가이드
# ============================================================
elif category == "항암 환자용":
    st.header("🧬 항암 환자용 해석")

    LABS_FULL = [
        ("WBC (백혈구)", "wbc"),
        ("Hb (헤모글로빈)", "hb"),
        ("혈소판 (PLT)", "plt"),
        ("ANC (호중구)", "anc"),
        ("Ca²⁺ (칼슘)", "ca"),
        ("Na⁺ (소디움)", "na"),
        ("K⁺ (포타슘)", "k"),
        ("Albumin (알부민)", "alb"),
        ("Glucose (혈당)", "glu"),
        ("Total Protein", "tp"),
        ("AST", "ast"),
        ("ALT", "alt"),
        ("LDH", "ldh"),
        ("CRP", "crp"),
        ("Creatinine (Cr)", "cr"),
        ("Total Bilirubin (TB)", "tb"),
        ("BUN", "bun"),
        ("BNP", "bnp"),
        ("UA (요산)", "ua"),
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
            if val != 0:
                entered[slug] = val
        temp = float(st.session_state.get("hx_fever_temp_c_v5__val", 0) or 0)

        if entered:
            section(md, "입력한 수치")
            for k, v in entered.items():
                bullet(md, f"**{k.upper()}**: {v}")
        if temp:
            bullet(md, f"**체온**: {temp:.1f}℃")

        section(md, "요약 해석")

        anc = entered.get("anc")
        if anc is not None and anc < 500:
            st.error("호중구 낮음(ANC<500): **감염위험 매우 높음** → 즉시 위생/조리 가이드 준수 & 병원 지침 따르기")
            add_line(md, NEUTROPENIA_COOKING)

        alb = entered.get("alb")
        if alb is not None and alb < 3.3:
            bullet(md, f"알부민 낮음 → 권장식품: {' · '.join(FOOD_RECS['albumin_low'])}")

        hb = entered.get("hb")
        if hb is not None and hb < 10:
            bullet(md, f"Hb 낮음 → 권장식품: {' · '.join(FOOD_RECS['hb_low'])}")
            add_line(md, IRON_WARNING)

        k_val = entered.get("k")
        if k_val is not None and k_val < 3.5:
            bullet(md, f"칼륨 낮음 → 권장식품: {' · '.join(FOOD_RECS['k_low'])}")
        na_val = entered.get("na")
        if na_val is not None and na_val < 135:
            bullet(md, f"나트륨 낮음 → 권장식품: {' · '.join(FOOD_RECS['na_low'])}")
        ca_val = entered.get("ca")
        if ca_val is not None and ca_val < 8.6:
            bullet(md, f"칼슘 낮음 → 권장식품: {' · '.join(FOOD_RECS['ca_low'])}")

        # 발열 가이드
        if temp:
            if temp >= 39.0:
                st.error("체온 39.0℃ 이상: **즉시 의료기관 방문 권장.**")
            elif temp >= 38.5:
                st.warning("체온 38.5℃ 이상: **병원 연락 권장.**")
            elif temp >= 38.0:
                st.info("체온 38.0~38.5℃: 해열제 복용 및 경과 관찰.")
            add_line(md, FEVER_GUIDE)

        st.success("✅ 항암 환자 해석 완료.")
        report = "\n".join(md)
        st.download_button("📥 항암 환자 보고서(.md) 다운로드", data=report,
                           file_name="blood_cancer_interpretation.md", mime="text/markdown")

# ============================================================
# 항암제 : 요약은 화면, 상세는 md
# ============================================================
elif category == "항암제":
    st.header("💊 항암제 해석 (숫자 직접 입력)")
    st.write("복용/투여 여부와 용량(정/회/㎎ 등)을 **숫자만** 입력하세요. (일반인은 알약 개수 단위 허용)")

    DRUGS = [
        ("6-MP", "6mp"),
        ("MTX", "mtx"),
        ("베사노이드", "vesa"),
        ("ARA-C (정맥 IV)", "arac_iv"),
        ("ARA-C (피하 SC)", "arac_sc"),
        ("ARA-C (고용량 HDAC)", "arac_hdac"),
        ("그라신 (G-CSF)", "gcsf"),
        ("하이드록시우레아", "hydroxyurea"),
        ("비크라빈", "vcrabine"),
        ("도우노루비신", "daunorubicin"),
        ("이달루시신", "idarubicin"),
        ("미토잔트론", "mitoxantrone"),
        ("사이클로포스파마이드", "cyclophosphamide"),
        ("에토포사이드", "etoposide"),
        ("토포테칸", "topotecan"),
        ("플루다라빈", "fludarabine"),
    ]

    cols = st.columns(2)
    for i, (label, slug) in enumerate(DRUGS):
        with cols[i % 2]:
            text_num_input(f"{label} (용량/개수)", key=f"dose_{slug}_v5", placeholder="예: 1 / 2.5 / 50")

    st.checkbox("최근 이뇨제 사용", key="flag_diuretic_v5")

    if st.button("항암제 해석하기", key="btn_chemo_v5"):
        md = []
        add_line(md, f"# 항암제 해석 결과 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
        add_line(md, CREDIT)

        used_any = False
        for _, slug in DRUGS:
            v = float(st.session_state.get(f"dose_{slug}_v5__val", 0) or 0)
            if v != 0:
                used_any = True
                st.write(f"• **{slug.upper()}**: {v}")
        if not used_any:
            st.info("입력된 항암제 용량이 없습니다. 0이 아닌 값만 반영합니다.")

        if float(st.session_state.get("dose_vesa_v5__val", 0) or 0) > 0:
            warn_box("베사노이드: 피부/점막 증상, 광과민, **설사** 가능. 증상 지속/악화 시 주치의와 상의.")
        if float(st.session_state.get("dose_arac_hdac_v5__val", 0) or 0) > 0:
            warn_box("HDAC: 신경독성/소뇌 증상, 점막염↑, 간/신장 모니터링 필요.")
        if float(st.session_state.get("dose_gcsf_v5__val", 0) or 0) > 0:
            warn_box("G-CSF: 골통/발열 반응 가능. 38.5℃ 이상 연락, 39℃ 이상 즉시 내원.")
        if st.session_state.get("flag_diuretic_v5", False):
            info_box(DIURETIC_NOTE)

        section(md, "상세 부작용/주의사항 (요약)")
        bullet(md, "베사노이드: 피부/점막 자극, 광과민, **설사** 가능.")
        bullet(md, "ARA-C IV/SC/HDAC: 골수억제, 점막염, **HDAC는 신경독성 주의**.")
        bullet(md, "G-CSF: 골통/발열 반응. 발열 지속 시 평가.")
        bullet(md, "MTX: 구내염, 간수치 상승, 신독성(고용량) 주의.")
        bullet(md, "6-MP: 간독성·골수억제. 황달/발열 시 연락.")
        bullet(md, "Cyclophosphamide: 출혈성 방광염, 수분섭취/메스나 고려.")
        bullet(md, "Etoposide/Topotecan/Fludarabine: 골수억제 중심, 감염주의.")
        bullet(md, "Anthracyclines(다우노/이달루시신/미토잔트론): 심독성 누적 용량 주의, 심장평가 필요.")

        add_line(md, "\n---\n" + FEVER_GUIDE)
        report = "\n".join(md)
        st.download_button("📥 항암제 상세 보고서(.md) 다운로드", data=report, file_name="chemo_interpretation.md", mime="text/markdown")

# ============================================================
# 투석 환자
# ============================================================
elif category == "투석 환자":
    st.header("🫁 투석 환자용 해석 (숫자 직접 입력)")

    text_num_input("하루 소변량(ml)", key="urine_ml_v5", placeholder="예: 500")
    for label, slug in [
        ("K⁺ (포타슘)", "k"),
        ("Na⁺ (소디움)", "na"),
        ("Ca²⁺ (칼슘)", "ca"),
        ("BUN", "bun"),
        ("Creatinine (Cr)", "cr"),
        ("UA (요산)", "ua"),
        ("Hb (헤모글로빈)", "hb"),
        ("Albumin (알부민)", "alb"),
    ]:
        text_num_input(label, key=f"dx_{slug}_v5")

    if st.button("해석하기", key="btn_dialysis_v5"):
        md = []
        add_line(md, f"# 투석 환자 해석 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
        add_line(md, CREDIT)

        urine = float(st.session_state.get("urine_ml_v5__val", 0) or 0)
        add_line(md, f"- 소변량: **{int(urine)} ml/day**")

        k = float(st.session_state.get("dx_k_v5__val", 0) or 0)
        if k != 0:
            if k > 5.5:
                warn_box("칼륨 높음: 고칼륨 식품(바나나, 오렌지 주스 등) 제한, 즉시 식이 조절/평가 필요.")
                bullet(md, "K>5.5: 고칼륨 식품 제한, 투석/약물 조정 검토.")
            elif k < 3.5:
                info_box("칼륨 낮음: 과도한 제한 주의, 의료진과 보충 여부 상의.")
                bullet(md, "K<3.5: 보충 고려, 원인 평가.")

        na = float(st.session_state.get("dx_na_v5__val", 0) or 0)
        if na != 0 and na < 135:
            info_box("저나트륨: 수분 과다/희석성 저나트륨증 가능. 제한 수분량 점검.")
            bullet(md, "Na<135: 수분 제한/원인 탐색.")

        bun = float(st.session_state.get("dx_bun_v5__val", 0) or 0)
        cr = float(st.session_state.get("dx_cr_v5__val", 0) or 0)
        if bun != 0 or cr != 0:
            bullet(md, f"BUN/Cr: {bun}/{cr} (요독증 증상 여부 점검)")

        alb = float(st.session_state.get("dx_alb_v5__val", 0) or 0)
        if alb != 0 and alb < 3.3:
            info_box("저알부민: 단백-에너지 영양불량 주의. 단백질 섭취/염분 조절 균형.")
            bullet(md, "Alb 낮음: 단백질 섭취 보강, 염분·수분 균형.")

        report = "\n".join(md)
        st.download_button("📥 투석 보고서(.md) 다운로드", data=report, file_name="dialysis_interpretation.md", mime="text/markdown")

# ============================================================
# 당뇨
# ============================================================
elif category == "당뇨":
    st.header("🍚 당뇨 해석 (숫자 직접 입력)")
    fpg = text_num_input("식전 혈당 (mg/dL)", key="dm_fpg_v5", placeholder="예: 95")
    ppg = text_num_input("식후 혈당 (mg/dL)", key="dm_ppg_v5", placeholder="예: 160")
    a1c = text_num_input("HbA1c (%)", key="dm_hba1c_v5", placeholder="예: 6.3")

    if st.button("해석하기", key="btn_dm_v5"):
        md = []
        add_line(md, f"# 당뇨 해석 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
        add_line(md, CREDIT)

        bullets = []
        if fpg != 0:
            bullets.append(f"식전: **{int(fpg)}** mg/dL")
        if ppg != 0:
            bullets.append(f"식후: **{int(ppg)}** mg/dL")
        if a1c != 0:
            bullets.append(f"HbA1c: **{a1c:.1f}%**")

        if bullets:
            add_line(md, "- " + " / ".join(bullets))
        else:
            st.info("입력된 수치가 없습니다.")

        info_box("저당 식이, 규칙적 운동, 수분 충분히. 저혈당 증상 시 즉시 섭취(포도당/주스 소량).")
        add_line(md, "- 기본: 저당 식이, 규칙 운동, 수분 보충.")

        report = "\n".join(md)
        st.download_button("📥 당뇨 보고서(.md) 다운로드", data=report, file_name="diabetes_interpretation.md", mime="text/markdown")

# ============================================================
# 하단 면책
# ============================================================
st.markdown("""
> ⚠️ 이 도구는 교육/자가관리 보조용입니다.  
> **최종 의사결정은 반드시 주치의가 승인**해야 합니다.
""")

