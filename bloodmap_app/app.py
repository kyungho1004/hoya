def main():
    from datetime import datetime
    import os
    import streamlit as st

    # ---- Safe config defaults ----
    try:
        from .config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE,
                             DISCLAIMER, ORDER, FEVER_GUIDE,
                             LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_CRP)
    except Exception:
        APP_TITLE='피수치 가이드 v3.15'; PAGE_TITLE='BloodMap'
        MADE_BY='제작: Hoya/GPT · 자문: Hoya/GPT'
        CAFE_LINK_MD='[📌 공식카페 바로가기](https://cafe.naver.com/bloodmap)'
        FOOTER_CAFE='피수치 가이드 공식카페 — 모두의 울타리'
        DISCLAIMER='본 자료는 보호자 참고용이며, 모든 의학적 판단은 의료진에게.'
        LBL_WBC='WBC'; LBL_Hb='Hb'; LBL_PLT='혈소판'; LBL_ANC='ANC'; LBL_CRP='CRP'
        ORDER=[LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, 'Ca','P','Na','K','Albumin','Glucose','Total Protein','AST','ALT','LDH',LBL_CRP,'Cr','UA','TB','BUN','BNP']
        FEVER_GUIDE='38.0~38.5℃ 해열제/경과, 38.5℃ 이상 병원 연락, 39℃ 즉시 병원.'

    # ---- Safe imports & fallbacks ----
    try:
        from .utils.inputs import num_input_generic, _parse_numeric
    except Exception:
        def _parse_numeric(s, decimals=1):
            if s is None or s=='': return None
            try:
                v=float(str(s).strip())
                return round(v, decimals) if decimals is not None else v
            except Exception:
                return None
        def num_input_generic(label, key=None, decimals=1, placeholder="", as_int=False):
            raw = st.text_input(label, key=key, placeholder=placeholder)
            v = _parse_numeric(raw, 0 if as_int else decimals)
            if as_int and v is not None:
                try: return int(v)
                except: return None
            return v

    try:
        from .utils.interpret import interpret_labs
    except Exception:
        def interpret_labs(vals, extras=None):
            lines=[]; anc=vals.get('ANC'); crp=vals.get('CRP')
            try:
                if anc is not None and float(anc)<500: lines.append('🔴 ANC<500: 생야채 금지 · 조리식 섭취')
                if crp is not None and float(crp)>=0.5: lines.append('⚠️ CRP 상승(추적 필요)')
            except Exception: pass
            return lines or ['🙂 특이 소견 없음(입력값 기준)']

    # ---- Compatibility shims ----
    def _num(label, *, key=None, decimals=1, placeholder="", as_int=False):
        try:
            return num_input_generic(label, key=key, decimals=decimals, placeholder=placeholder, as_int=as_int)
        except TypeError:
            try:
                return num_input_generic(label, key=key)
            except Exception:
                raw = st.text_input(label, key=key, placeholder=placeholder)
                return _parse_numeric(raw, 0 if as_int else decimals)

    def _interpret(vals, extras):
        """interpret_labs 시그니처 불일치(TypeError)까지 호환"""
        try:
            return interpret_labs(vals, extras)
        except TypeError:
            try:
                return interpret_labs(vals)
            except TypeError:
                try:
                    return interpret_labs(extras, vals)
                except Exception:
                    # 최후 안전 메세지
                    out=[]; anc=vals.get('ANC'); crp=vals.get('CRP')
                    try:
                        if anc is not None and float(anc)<500: out.append('🔴 ANC<500: 생야채 금지 · 조리식 섭취')
                        if crp is not None and float(crp)>=0.5: out.append('⚠️ CRP 상승(추적 필요)')
                    except Exception: pass
                    return out or ['🙂 특이 소견 없음(입력값 기준)']

    # ---- Page skeleton ----
    st.set_page_config(page_title=PAGE_TITLE, layout='centered')
    st.title(APP_TITLE)
    st.markdown(MADE_BY); st.markdown(CAFE_LINK_MD)

    # 공유 영역 (코드블록 복사 아이콘 대신 '읽기전용 입력상자' 사용 → 플러스/클립보드 아이콘 제거)
    st.markdown('### 🔗 공유하기')
    c1, c2 = st.columns([1,1])
    with c1: st.link_button('📱 카카오톡/메신저', 'https://hdzwo5ginueir7hknzzfg4.streamlit.app/')
    with c2: st.link_button('📝 카페/블로그', 'https://cafe.naver.com/bloodmap')
    st.text_input('웹앱 주소', value='https://hdzwo5ginueir7hknzzfg4.streamlit.app/', disabled=True)

    # 입력
    st.divider(); st.header('2️⃣ 기본 혈액 검사 수치')
    vals = {}
    for name in ORDER:
        dec = 2 if name==LBL_CRP else 1
        vals[name] = _num(name, key=f'v_{name}', decimals=dec)

    st.markdown('### 💧 동반 약물/상태')
    extras = {}
    extras['diuretic_amt'] = _num('이뇨제(복용량/회/일)', key='diuretic_amt', decimals=1, placeholder='예: 1')

    st.divider()
    if st.button('🔎 해석하기', use_container_width=True):
        lines = _interpret(vals, extras)
        for l in lines: st.write(l)
        st.markdown('### 🌡️ 발열 가이드'); st.write(FEVER_GUIDE)
        report = "\n".join(['# 피수치 가이드 보고서','- 모드: 일반/암','## 입력 수치'] + [f"- {k}: {v}" for k,v in vals.items() if v is not None])
        st.download_button('📥 보고서(.md) 다운로드', data=report.encode('utf-8'),
                           file_name=f"bloodmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                           mime='text/markdown')

    st.caption(FOOTER_CAFE); st.markdown('> ' + DISCLAIMER)
