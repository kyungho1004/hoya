
# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime, timedelta
import re, json, io, copy
import pandas as pd

st.set_page_config(page_title="피수치 자동 해석기 (통합+기록뷰어+저장확인+ANC예측)", layout="wide")

APP_VER = "v7.6-confirm-save-anc-table"
CREDIT = "제작: Hoya/GPT · 자문: Hoya/GPT"

st.title("🔬 피수치 자동 해석기 (통합) + 📊 기록 뷰어")
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

def _parse_ts(ts):
    try:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M")
    except Exception:
        return None

# ============================================================
# 고정 가이드 & 음식 사전
# ============================================================
FOOD_RECS = {
    "albumin_low": ["달걀", "연두부", "흰살 생선", "닭가슴살", "귀리죽"],
    "k_low": ["바나나", "감자", "호박죽", "고구마", "오렌지"],
    "hb_low": ["소고기", "시금치", "두부", "달걀 노른자", "렌틸콩"],
    "na_low": ["전해질 음료", "미역국", "바나나", "오트밀죽", "삶은 감자"],
    "ca_low": ["연어통조림", "두부", "케일", "브로콜리", "참깨 제외"],
    "p_low": ["우유/요거트", "달걀", "생선", "닭고기", "두부·콩류"],
    "p_high_avoid": ["우유·치즈", "견과/씨앗", "콜라·가공음료(인산염 첨가)", "초콜릿", "가공육", "내장류", "통곡물·현미"]
}

