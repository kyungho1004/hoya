def interpret_labs(vals, extras):
    res = []
    anc = vals.get("ANC(호중구)")
    hb = vals.get("Hb")
    plt = vals.get("혈소판(PLT)")
    crp = vals.get("CRP")
    if anc is not None and float(anc) < 500:
        res.append("호중구 낮음 → 생야채 금지 / 익힌 음식 권장")
    if hb is not None and float(hb) < 8.0:
        res.append("Hb 낮음 → 빈혈 증상 주의")
    if plt is not None and float(plt) < 50:
        res.append("혈소판 낮음 → 출혈 주의")
    if crp is not None and float(crp) >= 1.0:
        res.append("CRP 상승 가능 → 감염 의심 시 병원 연락")
    return res or ["특이 위험 신호 없음 (참고용)"]

def compare_with_previous(nickname, current_vals):
    # 실제 구현은 저장소 필요. 데모 메시지:
    return [f"{nickname}의 이전 기록과 비교 기능은 다음 업데이트에서 활성화됩니다."]

def food_suggestions(vals, anc_place):
    tips = []
    if vals.get("Albumin") and float(vals["Albumin"]) < 3.0:
        tips.append("알부민 낮음: 달걀, 연두부, 흰살 생선, 닭가슴살, 귀리죽")
    if vals.get("K(포타슘)") and float(vals["K(포타슘)"]) < 3.5:
        tips.append("칼륨 낮음: 바나나, 감자, 호박죽, 고구마, 오렌지")
    if vals.get("Hb") and float(vals["Hb"]) < 8.0:
        tips.append("Hb 낮음: 소고기, 시금치, 두부, 달걀 노른자, 렌틸콩")
    if vals.get("Na(소디움)") and float(vals["Na(소디움)"]) < 135:
        tips.append("나트륨 낮음: 전해질 음료, 미역국, 바나나, 오트밀죽, 삶은 감자")
    if vals.get("Ca(칼슘)") and float(vals["Ca(칼슘)"]) < 8.5:
        tips.append("칼슘 낮음: 연어통조림, 두부, 케일, 브로콜리")
    if anc_place == "가정" and vals.get("ANC(호중구)") and float(vals["ANC(호중구)"]) < 500:
        tips.append("호중구 낮음 가이드: 생채소 금지, 조리 후 2시간 지나면 재섭취 금지, 멸균식품 권장")
    return tips

def summarize_meds(meds):
    lines = []
    for k, info in meds.items():
        if k in ("MTX","Methotrexate"):
            lines.append("MTX: 간수치 상승/구내염/골수억제 — 엽산, 구강위생 주의")
        elif k in ("ATRA",):
            lines.append("ATRA: 분화증후군(DS) 주의, 호흡곤란/발열 시 병원")
        elif k in ("ARA-C",):
            form = info.get("form", "제형 미선택")
            lines.append(f"ARA-C({form}): 용량·제형별 신경독성/골수억제 주의")
        elif k in ("G-CSF",):
            lines.append("G-CSF: 골통 등 통증 가능, 고열 시 감염 평가")
        else:
            lines.append(f"{k}: {info}")
    return lines

def abx_summary(abx_dict):
    return [f"{k}: {v} 회" for k, v in abx_dict.items()]
