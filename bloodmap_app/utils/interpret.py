def interpret_labs(vals, extras):
    lines=[]
    anc=vals.get('ANC'); crp=vals.get('CRP')
    try:
        if anc is not None and float(anc)<500:
            lines.append('🔴 호중구 매우 낮음(ANC<500): 생야채 금지 · 조리식 섭취 · 외출 자제')
        if crp is not None and float(crp)>=0.5:
            lines.append('⚠️ 염증 수치 상승(추적 필요)')
    except Exception:
        pass
    return lines or ['🙂 특이 소견 없음(입력값 기준)']

def compare_with_previous(nickname, current_vals):
    # 간단 비교: 이전 값 대비 증가/감소 표기
    return []

def food_suggestions(vals, place):
    return ['- 알부민 낮을 때: 달걀, 연두부, 흰살생선, 닭가슴살, 귀리죽']

def summarize_meds(meds):
    out=[]
    for k,v in meds.items():
        if k=='ATRA':
            out.append('ATRA: 분화증후군(호흡곤란/부종) 주의 — 증상 시 즉시 병원')
        elif k=='MTX':
            out.append('MTX: 간수치 상승/구내염 주의 · 수분 충분히')
        elif k=='ARA-C':
            form=v.get('form','')
            out.append(f'ARA-C({form}): 골수억제/발열 주의')
        else:
            out.append(f'{k}: 일반적 부작용 주의')
    return out

def abx_summary(abx_dict):
    if not abx_dict: return []
    return [f"{k}: {v} 용량 입력됨" for k,v in abx_dict.items()]