ANC_FOOD_CAUTION = {
    "avoid": [
        "생고기·레어 스테이크·육회·회(생선회/초밥)",
        "반숙/흰자 안 익은 달걀, 수란·수제 마요네즈",
        "비살균(살균표시 없는) 우유/주스·치즈(연성치즈)",
        "익히지 않은 해산물(굴, 조개, 훈제연어 등)",
        "샐러드 바/뷔페 음식, 길거리 즉석식품",
        "덜 씻은 생채소·과일 껍질, 새싹채소",
        "덜 익힌 콩나물/숙주나물",
        "유산균 발효식품(콤부차·발효음료) — 주치의 지침 우선"
    ],
    "safe": [
        "완전히 익힌 고기/생선/달걀(노른자까지 익힘)",
        "살균(멸균) 표시 우유·요구르트·주스",
        "껍질 벗긴 과일, 충분히 씻고 데친 채소",
        "막 조리해 뜨거운 음식(전자레인지 30초 이상 재가열)",
        "개봉 직후 섭취하는 포장식품, 멸균팩 죽/우유",
        "조리 후 2시간 내 섭취, 남은 음식 빠른 냉장 보관"
    ]
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

def show_food_recs(title, items):
    if not items:
        return
    st.subheader(f"🍽️ {title}")
    for t, foods in items:
        st.write(f"- **{t}** → {', '.join(foods[:6])}")

def show_anc_caution(anc_val):
    if anc_val is None or anc_val == 0:
        return
    if anc_val < 500:
        st.subheader("🧼 ANC 낮음(＜500) 식품/조리 주의")
        st.write("**피해야 할 것:** " + " · ".join(ANC_FOOD_CAUTION["avoid"]))
        st.write("**안전하게 먹는 요령:** " + " · ".join(ANC_FOOD_CAUTION["safe"]))
    elif anc_val < 1000:
        st.subheader("🧼 ANC 낮음(500~999) 식품/조리 주의")
        st.write("가능하면 아래 **주의사항을 지켜서 조리**해 주세요.")
        st.write("**피해야 할 것:** " + " · ".join(ANC_FOOD_CAUTION["avoid"][:5]) + " 등")
        st.write("**안전하게 먹는 요령:** " + " · ".join(ANC_FOOD_CAUTION["safe"]))

# ============================================================
# 기록(History) 관리
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

if "history" not in st.session_state:
    st.session_state["history"] = {}

def save_record(nickname:str, category:str, values:dict):
    if not nickname:
        return False
    hist = st.session_state["history"].setdefault(nickname, [])
    hist.append({"ts": now_str(), "category": category, "values": copy.deepcopy(values)})
    return True

def safe_get_nickname_list(history):
    try:
        return list(history.keys())
    except Exception:
        return []

# ANC 예측 테이블 (>= 2일 이상 누적 시)
def anc_prediction_table(nickname: str, category_prefix: str):
    history = st.session_state.get("history", {})
    items = history.get(nickname, [])
    rows = []
    for rec in items:
        if not isinstance(rec, dict):
            continue
        if not str(rec.get("category","")).startswith(category_prefix):
            continue
        vals = rec.get("values", {})
        anc = parse_number(vals.get("anc"))
        ts  = rec.get("ts", "")
        tdt = _parse_ts(ts)
        if tdt and anc != 0:
            rows.append({"ts": tdt, "anc": anc})
    if len(rows) < 2:
        return None, "기록이 2건 미만입니다."
    rows = sorted(rows, key=lambda x: x["ts"])
    span_days = (rows[-1]["ts"] - rows[0]["ts"]).total_seconds() / 86400.0
    if span_days < 2.0:
        return None, "측정 간격이 2일 미만입니다."
    # 최근 2점으로 속도 추정
    anc0, t0 = rows[-1]["anc"], rows[-1]["ts"]
    anc1, t1 = rows[-2]["anc"], rows[-2]["ts"]
    days = max((t0 - t1).total_seconds() / 86400.0, 0.01)
    rate = (anc0 - anc1) / days  # /day

    preds = []
    for target in [500, 1000]:
        if rate > 0:
            remain = max(target - anc0, 0)
            eta_days = remain / rate if remain > 0 else 0
            eta_dt = datetime.now() + timedelta(days=eta_days)
            preds.append({"목표 ANC": target, "예상 도달까지(일)": round(eta_days, 1), "예상 시각": eta_dt.strftime("%Y-%m-%d %H:%M")})
        else:
            preds.append({"목표 ANC": target, "예상 도달까지(일)": None, "예상 시각": "상승 추세 아님 → 예측 불가"})

    hist_df = pd.DataFrame(rows).rename(columns={"ts":"시각","anc":"ANC"})
    pred_df = pd.DataFrame(preds)
    return (hist_df, pred_df, rate), None

# ============================================================
# 사이드바 공통
# ============================================================
nickname = st.sidebar.text_input("별명(환자 식별)", key="nickname_v7", placeholder="예: 홍길동/OOO호실")
st.sidebar.caption("같은 별명으로 입력하면 자동으로 이전 기록과 비교합니다.")
# 중복 안내
_existing_nicks = list(st.session_state.get("history", {}).keys())
if nickname:
    if nickname in _existing_nicks:
        st.sidebar.warning(f"‘{nickname}’은(는) 이미 존재합니다. 저장 시 기존 기록에 **그대로 추가**됩니다. (숫자 붙일 필요 없음)")
        st.sidebar.caption("동명이인 구분: 예) 홍길동(소아과), 홍길동-외래A")
    else:
        st.sidebar.success("새 별명입니다. 저장 시 첫 기록이 생성됩니다.")

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
            raw = uploaded.read().decode("utf-8-sig")
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

# 모드
mode = st.sidebar.radio("모드 선택", ["📊 기록 뷰어", "🧪 해석기"], index=1, key="mode_v1")

# ============================================================
# 📊 기록 뷰어
# ============================================================
if mode.startswith("📊"):
    st.header("📊 기록 뷰어 (테이블/차트/내보내기)")
    history = st.session_state.get("history", {})
    nicks = safe_get_nickname_list(history)

    if not nicks:
        st.info("기록이 없습니다. 먼저 해석기에서 기록을 저장하거나 JSON을 불러오세요.")
    else:
        c1, c2, c3 = st.columns([2,2,2])
        with c1:
            pick_nick = st.selectbox("별명 선택", options=nicks, index=0)
        with c2:
            cats = sorted({ rec.get("category","") for rec in history.get(pick_nick, []) if isinstance(rec, dict) })
            picks = st.multiselect("카테고리 필터", options=cats, default=cats)
        with c3:
            days = st.number_input("최근 N일만 보기", min_value=0, max_value=3650, value=0, step=1, help="0이면 전체 기간")
        
        # 데이터 정리
        now_dt = datetime.now()
        rows = []
        for rec in history.get(pick_nick, []):
            if not isinstance(rec, dict): continue
            if picks and rec.get("category") not in picks: continue
            ts_str = rec.get("ts","")
            ts_dt = _parse_ts(ts_str)
            if ts_dt is None: continue
            if days and (now_dt - ts_dt).days > days: continue
            row = {"ts": ts_dt, "category": rec.get("category","")}
            vals = rec.get("values", {})
            if isinstance(vals, dict):
                for k, v in vals.items():
                    row[k] = parse_number(v)
            rows.append(row)

        if not rows:
            st.info("선택된 조건에 해당하는 데이터가 없습니다.")
        else:
            df = pd.DataFrame(rows).sort_values("ts")
            st.subheader("📄 표 (정렬/필터 가능)")
            st.dataframe(df, use_container_width=True, hide_index=True)

            # KPI
            st.subheader("🧾 빠른 요약")
            latest = df.iloc[-1]
            kpis = ["anc","hb","plt","wbc","na","k","ca","phos","temp_c"]
            kpi_cols = st.columns(len(kpis))
            for idx, kpi in enumerate(kpis):
                with kpi_cols[idx]:
                    val = latest.get(kpi, None)
                    if pd.notna(val):
                        st.metric(kpi.upper(), f"{val:.2f}" if isinstance(val, (int,float)) else val)

            # 차트
            st.subheader("📈 추세 차트")
            chart_cols = st.columns(2)

            def plot_line(col, series_name):
                with col:
                    if series_name in df.columns:
                        sub = df[["ts", series_name]].dropna()
                        if len(sub) >= 1:
                            sub = sub.set_index("ts")
                            st.line_chart(sub, height=220)
                        else:
                            st.caption(f"{series_name.upper()} 데이터 없음")

            plot_line(chart_cols[0], "anc")
            plot_line(chart_cols[1], "hb")
            chart_cols2 = st.columns(2)
            plot_line(chart_cols2[0], "plt")
            plot_line(chart_cols2[1], "wbc")

            # ANC 예측표(뷰어에서도 제공)
            st.subheader("🧮 ANC 예측표 (항암 환자용, 2일 이상 누적 시)")
            res, err = anc_prediction_table(pick_nick, "항암 환자용")
            if err:
                st.caption("예측 불가: " + err)
            else:
                hist_df, pred_df, rate = res
                st.write(f"최근 상승 속도: **{rate:.1f} /일**")
                st.write("최근 측정 히스토리:")
                st.dataframe(hist_df, use_container_width=True, hide_index=True)
                st.write("예상 도달:")
                st.dataframe(pred_df, use_container_width=True, hide_index=True)

            # CSV
            st.subheader("⬇️ 내보내기")
            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("CSV 다운로드", data=csv, file_name=f"{pick_nick}_history.csv", mime="text/csv")

# ============================================================
# 🧪 해석기
# ============================================================
else:
    # 사이드바 카테고리
    category = st.sidebar.radio(
        "카테고리 선택 (환자 유형을 골라주세요)",
        [
            "항암 환자용 (전체 수치 + 발열 해석)",
            "항암제 (약물별 부작용/주의사항)",
            "투석 환자 (소변량·전해질 중심)",
            "당뇨 (혈당·HbA1c 해석)",
            "기본(일반) (WBC/Hb/PLT/ANC + 발열, 교차 복용)"
        ],
        key="category_v76"
    )

    # 저장 대기 버퍼
    if "pending_save" not in st.session_state:
        st.session_state["pending_save"] = None

    def confirm_save_ui(pending):
        st.markdown("---")
        st.subheader("💾 저장하시겠습니까?")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✅ 네, 저장하기", key="btn_confirm_save_yes"):
                ok = save_record(pending["nickname"], pending["category"], pending["values"])
                if ok:
                    st.success("기록 저장 완료! (기록 뷰어에서 확인 가능)")
                else:
                    st.error("별명이 비어 있어 저장하지 못했습니다.")
                st.session_state["pending_save"] = None
        with col_b:
            if st.button("취소", key="btn_confirm_save_no"):
                st.info("저장을 취소했습니다.")
                st.session_state["pending_save"] = None

    # 항암 환자용
    if category.startswith("항암 환자용"):
        st.header("🧬 항암 환자용 해석")
        LABS_FULL = [
            ("WBC (백혈구)", "wbc"), ("Hb (헤모글로빈)", "hb"), ("혈소판 (PLT)", "plt"),
            ("ANC (호중구)", "anc"), ("Ca²⁺ (칼슘)", "ca"), ("Phosphorus (P, 인)", "phos"), ("Na⁺ (소디움)", "na"),
            ("K⁺ (포타슘)", "k"), ("Albumin (알부민)", "alb"), ("Glucose (혈당)", "glu"),
            ("Total Protein", "tp"), ("AST", "ast"), ("ALT", "alt"), ("LDH", "ldh"),
            ("CRP", "crp"), ("Creatinine (Cr)", "cr"), ("Total Bilirubin (TB)", "tb"),
            ("BUN", "bun"), ("BNP", "bnp"), ("UA (요산)", "ua"),
        ]
        cols = st.columns(3)
        for i, (label, slug) in enumerate(LABS_FULL):
            with cols[i % 3]:
                text_num_input(label, key=f"hx_{slug}_v76", placeholder="예: 3.5")
        fever_c = text_num_input("현재 체온(℃)", key="hx_fever_temp_c_v76", placeholder="예: 38.2")
        st.divider()
        if st.button("해석하기", key="btn_cancer_v76"):
            entered = {}
            for _, slug in LABS_FULL:
                v = float(st.session_state.get(f"hx_{slug}_v76__val", 0) or 0)
                if v != 0:
                    entered[slug] = v
            temp = float(st.session_state.get("hx_fever_temp_c_v76__val", 0) or 0)
            nickname_cur = nickname  # capture

            md = []
            add_line(md, f"# 항암 환자 해석 ({now_str()})")
            add_line(md, CREDIT)
            if entered:
                section(md, "입력한 수치")
                for k, v in entered.items():
                    bullet(md, f"**{k.upper()}**: {v}")
            if temp:
                bullet(md, f"**체온**: {temp:.1f}℃")
                entered["temp_c"] = temp

            section(md, "요약 해석")
            anc = entered.get("anc")
            if anc is not None and anc < 500:
                st.error("호중구 낮음(ANC<500): 감염위험 매우 높음")
            # ANC 주의 즉시
            show_anc_caution(anc if anc is not None else 0)
            alb = entered.get("alb")
            hb = entered.get("hb")
            k_val = entered.get("k")
            na_val = entered.get("na")
            ca_val = entered.get("ca")
            p_val  = entered.get("phos")
            # 음식 추천
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
            if p_val is not None and p_val < 2.5:
                food_items.append(("인(P) 낮음", FOOD_RECS["p_low"]))
                bullet(md, f"인(P) 낮음 → 권장식품: {', '.join(FOOD_RECS['p_low'])}")
            if food_items:
                st.markdown("---")
                show_food_recs("맞춤 식단 제안", food_items)

            # 발열 가이드
            if temp:
                if temp >= 39.0: st.error("체온 39.0℃ 이상: 즉시 의료기관 방문 권장.")
                elif temp >= 38.5: st.warning("체온 38.5℃ 이상: 병원 연락 권장.")
                elif temp >= 38.0: st.info("체온 38.0~38.5℃: 해열제 복용 및 경과 관찰.")
                st.info(FEVER_GUIDE)

            # ANC 예측표 (이미 저장된 이력 기준, 2일 이상이면 표시)
            st.markdown("---")
            st.subheader("🧮 ANC 예측표 (저장된 기록 기준)")
            res, err = anc_prediction_table(nickname_cur, "항암 환자용")
            if err:
                st.caption("예측 불가: " + err + "  ※ '항암 환자용' 카테고리로 최소 2일 이상 간격의 기록 두 건이 필요합니다.")
            else:
                hist_df, pred_df, rate = res
                st.write(f"최근 상승 속도: **{rate:.1f} /일**")
                st.write("최근 측정 히스토리:")
                st.dataframe(hist_df, use_container_width=True, hide_index=True)
                st.write("예상 도달:")
                st.dataframe(pred_df, use_container_width=True, hide_index=True)

            # 저장 여부 확인 UI
            st.session_state["pending_save"] = {
                "nickname": nickname_cur,
                "category": "항암 환자용",
                "values": entered
            }
            confirm_save_ui(st.session_state["pending_save"])

    # 항암제
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
                text_num_input(f"{label} (용량/개수)", key=f"dose_{slug}_v76", placeholder="예: 1 / 2.5 / 50")
        st.checkbox("최근 이뇨제 사용", key="flag_diuretic_v76")
        st.divider()
        if st.button("해석하기", key="btn_chemo_v76"):
            md = []
            add_line(md, f"# 항암제 해석 ({now_str()})")
            add_line(md, CREDIT)
            used_any = False
            entered = {}
            for _, slug in DRUGS:
                v = float(st.session_state.get(f"dose_{slug}_v76__val", 0) or 0)
                if v != 0:
                    used_any = True
                    st.write(f"• **{slug.upper()}**: {v}")
                    entered[slug] = v
            if not used_any:
                st.info("입력된 항암제 용량이 없습니다.")
            if float(st.session_state.get("dose_vesa_v76__val", 0) or 0) > 0:
                warn_box("베사노이드: 피부/점막 증상, 광과민, 설사 가능.")
            if float(st.session_state.get("dose_arac_hdac_v76__val", 0) or 0) > 0:
                warn_box("HDAC: 신경독성/소뇌 증상, 점막염↑.")
            if float(st.session_state.get("dose_gcsf_v76__val", 0) or 0) > 0:
                warn_box("G-CSF: 골통/발열 반응 가능.")
            if st.session_state.get("flag_diuretic_v76", False):
                info_box("💧 이뇨제 병용 시 주의: 전해질 이상/탈수 위험. 수분 및 검사 필요.")

            # 저장 여부 확인 UI
            st.session_state["pending_save"] = {
                "nickname": nickname,
                "category": "항암제",
                "values": entered
            }
            confirm_save_ui(st.session_state["pending_save"])

    # 투석
    elif category.startswith("투석 환자"):
        st.header("🫁 투석 환자 해석")
        text_num_input("하루 소변량(ml)", key="urine_ml_v76", placeholder="예: 500")
        for label, slug in [("K⁺", "k"), ("Na⁺", "na"), ("Ca²⁺", "ca"), ("Phosphorus (P, 인)", "phos"),
                            ("BUN", "bun"), ("Creatinine (Cr)", "cr"), ("UA", "ua"), ("Hb", "hb"), ("Albumin", "alb")]:
            text_num_input(label, key=f"dx_{slug}_v76")
        st.divider()
        if st.button("해석하기", key="btn_dialysis_v76"):
            md = []
            add_line(md, f"# 투석 환자 해석 ({now_str()})")
            add_line(md, CREDIT)
            urine = float(st.session_state.get("urine_ml_v76__val", 0) or 0)
            add_line(md, f"- 소변량: {int(urine)} ml/day")
            # 저장할 값 구성
            entered = {
                "urine_ml": urine,
                "k": float(st.session_state.get("dx_k_v76__val", 0) or 0),
                "na": float(st.session_state.get("dx_na_v76__val", 0) or 0),
                "ca": float(st.session_state.get("dx_ca_v76__val", 0) or 0),
                "phos": float(st.session_state.get("dx_phos_v76__val", 0) or 0),
                "bun": float(st.session_state.get("dx_bun_v76__val", 0) or 0),
                "cr": float(st.session_state.get("dx_cr_v76__val", 0) or 0),
                "ua": float(st.session_state.get("dx_ua_v76__val", 0) or 0),
                "hb": float(st.session_state.get("dx_hb_v76__val", 0) or 0),
                "alb": float(st.session_state.get("dx_alb_v76__val", 0) or 0),
            }
            p = entered.get("phos", 0)
            if p and p > 5.5:
                warn_box("인(P) 높음(>5.5 mg/dL): 고인혈증 — 인이 많은 식품 제한 및 인결합제 복용 여부는 주치의 지시에 따르세요.")
            elif p and p < 3.0:
                info_box("인(P) 낮음(<3.0 mg/dL): 단백질/인지원 식품 보강 필요할 수 있음(우유/달걀/생선/두부 등).")

            # 저장 여부 확인 UI
            st.session_state["pending_save"] = {
                "nickname": nickname,
                "category": "투석 환자",
                "values": entered
            }
            confirm_save_ui(st.session_state["pending_save"])

    # 당뇨
    elif category.startswith("당뇨"):
        st.header("🍚 당뇨 해석")
        fpg = text_num_input("식전 혈당", key="dm_fpg_v76", placeholder="예: 95")
        ppg = text_num_input("식후 혈당", key="dm_ppg_v76", placeholder="예: 160")
        a1c = text_num_input("HbA1c (%)", key="dm_hba1c_v76", placeholder="예: 6.3")
        st.divider()
        if st.button("해석하기", key="btn_dm_v76"):
            md = []
            add_line(md, f"# 당뇨 해석 ({now_str()})")
            add_line(md, CREDIT)
            if fpg: bullet(md, f"식전: {fpg}")
            if ppg: bullet(md, f"식후: {ppg}")
            if a1c: bullet(md, f"HbA1c: {a1c}%")

            # 저장 여부 확인 UI
            entered = {"fpg": fpg, "ppg": ppg, "hba1c": a1c}
            st.session_state["pending_save"] = {
                "nickname": nickname,
                "category": "당뇨",
                "values": entered
            }
            confirm_save_ui(st.session_state["pending_save"])

    # 기본(일반)
    else:
        st.header("🩸 기본(일반)")
        LABS_SIMPLE = [("WBC", "wbc"), ("Hb", "hb"), ("혈소판", "plt"), ("ANC", "anc")]
        cols = st.columns(4)
        for i, (label, slug) in enumerate(LABS_SIMPLE):
            with cols[i % 4]:
                text_num_input(label, key=f"lab_{slug}_v76", placeholder="예: 3.4 / 10.2 / 80")
        fever_c = text_num_input("현재 체온(℃)", key="fever_temp_c_v76", placeholder="예: 38.3")
        st.divider()
        if st.button("해석하기", key="btn_general_simple_v76"):
            entered = {}
            for _, slug in LABS_SIMPLE:
                v = float(st.session_state.get(f"lab_{slug}_v76__val", 0) or 0)
                if v != 0:
                    entered[slug] = v
            temp = float(st.session_state.get("fever_temp_c_v76__val", 0) or 0)
            if temp:
                entered["temp_c"] = temp

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
            show_anc_caution(anc if anc is not None else 0)
            if temp:
                if temp >= 39.0: st.error("체온 39.0℃ 이상: 즉시 내원")
                elif temp >= 38.5: st.warning("체온 38.5℃ 이상: 병원 연락")
                elif temp >= 38.0: st.info("체온 38.0~38.5℃: 해열제 복용 및 경과관찰")
                st.info(FEVER_GUIDE)

            # 저장 여부 확인 UI
            st.session_state["pending_save"] = {
                "nickname": nickname,
                "category": "기본(일반)",
                "values": entered
            }
            confirm_save_ui(st.session_state["pending_save"])

# ============================================================
# 하단 면책
# ============================================================
st.markdown(
    """
> ⚠️ 이 도구는 교육/자가관리 보조용입니다.  
> **최종 의사결정은 반드시 주치의가 승인**해야 합니다.
    """
)

