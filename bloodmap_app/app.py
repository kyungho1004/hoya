
from datetime import datetime, date
import os
import math
import io

import streamlit as st

# ---- Constants & simple labels ------------------------------------------------
APP_TITLE = "피수치 가이드 · BloodMap (Subserver)"
PAGE_TITLE = "BloodMap"
MADE_BY = "제작: Hoya/GPT · 자문: Hoya/GPT"
CAFE_LINK_MD = "[📎 피수치 가이드 공식카페](https://cafe.naver.com/bloodmap)"
FOOTER_CAFE = "피드백/문의: 공식카페 이용"
DISCLAIMER = "본 자료는 보호자의 이해를 돕기 위한 참고용입니다. 모든 의학적 판단은 담당 의료진의 지시에 따르세요."
FEVER_GUIDE = "- 38.0~38.5℃: 해열제/경과관찰 · 38.5℃ 이상: 병원 연락 · 39℃ 이상: 즉시 병원"

# 기본 패널 표시 순서/라벨
LBL_WBC="WBC"; LBL_Hb="Hb"; LBL_PLT="혈소판"; LBL_ANC="호중구(ANC)"
LBL_Ca="Ca"; LBL_P="P"; LBL_Na="Na"; LBL_K="K"; LBL_Alb="Albumin"
LBL_Glu="Glucose"; LBL_TP="Total Protein"; LBL_AST="AST"; LBL_ALT="ALT"; LBL_LDH="LDH"; LBL_CRP="CRP"
LBL_Cr="Creatinine"; LBL_UA="Uric Acid"; LBL_TB="Total Bilirubin"; LBL_BUN="BUN"; LBL_BNP="BNP"
ORDER=[LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K, LBL_Alb,
       LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP]

# ---- Small helpers ------------------------------------------------------------
def _entered(x):
    try:
        return x is not None and str(x) != "" and not (isinstance(x,float) and math.isnan(x))
    except Exception:
        return False

def _num_input(label, key, decimals=1, placeholder=""):
    raw = st.text_input(label, key=key, placeholder=placeholder)
    if raw is None or raw.strip()=="":
        return None
    try:
        v = float(raw.replace(",",""))
        # formatting
        if decimals==0: return int(v)
        return round(v, decimals)
    except:
        st.caption(f"⚠️ 숫자만 입력하세요: {label}")
        return None

def _line(msg):
    st.write(msg)

