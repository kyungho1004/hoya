
def main():
    print("🔬 혈액 수치 자동 해석기 (공유용 버전)")
    print("-" * 40)

    # 혈액 수치 입력
    try:
        wbc = float(input("1. 백혈구(WBC): "))
        hb = float(input("2. 적혈구(Hb): "))
        plt = float(input("3. 혈소판: "))
        anc = float(input("4. 호중구(ANC): "))
        ca = float(input("5. 칼슘(Ca): "))
        na = float(input("6. 소디움(Na): "))
        k = float(input("7. 포타슘(K): "))
        alb = float(input("8. 알부민: "))
        glu = float(input("9. 혈당(Glucose): "))
        tp = float(input("10. 총단백(TP): "))
        ast = float(input("11. AST: "))
        alt = float(input("12. ALT: "))
        ldh = float(input("13. LDH: "))
        crp = float(input("14. CRP: "))
        cr = float(input("15. 크레아티닌(Cr): "))
        ua = float(input("16. 요산(UA): "))
        tb = float(input("17. 총빌리루빈(TB): "))
        bun = float(input("18. BUN: "))
        bnp = float(input("19. BNP: "))
    except:
        print("⚠️ 숫자만 입력하세요.")
        return

    print("\n🧪 [혈액 수치 요약]")
    if anc < 500:
        print(f"- ANC {anc}: 호중구 매우 낮음 → 감염 고위험 ⚠️")
    if hb < 8.0:
        print(f"- Hb {hb}: 중등도 빈혈 ⚠️")
    if plt < 50:
        print(f"- 혈소판 {plt}: 출혈 위험 ⚠️")
    if alb < 3.0:
        print(f"- 알부민 {alb}: 영양 상태 불량")
    if ast > 80 or alt > 80:
        print(f"- 간수치(AST/ALT) ↑ → 간 기능 저하 의심")
    if crp > 0.5:
        print(f"- CRP {crp}: 염증 or 감염 의심")
    if k < 3.3:
        print(f"- 칼륨 {k}: 저칼륨혈증 → 심장 리스크 ⚠️")
    if bnp > 200:
        print(f"- BNP {bnp}: 심장 부담 or 수분 과다 ⚠️")
    if bun > 25 and cr < 1.2:
        print(f"- BUN {bun}, Cr {cr}: 탈수 가능성 의심")

    print("\n💊 [복용 중인 항암제]")

    try:
        mp = float(input("6-MP (알약 개수): "))
        mtx = float(input("MTX (알약 개수): "))
        vesanoid = float(input("베사노이드 (알약 개수): "))
        arac = float(input("아라씨 (ARA-C, 알약 개수 또는 주사 횟수): "))
        gcsf = float(input("그라신 (G-CSF 주사 횟수): "))
    except:
        print("⚠️ 약물 용량은 숫자로 입력해주세요.")
        return

    print("\n📋 [주의할 부작용 요약]")
    if mp > 0:
        print("- 6-MP: 간수치 상승, 골수억제(호중구↓), 구내염 주의")
    if mtx > 0:
        print("- MTX: 간독성, 신장독성, 점막염, 피부발진, 탈모 가능성")
    if vesanoid > 0:
        print("- 베사노이드: RA증후군, 발열, 호흡곤란, 피부 벗겨짐 가능")
    if arac > 0:
        print("- 아라씨(ARA-C): 고열, 구토, 설사, 피부염, 간기능 저하 가능")
    if gcsf > 0:
        print("- 그라신(G-CSF): 골수통증, 열, 일시적 백혈구 급증 가능")

    print("\n💡 [피부 관련 부작용 안내]")
    print("- MTX, ARA-C, 베사노이드 등은 피부 벗겨짐, 발진, 가려움 유발 가능")
    print("- 증상 발생 시 보습제 사용 및 피부 자극 최소화 권장")

    input("\n✅ 완료되었습니다. 창을 닫으려면 Enter를 누르세요")

if __name__ == "__main__":
    main()
