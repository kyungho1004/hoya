def main():
    from datetime import datetime, date
    import os
    import streamlit as st

    # ---- Optional pandas ----
    try:
        import pandas as pd
        HAS_PD = True
    except Exception:
        HAS_PD = False

    # ---- Config (safe defaults if user's config 미존재) ----
    try:
        from .config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE,
                             DISCLAIMER, ORDER, FEVER_GUIDE,
                             LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
                             LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP,
                             FONT_PATH_REG)
    except Exception:
        APP_TITLE='피수치 가이드 v3.15'; PAGE_TITLE='BloodMap'
        MADE_BY='제작: Hoya/GPT · 자문: Hoya/GPT'
        CAFE_LINK_MD='[📌 공식카페 바로가기](https://cafe.naver.com/bloodmap)'
        FOOTER_CAFE='피수치 가이드 공식카페 — 모두의 울타리'
        DISCLAIMER='본 자료는 보호자 참고용이며, 모든 의학적 판단은 의료진에게.'
        FEVER_GUIDE='38.0~38.5℃ 해열제/경과, 38.5℃ 이상 병원 연락, 39℃ 즉시 병원.'
        LBL_WBC='WBC'; LBL_Hb='Hb'; LBL_PLT='혈소판'; LBL_ANC='ANC'
        LBL_Ca='Ca'; LBL_P='P'; LBL_Na='Na'; LBL_K='K'
        LBL_Alb='Albumin'; LBL_Glu='Glucose'; LBL_TP='Total Protein'
        LBL_AST='AST'; LBL_ALT='ALT'; LBL_LDH='LDH'; LBL_CRP='CRP'
        LBL_Cr='Cr'; LBL_UA='UA'; LBL_TB='TB'; LBL_BUN='BUN'; LBL_BNP='BNP'
        ORDER=[LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
               LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP,
               LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP]
        FONT_PATH_REG='fonts/NanumGothic.ttf'

    # ---- Imports (with safe fallbacks) ----
    try:
        from .utils.inputs import num_input_generic, entered, _parse_numeric
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
        def entered(v):
            try:
                return v is not None and str(v)!='' and float(v)!=0
            except Exception:
                return False

    # ---- Compatibility wrapper (TypeError 대응) ----
    def _num(label, *, key=None, decimals=1, placeholder="", as_int=False):
        """호환용 입력 래퍼: 사용자의 num_input_generic 시그니처가 달라도 안전하게 호출"""
        try:
            return num_input_generic(label, key=key, decimals=decimals, placeholder=placeholder, as_int=as_int)
        except TypeError:
            try:
                # 일부 버전은 decimals/placeholder 키워드 미지원
                return num_input_generic(label, key=key)
            except Exception:
                # 최후 fallback
                raw = st.text_input(label, key=key, placeholder=placeholder)
                return _parse_numeric(raw, 0 if as_int else decimals)

    try:
        from .utils.interpret import interpret_labs, compare_with_previous, food_suggestions, summarize_meds, abx_summary
    except Exception:
        def interpret_labs(vals, extras):
            lines=[]; anc=vals.get('ANC'); crp=vals.get('CRP')
            try:
                if anc is not None and float(anc)<500: lines.append('🔴 ANC<500: 생야채 금지 · 조리식 섭취')
                if crp is not None and float(crp)>=0.5: lines.append('⚠️ CRP 상승(추적 필요)')
            except Exception: pass
            return lines or ['🙂 특이 소견 없음(입력값 기준)']
        def compare_with_previous(nick, cur): return []
        def food_suggestions(vals, place): return ['- 알부민 낮을 때: 달걀, 연두부, 흰살생선, 닭가슴살, 귀리죽']
        def summarize_meds(meds): return [f"{k}: 입력됨" for k in meds.keys()]
        def abx_summary(d): return [f"{k}: {v} 용량 입력" for k,v in d.items()] if d else []

    try:
        from .utils.reports import build_report, md_to_pdf_bytes_fontlocked
    except Exception:
        def build_report(mode, meta, vals, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines):
            lines=['# 피수치 가이드 보고서','']
            lines.append(f"- 모드: {mode}")
            for k,v in (meta or {}).items(): lines.append(f"- {k}: {v}")
            if vals:
                lines.append('\n## 입력 수치')
                for k,v in vals.items():
                    if v is not None and v!='': lines.append(f"- {k}: {v}")
            if meds_lines: lines+=['\n## 약물 요약', *['- '+x for x in meds_lines]]
            if abx_lines: lines+=['\n## 항생제 요약', *['- '+x for x in abx_lines]]
            if food_lines: lines+=['\n## 음식 가이드', *food_lines]
            return '\n'.join(lines)
        def md_to_pdf_bytes_fontlocked(md_text): return b"%PDF-1.4\n%Mock\n"

    try:
        from .utils.graphs import render_graphs
    except Exception:
        def render_graphs():
            st.markdown('### 📈 저장된 수치 그래프 (플레이스홀더)')

    try:
        from .utils.schedule import render_schedule
    except Exception:
        def render_schedule(nickname):
            st.markdown('### 🗓️ 항암 스케줄표 (플레이스홀더)')

    try:
        from .data.drugs import ANTICANCER, ABX_GUIDE
    except Exception:
        ANTICANCER={'ATRA':{'alias':'베사노이드'}, 'MTX':{'alias':'메토트렉세이트'}, 'ARA-C':{'alias':'시아라빈'}}
        ABX_GUIDE={'세팔로스포린':['과민반응','설사'], '마크롤라이드':['CYP 상호작용','QT 연장']}

    try:
        from .utils import counter as _bm_counter
    except Exception:
        class _bmc:
            @staticmethod
            def count(): return 0
            @staticmethod
            def bump(): pass
        _bm_counter = _bmc()

    # ===== Page =====
    st.set_page_config(page_title=PAGE_TITLE, layout='centered')
    st.title(APP_TITLE)
    st.markdown(MADE_BY); st.markdown(CAFE_LINK_MD)

    # 공유버튼
    st.markdown('### 🔗 공유하기')
    c1, c2, c3 = st.columns([1,1,2])
    with c1: st.link_button('📱 카카오톡/메신저', 'https://hdzwo5ginueir7hknzzfg4.streamlit.app/')
    with c2: st.link_button('📝 카페/블로그', 'https://cafe.naver.com/bloodmap')
    with c3: st.code('https://hdzwo5ginueir7hknzzfg4.streamlit.app/', language='text')
    st.caption('✅ 모바일 줄꼬임 방지 · 별명 저장/그래프 · 암별/소아 패널 · PDF 한글 폰트 고정')

    # 카운터
    try:
        os.makedirs('fonts', exist_ok=True)
        _bm_counter.bump()
        st.caption(f'👀 조회수(방문): {_bm_counter.count()}')
    except Exception: pass

    if 'records' not in st.session_state: st.session_state.records = {}

    # 기본 입력
    st.divider(); st.header('1️⃣ 환자/암·소아 정보')
    nickname = st.text_input('별명(저장/그래프/스케줄용)', placeholder='예: 홍길동')
    mode = st.selectbox('모드 선택', ['일반/암','소아(일상/호흡기)','소아(감염질환)'])
    anc_place = st.radio('현재 식사 장소(ANC 가이드용)', ['가정','병원'], horizontal=True)

    # 검사항목
    st.divider(); st.header('2️⃣ 기본 혈액 검사 수치 (입력한 값만 해석)')
    vals = {}
    for name in ORDER:
        dec = 2 if name==LBL_CRP else 1
        vals[name] = _num(name, key=f'v_{name}', decimals=dec, placeholder='')

    # 동반 약물/상태 — 여기서 TypeError 방지 래퍼 사용
    st.markdown('### 💧 동반 약물/상태')
    extras = {}
    extras['diuretic_amt'] = _num('이뇨제(복용량/회/일)', key='diuretic_amt', decimals=1, placeholder='예: 1')

    # 실행
    st.divider()
    if st.button('🔎 해석하기', use_container_width=True):
        lines = interpret_labs(vals, extras)
        for l in lines: st.write(l)
        st.markdown('### 🌡️ 발열 가이드'); st.write(FEVER_GUIDE)

        meta={'anc_place': anc_place}
        report_md = build_report(mode, meta, vals, [], {}, [], [], [])
        st.download_button('📥 보고서(.md) 다운로드', data=report_md.encode('utf-8'),
                           file_name=f'bloodmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md',
                           mime='text/markdown')

    st.caption(FOOTER_CAFE); st.markdown('> ' + DISCLAIMER)