def _interpret(vals, extras):
    out=[]

    anc = vals.get(LBL_ANC)
    alb = vals.get(LBL_Alb)
    ca  = vals.get(LBL_Ca)
    crp = vals.get(LBL_CRP)

    if _entered(anc):
        if float(anc) < 500:
            out.append("🚨 **호중구(ANC) 극저하**: 생야채/회/비살균 식품 금지, 모든 음식 **충분 가열(전자레인지 30초+)**·멸균식품 권장 · 남은 음식 2시간 이후 섭취 금지")
        elif float(anc) < 1000:
            out.append("⚠️ **호중구 낮음**: 감염 주의, 외출/접촉 최소화 · 손위생·마스크 철저")

    if _entered(alb) and float(alb) < 3.0:
        out.append("⚠️ **알부민 낮음**: 단백질 보충(달걀·연두부·흰살생선·닭가슴살·귀리죽)")

    if _entered(ca) and float(ca) < 8.5:
        out.append("⚠️ **칼슘 낮음**: 연어통조림·두부·케일·브로콜리 권장 (참깨 제외)")

    if _entered(crp) and float(crp) >= 1.0:
        out.append("⚠️ **CRP 상승**: 염증/감염 가능성, 임상경과/발열 동반 여부 확인")

    # Diuretic hints
    if extras.get("diuretic_amt"):
        bun = vals.get(LBL_BUN); cr = vals.get(LBL_Cr); k = vals.get(LBL_K); na = vals.get(LBL_Na)
        notes=[]
        try:
            if _entered(bun) and _entered(cr) and float(cr) > 0:
                ratio = float(bun)/float(cr)
                if ratio>=20: notes.append("BUN/Cr 상승 → 탈수 의심")
        except: pass
        try:
            if _entered(k) and float(k)<3.5: notes.append("저칼륨 주의")
            if _entered(na) and float(na)<135: notes.append("저나트륨 주의")
        except: pass
        if notes:
            out.append("💧 **이뇨제 관련 체크**: " + " · ".join(notes))

    # Urine special
    ur = extras.get("urine",{})
    if ur:
        u_notes=[]
        if _entered(ur.get("RBC")) and float(ur["RBC"])>0: u_notes.append("현미경적 혈뇨(+?)")
        if _entered(ur.get("Protein")) and float(ur["Protein"])>0: u_notes.append("단백뇨")
        if _entered(ur.get("Nitrite")) and int(ur["Nitrite"])==1: u_notes.append("니트라이트 양성(요로감염 의심)")
        if _entered(ur.get("LE")) and int(ur["LE"])==1: u_notes.append("백혈구에스테라제 양성")
        if _entered(ur.get("ACR")) and float(ur["ACR"])>=30: u_notes.append("미세알부민뇨(ACR≥30)")
        if u_notes:
            out.append("🟦 **소변 특수검사 소견**: " + " · ".join(u_notes))

    # Complement
    comp = extras.get("complement",{})
    if comp:
        c_notes=[]
        if _entered(comp.get("C3")) and float(comp["C3"])<90: c_notes.append("C3 낮음")
        if _entered(comp.get("C4")) and float(comp["C4"])<10: c_notes.append("C4 낮음")
        if c_notes:
            out.append("🟪 **보체(C3/C4) 참고**: " + " · ".join(c_notes))

    if not out:
        out.append("✅ 특이 소견 없음(입력값 기준). 변동 시 의료진과 상의하세요.")
    return out

def _food(vals, anc_place):
    out=[]
    anc = vals.get(LBL_ANC)
    if _entered(anc) and float(anc)<1000:
        if anc_place=="가정":
            out.append("- **ANC 낮음·가정**: 생식 금지, 모든 음식 완전가열, 유통기한/보관 온도 준수")
        else:
            out.append("- **ANC 낮음·병원**: 보호자 반입 음식 가열·밀봉, 남은 음식 폐기")
    alb = vals.get(LBL_Alb)
    if _entered(alb) and float(alb)<3.0:
        out.append("- **알부민 보강 음식(5)**: 달걀, 연두부, 흰살 생선, 닭가슴살, 귀리죽")
    ca = vals.get(LBL_Ca)
    if _entered(ca) and float(ca)<8.5:
        out.append("- **칼슘 보강 음식(5)**: 연어통조림, 두부, 케일, 브로콜리, 저지방 우유")
    return out

def _summarize_meds(meds):
    out=[]
    for k, info in (meds or {}).items():
        low = k.lower()
        if "mtx" in low or k=="MTX":
            out.append("MTX: 구내염·간독성·골수억제 주의, NSAIDs/PCP 계열 상호작용")
        if k=="ATRA":
            out.append("ATRA(베사노이드): 분화증후군(발열/호흡곤란/부종) 즉시 병원, 임신금기")
        if k in ["G-CSF","Filgrastim","Pegfilgrastim"]:
            out.append("G-CSF: 골통/미열 흔함, 과도한 백혈구 상승 모니터")
        if k=="ARA-C":
            form = info.get("form","")
            if "고용량" in form:
                out.append("ARA-C(HDAC): 신경독성/결막염 주의, 스테로이드 점안 고려")
            else:
                out.append("ARA-C: 골수억제·오심·발열 반응 가능")
    return out

def _abx_summary(abx_dict):
    out=[]
    for cat, dose in (abx_dict or {}).items():
        if "Fluoroquinolone" in cat:
            out.append("플루오로퀴놀론: QT 연장·광과민, 제산제/와파린 상호작용")
        if "Macrolide" in cat:
            out.append("마크롤라이드: QT 연장, CYP3A4 상호작용")
        if "Cephalosporin" in cat:
            out.append("세팔로스포린: 알레르기 교차반응 주의")
    return out

