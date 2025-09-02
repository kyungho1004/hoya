import streamlit as st
from datetime import datetime, date

# ===== all UI is inside main() to avoid NameError on import =====
def main():
    st.set_page_config(page_title="피수치 가이드 v3.20", layout="centered")
    st.title("🩸 피수치 가이드 v3.20")
    st.caption("제작: Hoya/GPT | 자문: Hoya/GPT")

    st.markdown("### 🔗 공유하기")
    c1, c2 = st.columns(2)
    with c1:
        st.link_button("📱 카카오톡/메신저", "https://hdzwo5ginueir7hknzzfg4.streamlit.app/")
    with c2:
        st.link_button("📝 공식 카페", "https://cafe.naver.com/bloodmap")

    st.divider()
    st.header("1️⃣ 환자/모드")
    nickname = st.text_input("별명", key="nick")
    anc_place = st.radio("식사 장소(ANC 가이드)", ["가정","병원"], horizontal=True)

    st.divider()
    st.header("2️⃣ 기본 수치 입력")
    labels = ["WBC(백혈구)","Hb(혈색소)","혈소판(PLT)","ANC(호중구)","CRP"]
    vals = {}
    for lb in labels:
        dec = 2 if lb=="CRP" else 1
        raw = st.text_input(lb, key=f"v_{lb}")
        try:
            vals[lb] = round(float(raw), dec) if raw.strip()!="" else None
        except:
            vals[lb] = None

    st.divider()
    if st.button("🔎 해석하기", use_container_width=True):
        st.subheader("📋 해석 결과")
        anc = vals.get("ANC(호중구)")
        alb = None  # placeholder if 알부민 입력 추가되면 사용
        crp = vals.get("CRP")
        out = []
        try:
            if anc is not None:
                if anc < 500:
                    out.append("🚨 ANC<500: 생야채 금지, 완전가열/전자레인지 30초+, 멸균식품 권장, 남은 음식 2시간 내 폐기.")
                elif anc < 1000:
                    out.append("⚠️ ANC<1000: 외출 최소화/위생 철저/생식 피하기.")
        except: pass
        try:
            if crp is not None and crp >= 0.5:
                out.append("⚠️ CRP 상승: 염증/감염 가능성, 발열 모니터.")
        except: pass
        if not out:
            out.append("입력값 기준 특이 경고 없음.")
        for line in out:
            st.write(line)

# keep this for direct run, but the main entry is streamlit_app.py
if __name__ == "__main__":
    main()
