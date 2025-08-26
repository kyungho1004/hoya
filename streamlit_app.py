from datetime import datetime, date  # ✅ fixed import
import streamlit as st

try:
    import pandas as pd
    HAS_PD = True
except Exception:
    HAS_PD = False

st.set_page_config(page_title="피수치 자동 해석기", layout="centered")
st.title("🩸 피수치 자동 해석기")

# --- 공통 ---
ORDER = ["WBC","Hb","PLT","ANC","Ca","P","Na","K","Albumin","Glucose","Total Protein","AST","ALT","LDH","CRP","Cr","UA","TB","BUN","BNP"]

def entered(v):
    try:
        return v is not None and float(v) > 0
    except Exception:
        return False

def parse_vals(s: str):
    s = (s or "").replace("，", ",").replace("\r\n", "\n").replace("\r", "\n").strip("\n ")
    if not s: return [None]*len(ORDER)
    if ("," in s) and ("\n" not in s):
        tokens = [tok.strip() for tok in s.split(",")]
    else:
        tokens = [line.strip() for line in s.split("\n")]
    out = []
    for i in range(len(ORDER)):
        tok = tokens[i] if i < len(tokens) else ""
        try:
            out.append(float(tok) if tok != "" else None)
        except:
            out.append(None)
    return out

def interpret_labs(vals):
    l = dict(zip(ORDER, vals))
    out=[]
    def add(s): out.append("- " + s)
    if entered(l.get("WBC")): add(f"WBC {l['WBC']}: " + ("낮음 → 감염 위험↑" if l["WBC"]<4 else "높음 → 감염/염증 가능" if l["WBC"]>10 else "정상"))
    if entered(l.get("Hb")): add(f"Hb {l['Hb']}: " + ("낮음 → 빈혈" if l["Hb"]<12 else "정상"))
    if entered(l.get("PLT")): add(f"혈소판 {l['PLT']}: " + ("낮음 → 출혈 위험" if l["PLT"]<150 else "정상"))
    if entered(l.get("ANC")): add(f"ANC {l['ANC']}: " + ("중증 감소(<500)" if l["ANC"]<500 else "감소(<1500)" if l["ANC"]<1500 else "정상"))
    if entered(l.get("Albumin")): add(f"Albumin {l['Albumin']}: " + ("낮음 → 영양/염증/간질환 가능" if l["Albumin"]<3.5 else "정상"))
    if entered(l.get("Glucose")): add(f"Glucose {l['Glucose']}: " + ("고혈당(≥200)" if l["Glucose"]>=200 else "저혈당(<70)" if l["Glucose"]<70 else "정상"))
    if entered(l.get("CRP")): add(f"CRP {l['CRP']}: " + ("상승 → 염증/감염 의심" if l["CRP"]>0.5 else "정상"))
    if entered(l.get("BUN")) and entered(l.get("Cr")) and l["Cr"]>0:
        ratio=l["BUN"]/l["Cr"]
        if ratio>20: add(f"BUN/Cr {ratio:.1f}: 탈수 의심")
        elif ratio<10: add(f"BUN/Cr {ratio:.1f}: 간질환/영양 고려")
    return out, l

# --- 입력 ---
st.header("1) 기본 정보")
date_val = st.date_input("검사 날짜", value=date.today())

st.header("2) 입력 방식 선택")
mode = st.radio("입력 방식", ["개별 칸으로 입력", "텍스트로 한 번에"], horizontal=True)

vals = [None]*len(ORDER)

with st.form("main", clear_on_submit=False):
    if mode == "개별 칸으로 입력":
        WBC = st.number_input("WBC (백혈구)", step=0.1)
        Hb = st.number_input("Hb (혈색소)", step=0.1)
        PLT = st.number_input("PLT (혈소판)", step=0.1)
        ANC = st.number_input("ANC (호중구)", step=1.0)
        Ca = st.number_input("Ca (칼슘)", step=0.1)
        P = st.number_input("P (인)", step=0.1)
        Na = st.number_input("Na (소디움)", step=0.1)
        K = st.number_input("K (포타슘)", step=0.1)
        Albumin = st.number_input("Albumin (알부민)", step=0.1)
        Glucose = st.number_input("Glucose (혈당)", step=1.0)
        TotalProtein = st.number_input("Total Protein (총단백)", step=0.1)
        AST = st.number_input("AST", step=1.0)
        ALT = st.number_input("ALT", step=1.0)
        LDH = st.number_input("LDH", step=1.0)
        CRP = st.number_input("CRP", step=0.1)
        Cr = st.number_input("Creatinine (Cr)", step=0.1)
        UA = st.number_input("Uric Acid (UA, 요산)", step=0.1)
        TB = st.number_input("Total Bilirubin (TB)", step=0.1)
        BUN = st.number_input("BUN", step=0.1)
        BNP = st.number_input("BNP (선택)", step=1.0)
    else:
        raw = st.text_area("값을 순서대로 입력 (줄바꿈/쉼표 가능)", height=160, placeholder="예) 5.2, 11.8, 180, 1200, …")
    run = st.form_submit_button("🔎 해석하기", use_container_width=True)

# --- 처리 ---
if run:
    if mode == "개별 칸으로 입력":
        mapping = {
            "WBC": WBC, "Hb": Hb, "PLT": PLT, "ANC": ANC, "Ca": Ca, "P": P, "Na": Na, "K": K,
            "Albumin": Albumin, "Glucose": Glucose, "Total Protein": TotalProtein, "AST": AST,
            "ALT": ALT, "LDH": LDH, "CRP": CRP, "Cr": Cr, "UA": UA, "TB": TB, "BUN": BUN, "BNP": BNP
        }
        vals = [mapping.get(k) for k in ORDER]
    else:
        vals = parse_vals(raw)

    lines, labs = interpret_labs(vals)

    st.subheader("📋 해석 결과")
    if lines:
        for line in lines: st.write(line)
    else:
        st.info("입력된 수치가 없습니다. 한 항목 이상 입력해 주세요.")

    # 보고서 다운로드 (✅ datetime 사용 고정)
    buf = [f"# BloodMap 보고서 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n",
           f"- 입력 방식: {mode}\n",
           f"- 검사일: {date_val}\n\n"]
    for k, v in labs.items():
        if entered(v): buf.append(f"- {k}: {v}\n")
    st.download_button("📥 보고서(.md) 다운로드",
                       data="".join(buf).encode("utf-8"),
                       file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                       mime="text/markdown")