def _build_report(mode, meta, vals, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines):
    lines=[]
    lines.append(f"# BloodMap 보고서 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    lines.append("제작: Hoya/GPT · 자문: Hoya/GPT")
    lines.append("")
    if meta.get("nickname_key"):
        lines.append(f"- 사용자: {meta.get('nickname_key')}")
    lines.append(f"- 모드: {mode}")
    if meta.get("group"): lines.append(f"- 그룹/암종: {meta.get('group')} / {meta.get('cancer')}")
    if meta.get("anc_place"): lines.append(f"- 식사 장소: {meta.get('anc_place')}")
    lines.append("")
    if vals:
        lines.append("## 입력 수치")
        for k in ORDER:
            v = vals.get(k)
            if _entered(v): lines.append(f"- {k}: {v}")
    if extra_vals:
        lines.append("## 특수검사/추가")
        for k, v in extra_vals.items():
            if _entered(v): lines.append(f"- {k}: {v}")
    if cmp_lines:
        lines.append("## 수치 변화 비교")
        for l in cmp_lines: lines.append(f"- {l}")
    if meds_lines:
        lines.append("## 약물 요약")
        for l in meds_lines: lines.append(f"- {l}")
    if abx_lines:
        lines.append("## 항생제 주의")
        for l in abx_lines: lines.append(f"- {l}")
    if food_lines:
        lines.append("## 식이 가이드")
        for l in food_lines: lines.append(f"- {l}")
    lines.append("")
    lines.append("## 발열 가이드")
    lines.append(FEVER_GUIDE)
    lines.append("")
    lines.append("> " + DISCLAIMER)
    return "\\n".join(lines)

def render_graphs():
    if "records" not in st.session_state or not st.session_state["records"]:
        return
    st.markdown("---")
    st.subheader("📈 추이 그래프")
    try:
        import pandas as pd
        rows=[]
        for nick, recs in st.session_state["records"].items():
            for r in recs:
                ts = r.get("ts")
                row={"별명": nick, "ts": ts}
                labs = (r.get("labs") or {})
                for k in [LBL_WBC, LBL_Hb, LBL_PLT, LBL_CRP, LBL_ANC]:
                    row[k]=labs.get(k)
                rows.append(row)
        if not rows:
            st.info("그래프화할 데이터가 없습니다.")
            return
        df = pd.DataFrame(rows)
        opts = ["전체"] + sorted(df["별명"].unique().tolist())
        who = st.selectbox("별명 선택", opts)
        if who != "전체":
            df = df[df["별명"]==who]
        st.line_chart(df.set_index("ts")[[LBL_WBC, LBL_Hb, LBL_PLT, LBL_CRP, LBL_ANC]])
    except Exception as e:
        st.caption("그래프를 표시하려면 pandas가 필요합니다.")

def render_schedule(nickname_key):
    st.markdown("### 📅 항암 스케줄(간단 메모)")
    if "schedules" not in st.session_state:
        st.session_state["schedules"]={}
    txt = st.text_area("스케줄 메모", key=f"sched_{nickname_key}", placeholder="예: D1 ARA-C, D3 G-CSF 시작 ...")
    if st.button("스케줄 저장", key=f"save_sched_{nickname_key}"):
        st.session_state["schedules"][nickname_key]=txt
        st.success("스케줄 메모 저장됨")

def main():
    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    st.title(APP_TITLE)
    st.caption(MADE_BY)
    st.markdown(CAFE_LINK_MD)

    # CSS
    try:
        st.markdown("<style>" + open("assets/style.css","r",encoding="utf-8").read() + "</style>", unsafe_allow_html=True)
    except Exception:
        pass

    # 공유/카운터
    st.markdown("### 🔗 공유하기")
    c1, c2, c3 = st.columns([1,1,2])
    with c1:
        st.link_button("📱 카카오톡/메신저", "https://hdzwo5ginueir7hknzzfg4.streamlit.app/")
    with c2:
        st.link_button("📝 카페/블로그", "https://cafe.naver.com/bloodmap")
    with c3:
        st.code("https://hdzwo5ginueir7hknzzfg4.streamlit.app/", language="text")
    st.caption("✅ 모바일 줄꼬임 방지 · 별명 저장/그래프 · 암별 패널 · PDF/TXT/MD · ANC 가이드")

    # 세션 준비
    if "records" not in st.session_state: st.session_state["records"]={}
    if "schedules" not in st.session_state: st.session_state["schedules"]={}

    # 1) 환자/모드
    st.divider()
    st.header("1️⃣ 환자/암 정보")
    c1, c2 = st.columns(2)
    with c1:
        nickname = st.text_input("별명", placeholder="예: 홍길동")
    with c2:
        pin = st.text_input("PIN(4자리)", max_chars=4, placeholder="예: 1234")
    if pin and (not pin.isdigit() or len(pin)!=4):
        st.warning("PIN은 숫자 4자리로 입력하세요.")
    test_date = st.date_input("검사 날짜", value=date.today())
    anc_place = st.radio("현재 식사 장소(ANC 가이드용)", ["가정", "병원"], horizontal=True)

    group = st.selectbox("암 그룹", ["미선택/일반","혈액암","고형암","육종","소아암","희귀암"])
    cancer = None
    if group=="혈액암":
        cancer = st.selectbox("혈액암", ["AML","APL","ALL","CML","CLL"])
    elif group=="고형암":
        cancer = st.selectbox("고형암", [
            "폐암(Lung cancer)","유방암(Breast cancer)","위암(Gastric cancer)",
            "대장암(Cololoractal cancer)","간암(HCC)","췌장암(Pancreatic cancer)",
            "담도암(Cholangiocarcinoma)","자궁내막암(Endometrial cancer)",
            "구강암/후두암","피부암(흑색종)","신장암(RCC)",
            "갑상선암","난소암","자궁경부암","전립선암","뇌종양(Glioma)","식도암","방광암"
        ])

    elif group=="육종":
        cancer = st.selectbox("육종(진단명으로 선택)", [
            "골육종(Osteosarcoma)","연골육종(Chondrosarcoma)","유윙육종(Ewing sarcoma)",
            "지방육종(Liposarcoma)","평활근육종(Leiomyosarcoma)","횡문근육종(Rhabdomyosarcoma)",
            "윤활막육종(Synovial sarcoma)","혈관육종(Angiosarcoma)","섬유육종(Fibrosarcoma)",
            "악성말초신경초종(MPNST)","복막/후복막육종(Retroperitoneal STS)"
        ])

    elif group=="소아암":
        cancer = st.selectbox("소아암", ["Neuroblastoma","Wilms tumor"])
    elif group=="희귀암":
        cancer = st.selectbox("희귀암", [
            "담낭암(Gallbladder cancer)","부신암(Adrenal cancer)","망막모세포종(Retinoblastoma)",
            "흉선종/흉선암(Thymoma/Thymic carcinoma)","신경내분비종양(NET)",
            "간모세포종(Hepatoblastoma)","비인두암(NPC)","GIST"
        ])
    nickname_key = (nickname.strip() + "#" + pin.strip()) if (nickname and pin and pin.isdigit() and len(pin)==4) else nickname.strip()

    # 2) 기본 패널
    st.divider()
    st.header("2️⃣ 기본 혈액 검사 수치 (입력한 값만 해석)")
    vals={}
    def _render_inputs():
        left, right = st.columns(2)
        half = (len(ORDER)+1)//2
        with left:
            for name in ORDER[:half]:
                dec = 2 if name==LBL_CRP else (1 if name in [LBL_WBC,LBL_ANC,LBL_AST,LBL_ALT,LBL_LDH,LBL_BNP,LBL_Glu] else 1)
                vals[name]=_num_input(name, key=f"v_{name}", decimals=dec, placeholder="예: 0.12" if name==LBL_CRP else "예: 1200" if name in [LBL_WBC,LBL_ANC] else "예: 3.5")
        with right:
            for name in ORDER[half:]:
                dec = 2 if name==LBL_CRP else (1 if name in [LBL_WBC,LBL_ANC,LBL_AST,LBL_ALT,LBL_LDH,LBL_BNP,LBL_Glu] else 1)
                vals[name]=_num_input(name, key=f"r_{name}", decimals=dec, placeholder="예: 0.12" if name==LBL_CRP else "예: 1200" if name in [LBL_WBC,LBL_ANC] else "예: 3.5")
    _render_inputs()

    # 3) 특수검사(토글) - 소변/보체 + 암별 마커 일부
    st.divider()
    with st.expander("3️⃣ 🔬 특수검사(소변/보체/암별 마커)", expanded=False):
        st.caption("자주 나가지 않는 검사들은 토글로 묶었습니다.")
        # Urine
        st.markdown("**소변 특수검사**")
        ucols = st.columns(5)
        with ucols[0]:
            u_rbc = _num_input("RBC(/HPF)", key="u_rbc", decimals=0, placeholder="예: 5")
        with ucols[1]:
            u_pro = _num_input("단백뇨(g/L)", key="u_pro", decimals=1, placeholder="예: 0.3")
        with ucols[2]:
            u_nit = _num_input("Nitrite(0/1)", key="u_nit", decimals=0, placeholder="0 또는 1")
        with ucols[3]:
            u_le  = _num_input("Leukocyte esterase(0/1)", key="u_le", decimals=0, placeholder="0 또는 1")
        with ucols[4]:
            u_acr = _num_input("미세알부민/Cr(ACR)", key="u_acr", decimals=1, placeholder="예: 35")

        # Complement
        st.markdown("**보체 검사**")
        ccols = st.columns(2)
        with ccols[0]:
            c3 = _num_input("C3(mg/dL)", key="c3", decimals=0, placeholder="예: 85")
        with ccols[1]:
            c4 = _num_input("C4(mg/dL)", key="c4", decimals=0, placeholder="예: 9")

        # Tumor markers (간단)
        st.markdown("**암별 마커(간단)**")
        mcols = st.columns(4)
        with mcols[0]: cea = _num_input("CEA(ng/mL)", key="mk_cea", decimals=1, placeholder="예: 3.1")
        with mcols[1]: ca199 = _num_input("CA19-9(U/mL)", key="mk_ca199", decimals=1, placeholder="예: 27")
        with mcols[2]: afp = _num_input("AFP(ng/mL)", key="mk_afp", decimals=1, placeholder="예: 12")
        with mcols[3]: dd = _num_input("D-dimer(µg/mL FEU)", key="mk_dd", decimals=2, placeholder="예: 0.60")
        # Sarcoma-specific markers
        if group == "육종":
            st.markdown("**육종 특이 마커**")
            scols = st.columns(2)
            with scols[0]:
                sar_alp = _num_input("ALP(U/L)", key="sar_alp", decimals=0, placeholder="예: 120")
            with scols[1]:
                sar_ck = _num_input("CK(U/L)", key="sar_ck", decimals=0, placeholder="예: 180")


    # 4) 약물/상태(간단)
    st.divider()
    st.header("4️⃣ 약물/상태 입력")
    meds={}
    abx={}
    ara_sel = st.selectbox("ARA-C 제형", ["선택안함","정맥(IV)","피하(SC)","고용량(HDAC)"])
    if ara_sel!="선택안함":
        dose = _num_input("ARA-C 용량/일", key="ara_d", decimals=1, placeholder="예: 100")
        if _entered(dose):
            meds["ARA-C"]={"form": ara_sel, "dose": dose}
    atra_caps = _num_input("ATRA(캡슐 개수/일)", key="atra", decimals=0, placeholder="예: 2")
    if _entered(atra_caps):
        meds["ATRA"]={"tabs": atra_caps}
    mtx_tabs = _num_input("MTX(알약 수/일)", key="mtx", decimals=1, placeholder="예: 1.5")
    if _entered(mtx_tabs):
        meds["MTX"]={"tabs": mtx_tabs}

    abx_cat = st.selectbox("항생제 계열", ["선택안함","Fluoroquinolone","Macrolide","Cephalosporin"])
    if abx_cat!="선택안함":
        abx_d = _num_input("복용/주입량", key="abx_d", decimals=1, placeholder="예: 1")
        if _entered(abx_d): abx[abx_cat]=abx_d

    diuretic_amt = _num_input("이뇨제(복용량/회/일)", key="diuretic", decimals=1, placeholder="예: 1")

    # 버튼
    st.divider()
    run = st.button("🔎 해석하기", use_container_width=True)

    # collect extra_vals for report
    extra_vals = {}
    for k, v in [( "CEA", cea if 'cea' in locals() else None ),
                 ( "CA19-9", ca199 if 'ca199' in locals() else None ),
                 ( "AFP", afp if 'afp' in locals() else None ),
                 ( "D-dimer", dd if 'dd' in locals() else None ),
                 ( "Urine RBC", u_rbc if 'u_rbc' in locals() else None ),
                 ( "Urine Protein(g/L)", u_pro if 'u_pro' in locals() else None ),
                 ( "Nitrite", u_nit if 'u_nit' in locals() else None ),
                 ( "Leukocyte esterase", u_le if 'u_le' in locals() else None ),
                 ( "ACR", u_acr if 'u_acr' in locals() else None ),
                 ( "C3", c3 if 'c3' in locals() else None ),
                 ( "C4", c4 if 'c4' in locals() else None ),
                 ( "ALP", sar_alp if 'sar_alp' in locals() else None ),
                 ( "CK", sar_ck if 'sar_ck' in locals() else None ),
                 ]:
        if _entered(v): extra_vals[k]=v

    extras = {
        "diuretic_amt": diuretic_amt if _entered(diuretic_amt) else None,
        "abx": abx,
        "urine": {
            "RBC": u_rbc if 'u_rbc' in locals() else None,
            "Protein": u_pro if 'u_pro' in locals() else None,
            "Nitrite": u_nit if 'u_nit' in locals() else None,
            "LE": u_le if 'u_le' in locals() else None,
            "ACR": u_acr if 'u_acr' in locals() else None,
        },
        "complement": {
            "C3": c3 if 'c3' in locals() else None,
            "C4": c4 if 'c4' in locals() else None,
        }
    }

    if run:
        st.subheader("📋 해석 결과")
        lines = _interpret(vals, extras)
        for l in lines: _line(l)

        meds_lines = _summarize_meds(meds)
        if meds_lines:
            st.markdown("### 💊 약물 요약")
            for l in meds_lines: _line(l)

        abx_lines = _abx_summary(abx)
        if abx_lines:
            st.markdown("### 🧪 항생제 주의 요약")
            for l in abx_lines: _line(l)

        st.markdown("### 🌡️ 발열 가이드")
        st.write(FEVER_GUIDE)

        food_lines = _food(vals, anc_place)
        if food_lines:
            st.markdown("### 🥗 음식 가이드")
            for l in food_lines: _line(l)

        meta={
            "group": group, "cancer": cancer, "anc_place": anc_place,
            "nickname_key": nickname_key
        }
        report_md = _build_report("일반/암", meta, vals, [], extra_vals, meds_lines, food_lines, abx_lines)

        st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                           mime="text/markdown")
        st.download_button("📄 보고서(.txt) 다운로드", data=report_md.encode("utf-8"),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                           mime="text/plain")

        # Save record
        if nickname_key:
            rec = {
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "mode": "일반/암",
                "group": group,
                "cancer": cancer,
                "labs": {k: vals.get(k) for k in ORDER if _entered(vals.get(k))},
                "extra": extra_vals,
                "meds": meds,
                "extras": extras,
            }
            st.session_state["records"].setdefault(nickname_key, []).append(rec)
            st.success("저장되었습니다. 아래 그래프에서 추이를 확인하세요.")
        else:
            st.info("별명과 PIN 4자리를 입력하면 기록이 구분되어 저장됩니다.")

    render_graphs()
    render_schedule(nickname_key)

    st.markdown("---")
    st.caption(FOOTER_CAFE)
    st.markdown("> " + DISCLAIMER)
