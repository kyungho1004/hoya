import streamlit as st

st.set_page_config(page_title="혈액검사 해석기", layout="centered")
st.title("🔬 항암치료 환자를 위한 혈액검사 해석기")
st.caption("버전: 공유용 / 모든 수치는 의사와 상담 없이 단독 해석에 사용하지 마세요.")
st.markdown("---")

with st.form("lab_form"):
    st.subheader("🩸 기본 혈액 수치 입력")
    wbc = st.number_input("1. 백혈구 (WBC)", min_value=0.0)
    hb = st.number_input("2. 적혈구 (Hb)", min_value=0.0)
    plt = st.number_input("3. 혈소판", min_value=0.0)
    anc = st.number_input("4. 호중구 (ANC)", min_value=0.0)
    ca = st.number_input("5. 칼슘 (Ca)", min_value=0.0)
    na = st.number_input("6. 소디움 (Na)", min_value=0.0)
    k = st.number_input("7. 포타슘 (K)", min_value=0.0)
    alb = st.number_input("8. 알부민", min_value=0.0)
    glu = st.number_input("9. 혈당 (Glucose)", min_value=0.0)
    tp = st.number_input("10. 총단백 (TP)", min_value=0.0)
    ast = st.number_input("11. AST", min_value=0.0)
    alt = st.number_input("12. ALT", min_value=0.0)
    ldh = st.number_input("13. LDH", min_value=0.0)
    crp = st.number_input("14. CRP", min_value=0.0)
    cr = st.number_input("15. 크레아티닌 (Cr)", min_value=0.0)
    ua = st.number_input("16. 요산 (UA)", min_value=0.0)
    tb = st.number_input("17. 총빌리루빈 (TB)", min_value=0.0)
    bun = st.number_input("18. BUN", min_value=0.0)
    bnp = st.number_input("19. BNP", min_value=0.0)

    st.subheader("💊 복용 중인 항암제 (알약/주사 횟수 입력)")
    mp = st.number_input("6-MP (알약 수)", min_value=0.0)
    mtx = st.number_input("MTX (알약 수)", min_value=0.0)
    vesanoid = st.number_input("베사노이드 (알약 수)", min_value=0.0)
    arac = st.number_input("아라씨 (ARA-C)", min_value=0.0)
    gcsf = st.number_input("그라신 (G-CSF)", min_value=0.0)

    submitted = st.form_submit_button("해석하기")

if submitted:
    st.markdown("---")
    st.subheader("🧪 혈액 수치 요약")
    if anc < 500:
        st.warning(f"ANC {anc} → 호중구 매우 낮음 → 감염 고위험")
    if hb < 8.0:
        st.warning(f"Hb {hb} → 중등도 빈혈")
    if plt < 50:
        st.warning(f"혈소판 {plt} → 출혈 위험")
    if alb < 3.0:
        st.info(f"알부민 {alb} → 영양 상태 불량")
    if ast > 80 or alt > 80:
        st.warning("간수치(AST/ALT) 상승 → 간 기능 저하 의심")
    if crp > 0.5:
        st.warning(f"CRP {crp} → 염증 or 감염 의심")
    if k < 3.3:
        st.warning(f"칼륨 {k} → 저칼륨혈증 (심장 리스크)")
    if bnp > 200:
        st.warning(f"BNP {bnp} → 심장 부담 or 수분 과다")
    if bun > 25 and cr < 1.2:
        st.info(f"BUN {bun}, Cr {cr} → 탈수 가능성")

    st.subheader("💊 항암제 부작용 요약")
    if mp > 0:
        st.write("- 6-MP: 간수치 상승, 골수억제(호중구↓), 구내염 주의")
    if mtx > 0:
        st.write("- MTX: 간독성, 신장독성, 점막염, 피부발진, 탈모 가능")
    if vesanoid > 0:
        st.write("- 베사노이드: RA증후군, 발열, 호흡곤란, 피부 벗겨짐 가능")
    if arac > 0:
        st.write("- 아라씨(ARA-C): 고열, 구토, 설사, 피부염, 간기능 저하 가능")
    if gcsf > 0:
        st.write("- 그라신(G-CSF): 골수통증, 발열, 일시적 백혈구 급증 가능")

    st.subheader("💡 피부 관련 부작용 안내")
    st.info("MTX, ARA-C, 베사노이드는 피부 벗겨짐, 발진, 가려움 유발 가능\n→ 증상 발생 시 보습제 사용 및 피부 자극 최소화 권장")

    st.success("✅ 입력 완료! 결과는 위에서 확인하세요.")
