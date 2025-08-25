
# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime, timedelta
import re, json, io, copy

st.set_page_config(page_title="피수치 자동 해석기 (통합본+음식추천)", layout="centered")

APP_VER = "v7.2-food"
CREDIT = "제작: Hoya/GPT · 자문: Hoya/GPT"

st.title("🔬 피수치 자동 해석기 (통합본)")
st.caption(f"{CREDIT} | {APP_VER}")

# ============================================================
# 유틸
# ============================================================
def parse_number(s):
    if s is None:
        return 0.0
    try:
        s = str(s).strip().replace(",", "")
    except Exception:
        return 0.0
    if s == "":
        return 0.0
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

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

# ============================================================
# 고정 가이드 & 음식 사전
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

def show_food_recs(title, items):
    """즉시 화면에 음식 추천 섹션 표시"""
    if not items:
        return
    st.subheader(f"🍽️ {title}")
    for t, foods in items:
        st.write(f"- **{t}** → {', '.join(foods[:5])}")

# ============================================================
# 안전한 기록 구조 보정
# ============================================================
def _coerce_values_dict(d):
    if not isinstance(d, dict):
        return {}
    out = {}
    for k, v in d.items():
        if isinstance(v, (int, float)):
            out[k] = float(v)
        else:
            out[k] = parse_number(v)
    return out

def normalize_history(loaded):
    if not isinstance(loaded, dict):
        return None, "최상위가 객체(JSON object)가 아닙니다. { \"별명\": [ ... ] } 형태여야 합니다."
    norm = {}
    for nickname, items in loaded.items():
        if not isinstance(nickname, str):
            return None, "키(별명)가 문자열이어야 합니다."
        if not isinstance(items, list):
            return None, f"'{nickname}' 값은 리스트여야 합니다."
        lst = []
        for idx, rec in enumerate(items):
            if not isinstance(rec, dict):
                return None, f"'{nickname}'의 {idx+1}번째 항목이 객체가 아닙니다."
            ts = rec.get("ts")
            cat = rec.get("category")
            vals = rec.get("values")
            if not isinstance(ts, str) or not isinstance(cat, str) or not isinstance(vals, dict):
                return None, f"'{nickname}'의 {idx+1}번째 항목에 ts/category/values 중 누락 또는 형식 오류가 있습니다."
            lst.append({"ts": ts.strip(), "category": str(cat), "values": _coerce_values_dict(vals)})
        norm[nickname] = lst
    return norm, None

def safe_get_nickname_list(history):
    try:
        return list(history.keys())
    except Exception:
        return []

# ============================================================
# 기록 저장/불러오기
# ============================================================
if "history" not in st.session_state:
    st.session_state["history"] = {}

def save_record(nickname:str, category:str, values:dict):
    if not nickname:
        return False
    hist = st.session_state["history"].setdefault(nickname, [])
    hist.append({"ts": now_str(), "category": category, "values": copy.deepcopy(values)})
    return True

def prev_record(nickname:str, category_prefix:str):
    history = st.session_state.get("history", {})
    items = history.get(nickname, [])
    if not isinstance(items, list):
        return None
    for rec in reversed(items):
        try:
            if isinstance(rec, dict) and str(rec.get("category","")).startswith(category_prefix):
                return rec
        except Exception:
            continue
    return None

def last_two_anc(nickname:str, category_prefix:str):
    history = st.session_state.get("history", {})
    items = history.get(nickname, [])
    if not isinstance(items, list):
        return []
    result = []
    for rec in reversed(items):
        try:
            if not isinstance(rec, dict):
                continue
            cat = str(rec.get("category",""))
            if not cat.startswith(category_prefix):
                continue
            vals = rec.get("values", {})
            if not isinstance(vals, dict):
                continue
            anc = parse_number(vals.get("anc"))
            if anc != 0:
                result.append((anc, rec.get("ts","")))
            if len(result) == 2:
                break
        except Exception:
            continue
    return result

# ============================================================
# 사이드바 공통
# ============================================================
nickname = st.sidebar.text_input("별명(환자 식별)", key="nickname_v7", placeholder="예: 홍길동/OOO호실")
st.sidebar.caption("같은 별명으로 입력하면 자동으로 이전 기록과 비교합니다.")

with st.sidebar.expander("📦 기록 내보내기/불러오기", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 전체 기록 JSON 내보내기"):
            data = json.dumps(st.session_state["history"], ensure_ascii=False, indent=2)
            st.download_button("다운로드 시작", data=data, file_name="lab_history.json", mime="application/json")
    with col2:
        if st.button("🧹 기록 초기화"):
            st.session_state["history"] = {}
            st.success("기록을 모두 지웠습니다.")
    uploaded = st.file_uploader("기록 JSON 불러오기", type=["json"])
    if uploaded is not None:
        try:
            raw = uploaded.read().decode("utf-8")
            loaded = json.loads(raw)
            norm, err = normalize_history(loaded)
            if err:
                st.error("불러오기 실패: " + err)
            else:
                for k, v in norm.items():
                    if k in st.session_state["history"] and isinstance(st.session_state["history"][k], list):
                        st.session_state["history"][k].extend(v)
                    else:
                        st.session_state["history"][k] = v
                st.success(f"✅ 기록 불러오기 완료 (별명 {len(norm)}명)")
        except Exception as e:
            st.error(f"불러오기 실패(예외): {e}")

with st.sidebar.expander("🔎 디버그(업로드된 기록 확인)", expanded=True):
    try:
        nicks = safe_get_nickname_list(st.session_state["history"])
        st.write("저장된 별명 목록:", nicks if nicks else "(없음)")
        preview = {}
        for name, items in st.session_state["history"].items():
            if isinstance(items, list) and items:
                last = items[-1]
                if isinstance(last, dict):
                    preview[name] = {"ts": last.get("ts"), "category": last.get("category"), "values_keys": list(last.get("values", {}).keys())}
        st.write("미리보기(최근 1건):", preview if preview else "(없음)")
    except Exception as e:
        st.write("디버그 표시 중 오류:", e)

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
    key="category_v7"
)

# ============================================================
# 카테고리 1) 항암 환자용
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
            text_num_input(label, key=f"hx_{slug}_v7", placeholder="예: 3.5")
    fever_c = text_num_input("현재 체온(℃)", key="hx_fever_temp_c_v7", placeholder="예: 38.2")
    st.divider()
    if st.button("해석하기", key="btn_cancer_v7"):
        entered = {}
        for _, slug in LABS_FULL:
            v = float(st.session_state.get(f"hx_{slug}_v7__val", 0) or 0)
            if v != 0:
                entered[slug] = v
        temp = float(st.session_state.get("hx_fever_temp_c_v7__val", 0) or 0)
        if nickname:
            save_record(nickname, "항암 환자용", entered | ({"temp_c": temp} if temp else {}))
        md = []
        add_line(md, f"# 항암 환자 해석 ({now_str()})")
        add_line(md, CREDIT)
        if entered:
            section(md, "입력한 수치")
            for k, v in entered.items():
                bullet(md, f"**{k.upper()}**: {v}")
        if temp:
            bullet(md, f"**체온**: {temp:.1f}℃")
        section(md, "요약 해석")
        anc = entered.get("anc")
        if anc is not None and anc < 500:
            st.error("호중구 낮음(ANC<500): 감염위험 매우 높음")
            add_line(md, NEUTROPENIA_COOKING)
        alb = entered.get("alb")
        hb = entered.get("hb")
        k_val = entered.get("k")
        na_val = entered.get("na")
        ca_val = entered.get("ca")
        # 음식 추천 즉시 표시
        food_items = []
        if alb is not None and alb < 3.3:
            food_items.append(("알부민 낮음", FOOD_RECS["albumin_low"]))
            bullet(md, f"알부민 낮음 → 권장식품: {', '.join(FOOD_RECS['albumin_low'])}")
        if hb is not None and hb < 10:
            food_items.append(("Hb 낮음", FOOD_RECS["hb_low"]))
            bullet(md, f"Hb 낮음 → 권장식품: {', '.join(FOOD_RECS['hb_low'])}")
            add_line(md, IRON_WARNING)
        if k_val is not None and k_val < 3.5:
            food_items.append(("칼륨 낮음", FOOD_RECS["k_low"]))
            bullet(md, f"칼륨 낮음 → 권장식품: {', '.join(FOOD_RECS['k_low'])}")
        if na_val is not None and na_val < 135:
            food_items.append(("나트륨 낮음", FOOD_RECS["na_low"]))
            bullet(md, f"나트륨 낮음 → 권장식품: {', '.join(FOOD_RECS['na_low'])}")
        if ca_val is not None and ca_val < 8.6:
            food_items.append(("칼슘 낮음", FOOD_RECS["ca_low"]))
            bullet(md, f"칼슘 낮음 → 권장식품: {', '.join(FOOD_RECS['ca_low'])}")
        if food_items:
            show_food_recs("맞춤 식단 제안", food_items)
        # 발열 가이드
        if temp:
            if temp >= 39.0: st.error("체온 39.0℃ 이상: 즉시 의료기관 방문 권장.")
            elif temp >= 38.5: st.warning("체온 38.5℃ 이상: 병원 연락 권장.")
            elif temp >= 38.0: st.info("체온 38.0~38.5℃: 해열제 복용 및 경과 관찰.")
            add_line(md, FEVER_GUIDE)
        # 이전 기록 비교
        if nickname:
            prev = prev_record(nickname, "항암 환자용")
            if prev and isinstance(prev, dict):
                section(md, f"이전 기록과 비교 (별명: {nickname})")
                prev_vals = prev.get("values", {}) if isinstance(prev.get("values", {}), dict) else {}
                for k, curv in entered.items():
                    prevv = parse_number(prev_vals.get(k))
                    if prevv == 0 and k not in prev_vals:
                        continue
                    delta = curv - prevv
                    arrow = "⬆️" if delta > 0 else ("⬇️" if delta < 0 else "➡️")
                    bullet(md, f"{k.upper()}: {curv} ({arrow} {delta:+.2f} vs {prevv})")
                if temp and "temp_c" in prev_vals:
                    dtemp = temp - parse_number(prev_vals.get("temp_c"))
                    arrow = "⬆️" if dtemp > 0 else ("⬇️" if dtemp < 0 else "➡️")
                    bullet(md, f"체온: {temp:.1f}℃ ({arrow} {dtemp:+.1f}℃ vs {prev_vals.get('temp_c')})")
                bullet(md, f"이전 기록 시각: {prev.get('ts')}")
        # ANC 예측
        if nickname and anc is not None and anc != 0:
            pts = last_two_anc(nickname, "항암 환자용")
            if len(pts) >= 2:
                (anc1, ts1), (anc0, ts0) = pts[1], pts[0]
                try:
                    t1 = datetime.strptime(ts1, "%Y-%m-%d %H:%M")
                    t0 = datetime.strptime(ts0, "%Y-%m-%d %H:%M")
                    days = max((t0 - t1).total_seconds() / 86400.0, 0.01)
                except Exception:
                    days = 1.0
                rate = (anc0 - anc1) / days
                section(md, "ANC 회복 속도 & 퇴원 가능성 예측")
                bullet(md, f"최근 ANC 상승 속도: **{rate:.1f} /일** (기준: {ts1}→{ts0})")
                for target in [500, 1000]:
                    if rate > 0:
                        remain = max(target - anc0, 0)
                        eta_days = remain / rate if remain > 0 else 0
                        eta_text = f"{eta_days:.1f}일 후 (대략 { (datetime.now() + timedelta(days=eta_days)).strftime('%m/%d %H:%M') })"
                        bullet(md, f"ANC {target} 예상 도달: **{eta_text}**")
                    else:
                        bullet(md, f"ANC {target} 예상 도달: **상승 추세 아님 → 예측 불가**")
            else:
                info_box("ANC 예측: 동일 별명으로 최소 2회 기록이 있어야 추세 계산이 가능합니다.")
        report = "\n".join(md)
        st.download_button("📥 항암 환자 보고서(.md) 다운로드", data=report, file_name="blood_cancer_interpretation.md", mime="text/markdown")

# ============================================================
# 카테고리 2) 항암제
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
            text_num_input(f"{label} (용량/개수)", key=f"dose_{slug}_v7", placeholder="예: 1 / 2.5 / 50")
    st.checkbox("최근 이뇨제 사용", key="flag_diuretic_v7")
    if st.button("항암제 해석하기", key="btn_chemo_v7"):
        md = []
        add_line(md, f"# 항암제 해석 ({now_str()})")
        add_line(md, CREDIT)
        used_any = False
        for _, slug in DRUGS:
            v = float(st.session_state.get(f"dose_{slug}_v7__val", 0) or 0)
            if v != 0:
                used_any = True
                st.write(f"• **{slug.upper()}**: {v}")
        if not used_any:
            st.info("입력된 항암제 용량이 없습니다.")
        if float(st.session_state.get("dose_vesa_v7__val", 0) or 0) > 0:
            warn_box("베사노이드: 피부/점막 증상, 광과민, 설사 가능.")
        if float(st.session_state.get("dose_arac_hdac_v7__val", 0) or 0) > 0:
            warn_box("HDAC: 신경독성/소뇌 증상, 점막염↑.")
        if float(st.session_state.get("dose_gcsf_v7__val", 0) or 0) > 0:
            warn_box("G-CSF: 골통/발열 반응 가능.")
        if st.session_state.get("flag_diuretic_v7", False):
            info_box("💧 이뇨제 병용 시 주의: 전해질 이상/탈수 위험. 수분 및 검사 필요.")
        section(md, "상세 부작용/주의사항 (요약)")
        bullet(md, "베사노이드: 피부/점막, 설사.")
        bullet(md, "ARA-C HDAC: 신경독성, 점막염↑.")
        bullet(md, "G-CSF: 골통, 발열 반응.")
        bullet(md, "MTX: 구내염, 간수치 상승.")
        bullet(md, "6-MP: 간독성·골수억제.")
        bullet(md, "Cyclophosphamide: 방광염, 수분섭취.")
        report = "\n".join(md)
        st.download_button("📥 항암제 보고서(.md)", data=report, file_name="chemo_interpretation.md", mime="text/markdown")

# ============================================================
# 카테고리 3) 투석 환자
# ============================================================
elif category.startswith("투석 환자"):
    st.header("🫁 투석 환자 해석")
    text_num_input("하루 소변량(ml)", key="urine_ml_v7", placeholder="예: 500")
    for label, slug in [("K⁺", "k"), ("Na⁺", "na"), ("Ca²⁺", "ca"), ("BUN", "bun"),
                        ("Creatinine (Cr)", "cr"), ("UA", "ua"), ("Hb", "hb"), ("Albumin", "alb")]:
        text_num_input(label, key=f"dx_{slug}_v7")
    if st.button("해석하기", key="btn_dialysis_v7"):
        md = []
        add_line(md, f"# 투석 환자 해석 ({now_str()})")
        add_line(md, CREDIT)
        urine = float(st.session_state.get("urine_ml_v7__val", 0) or 0)
        add_line(md, f"- 소변량: {int(urine)} ml/day")
        # 음식 추천
        food_items = []
        k = float(st.session_state.get("dx_k_v7__val", 0) or 0)
        na = float(st.session_state.get("dx_na_v7__val", 0) or 0)
        ca = float(st.session_state.get("dx_ca_v7__val", 0) or 0)
        alb = float(st.session_state.get("dx_alb_v7__val", 0) or 0)
        hb  = float(st.session_state.get("dx_hb_v7__val", 0) or 0)
        if k and k < 3.5:
            food_items.append(("칼륨 낮음", FOOD_RECS["k_low"]))
        if na and na < 135:
            food_items.append(("나트륨 낮음", FOOD_RECS["na_low"]))
        if ca and ca < 8.6:
            food_items.append(("칼슘 낮음", FOOD_RECS["ca_low"]))
        if alb and alb < 3.3:
            food_items.append(("알부민 낮음", FOOD_RECS["albumin_low"]))
        if hb and hb < 10:
            food_items.append(("Hb 낮음", FOOD_RECS["hb_low"]))
        if food_items:
            show_food_recs("맞춤 식단 제안", food_items)
        report = "\n".join(md)
        st.download_button("📥 투석 보고서(.md)", data=report, file_name="dialysis_interpretation.md", mime="text/markdown")

# ============================================================
# 카테고리 4) 당뇨
# ============================================================
elif category.startswith("당뇨"):
    st.header("🍚 당뇨 해석")
    fpg = text_num_input("식전 혈당", key="dm_fpg_v7", placeholder="예: 95")
    ppg = text_num_input("식후 혈당", key="dm_ppg_v7", placeholder="예: 160")
    a1c = text_num_input("HbA1c (%)", key="dm_hba1c_v7", placeholder="예: 6.3")
    if st.button("해석하기", key="btn_dm_v7"):
        md = []
        add_line(md, f"# 당뇨 해석 ({now_str()})")
        add_line(md, CREDIT)
        if fpg: bullet(md, f"식전: {fpg}")
        if ppg: bullet(md, f"식후: {ppg}")
        if a1c: bullet(md, f"HbA1c: {a1c}%")
        # 간단 식이 팁
        st.subheader("🍽️ 기본 식이 팁")
        st.write("- 정제 탄수화물 줄이고, 단백질/식이섬유 보강")
        st.write("- 물 충분히, 가당음료/야식 줄이기")
        report = "\n".join(md)
        st.download_button("📥 당뇨 보고서(.md)", data=report, file_name="diabetes_interpretation.md", mime="text/markdown")

# ============================================================
# 카테고리 5) 기본(일반)
# ============================================================
elif category.startswith("기본(일반)"):
    st.header("🩸 기본(일반)")
    LABS_SIMPLE = [("WBC", "wbc"), ("Hb", "hb"), ("혈소판", "plt"), ("ANC", "anc")]
    cols = st.columns(4)
    for i, (label, slug) in enumerate(LABS_SIMPLE):
        with cols[i % 4]:
            text_num_input(label, key=f"lab_{slug}_v7", placeholder="예: 3.4 / 10.2 / 80")
    fever_c = text_num_input("현재 체온(℃)", key="fever_temp_c_v7", placeholder="예: 38.3")
    st.divider()
    if st.button("해석하기", key="btn_general_simple_v7"):
        entered = {}
        for _, slug in LABS_SIMPLE:
            v = float(st.session_state.get(f"lab_{slug}_v7__val", 0) or 0)
            if v != 0:
                entered[slug] = v
        temp = float(st.session_state.get("fever_temp_c_v7__val", 0) or 0)
        if nickname:
            save_record(nickname, "기본(일반)", entered | ({"temp_c": temp} if temp else {}))
        md = []
        add_line(md, f"# 일반 해석 ({now_str()})")
        add_line(md, CREDIT)
        if entered:
            section(md, "입력한 수치")
            for k, v in entered.items():
                bullet(md, f"**{k.upper()}**: {v}")
        if temp:
            bullet(md, f"**체온**: {temp:.1f}℃")
        section(md, "요약 해석")
        anc = entered.get("anc")
        if anc is not None and anc < 500:
            st.warning("호중구 낮음(ANC<500): 감염위험 ↑")
            add_line(md, NEUTROPENIA_COOKING)
        if temp:
            if temp >= 39.0: st.error("체온 39.0℃ 이상: 즉시 내원")
            elif temp >= 38.5: st.warning("체온 38.5℃ 이상: 병원 연락")
            elif temp >= 38.0: st.info("체온 38.0~38.5℃: 해열제 복용 및 경과관찰")
            add_line(md, FEVER_GUIDE)
        # 음식 추천 (기본 카테고리는 Hb만 활용)
        food_items = []
        hb = entered.get("hb")
        if hb is not None and hb < 10:
            food_items.append(("Hb 낮음", FOOD_RECS["hb_low"]))
        if food_items:
            show_food_recs("맞춤 식단 제안", food_items)
        # 비교
        if nickname:
            prev = prev_record(nickname, "기본(일반)")
            if prev and isinstance(prev, dict):
                section(md, f"이전 기록과 비교 (별명: {nickname})")
                prev_vals = prev.get("values", {}) if isinstance(prev.get("values", {}), dict) else {}
                for k, curv in entered.items():
                    prevv = parse_number(prev_vals.get(k))
                    if prevv == 0 and k not in prev_vals:
                        continue
                    delta = curv - prevv
                    arrow = "⬆️" if delta > 0 else ("⬇️" if delta < 0 else "➡️")
                    bullet(md, f"{k.upper()}: {curv} ({arrow} {delta:+.2f} vs {prevv})")
                if temp and "temp_c" in prev_vals:
                    dtemp = temp - parse_number(prev_vals.get("temp_c"))
                    arrow = "⬆️" if dtemp > 0 else ("⬇️" if dtemp < 0 else "➡️")
                    bullet(md, f"체온: {temp:.1f}℃ ({arrow} {dtemp:+.1f}℃ vs {prev_vals.get('temp_c')})")
                bullet(md, f"이전 기록 시각: {prev.get('ts')}")
        report = "\n".join(md)
        st.download_button("📥 일반 보고서(.md)", data=report, file_name="blood_simple_interpretation.md", mime="text/markdown")

# ============================================================
# 하단 면책
# ============================================================
st.markdown("""
> ⚠️ 이 도구는 교육/자가관리 보조용입니다.  
> **최종 의사결정은 반드시 주치의가 승인**해야 합니다.
""")
