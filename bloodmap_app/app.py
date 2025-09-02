def main():
    from datetime import datetime, date
    import os
    import streamlit as st

    # ===== Config =====
    try:
        from .config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE,
                             DISCLAIMER, ORDER, FEVER_GUIDE,
                             LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
                             LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP)
    except Exception:
        APP_TITLE='피수치 가이드 v3.15'; PAGE_TITLE='BloodMap'
        MADE_BY='제작: Hoya/GPT · 자문: Hoya/GPT'
        CAFE_LINK_MD='[📌 공식카페 바로가기](https://cafe.naver.com/bloodmap)'
        FOOTER_CAFE='피수치 가이드 공식카페 — 모두의 울타리'
        DISCLAIMER='본 자료는 보호자 참고용입니다.'
        LBL_WBC='WBC'; LBL_Hb='Hb'; LBL_PLT='PLT'; LBL_ANC='ANC'
        LBL_Ca='Ca'; LBL_P='P'; LBL_Na='Na'; LBL_K='K'
        LBL_Alb='Alb'; LBL_Glu='Glu'; LBL_TP='TP'
        LBL_AST='AST'; LBL_ALT='ALT'; LBL_LDH='LDH'; LBL_CRP='CRP'
        LBL_Cr='Cr'; LBL_UA='UA'; LBL_TB='TB'; LBL_BUN='BUN'; LBL_BNP='BNP'
        ORDER=[LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
               LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP,
               LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP]
        FEVER_GUIDE='38.0~38.5℃ 해열제/경과, 38.5℃ 이상 병원 연락, 39℃ 즉시 병원.'

    # ===== Optional deps =====
    try:
        import pandas as pd
        HAS_PD=True
    except Exception:
        HAS_PD=False

    # ===== Utils (fallbacks) =====
    try:
        from .utils.inputs import num_input_generic, entered, _parse_numeric
    except Exception:
        def _parse_numeric(s, decimals=1):
            if s is None or s=='': return None
            try: v=float(str(s).strip()); return round(v, decimals) if decimals is not None else v
            except: return None
        def num_input_generic(label, key=None, decimals=1, placeholder="", as_int=False):
            raw=st.text_input(label, key=key, placeholder=placeholder)
            v=_parse_numeric(raw, 0 if as_int else decimals)
            if as_int and v is not None:
                try: return int(v)
                except: return None
            return v
        def entered(v):
            try: return v is not None and str(v)!='' and float(v)!=0
            except: return False

    def _num(label, *, key=None, decimals=1, placeholder="", as_int=False):
        try:
            return num_input_generic(label, key=key, decimals=decimals, placeholder=placeholder, as_int=as_int)
        except TypeError:
            try: return num_input_generic(label, key=key)
            except Exception:
                raw = st.text_input(label, key=key, placeholder=placeholder)
                return _parse_numeric(raw, 0 if as_int else decimals)

    try:
        from .utils.interpret import interpret_labs, compare_with_previous, food_suggestions, summarize_meds, abx_summary
    except Exception:
        def interpret_labs(vals, extras):
            out=[]; anc=vals.get('ANC'); crp=vals.get('CRP')
            try:
                if anc is not None and float(anc)<500: out.append('🔴 ANC<500: 생야채 금지 · 조리식 섭취 · 외출 자제')
                if crp is not None and float(crp)>=0.5: out.append('⚠️ 염증 수치 상승(추적 필요)')
            except: pass
            return out or ['🙂 특이 소견 없음(입력값 기준)']
        def compare_with_previous(n, cur): return []
        def food_suggestions(vals, place): return ['- 알부민 낮을 때: 달걀, 연두부, 흰살생선, 닭가슴살, 귀리죽']
        def summarize_meds(meds):
            out=[]; 
            for k,v in (meds or {}).items():
                if k=='ATRA': out.append('ATRA: 분화증후군 주의 — 호흡곤란/부종 시 즉시 병원')
                elif k=='MTX': out.append('MTX: 간수치/구내염 주의 · 수분충분')
                elif k=='ARA-C': out.append('ARA-C: 제형별(IV/SC/HDAC) 부작용 주의')
                else: out.append(f'{k}: 일반적 부작용 주의')
            return out
        def abx_summary(d): return [f"{k}: {v} 용량 입력됨" for k,v in (d or {}).items()]

    try:
        from .utils.reports import build_report, md_to_pdf_bytes_fontlocked
    except Exception:
        def build_report(mode, meta, vals, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines):
            lines=['# 피수치 가이드 보고서','']
            lines.append(f"- 모드: {mode}")
            for k,v in (meta or {}).items():
                if v not in (None,""): lines.append(f"- {k}: {v}")
            lines.append('')
            if vals:
                lines.append('## 입력 수치')
                for k,v in vals.items():
                    if v is not None and v!='':
                        lines.append(f"- {k}: {v}")
            if extra_vals:
                lines.append('\n## 암별 디테일 수치')
                for k,v in extra_vals.items():
                    if v is not None and v!='':
                        lines.append(f"- {k}: {v}")
            if meds_lines: lines+=['\n## 약물 요약', *['- '+x for x in meds_lines]]
            if abx_lines: lines+=['\n## 항생제 요약', *['- '+x for x in abx_lines]]
            if food_lines: lines+=['\n## 음식 가이드', *food_lines]
            return "\n".join(lines)
        def md_to_pdf_bytes_fontlocked(md_text): return b"%PDF-1.4\n%Mock\n"

    try:
        from .utils.graphs import render_graphs
    except Exception:
        def render_graphs(nickname, order, records): pass

    try:
        from .utils.schedule import render_schedule
    except Exception:
        def render_schedule(nickname): pass

    try:
        from .data.drugs import ANTICANCER, ABX_GUIDE
    except Exception:
        ANTICANCER={"ATRA":{"alias":"베사노이드"},"ARA-C":{"alias":"시아라빈"},"MTX":{"alias":"메토트렉세이트"}}
        ABX_GUIDE={"세팔로스포린":["과민반응","설사"],"마크롤라이드":["CYP 상호작용","QT 연장"]}

    try:
        from .utils import counter as _bm_counter
    except Exception:
        class _c:
            @staticmethod
            def bump(): pass
            @staticmethod
            def count(): return 0
        _bm_counter=_c()

    # ===== Page =====
    st.set_page_config(page_title=PAGE_TITLE, layout='centered')
    st.title(APP_TITLE); st.markdown(MADE_BY); st.markdown(CAFE_LINK_MD)

    # 공유 (복사아이콘 제거: code → disabled text_input)
    st.markdown('### 🔗 공유하기')
    c1, c2 = st.columns([1,1])
    with c1: st.link_button('📱 카카오톡/메신저', 'https://hdzwo5ginueir7hknzzfg4.streamlit.app/')
    with c2: st.link_button('📝 카페/블로그', 'https://cafe.naver.com/bloodmap')
    st.text_input('웹앱 주소', value='https://hdzwo5ginueir7hknzzfg4.streamlit.app/', disabled=True)
    st.caption('✅ 모바일 줄꼬임 방지 · 별명 저장/추세 그래프 · 암별/소아 패널 · PDF 훅')

    # 카운터
    try:
        os.makedirs('fonts', exist_ok=True)
        _bm_counter.bump()
        st.caption(f'👀 조회수(방문): {_bm_counter.count()}')
    except Exception:
        pass

    # 세션 준비
    if 'records' not in st.session_state:
        st.session_state.records = {}
    if 'schedules' not in st.session_state:
        st.session_state.schedules = {}

    # 1) 기본 정보
    st.divider(); st.header('1️⃣ 환자/암·소아 정보')
    nickname = st.text_input('별명(저장/그래프/스케줄용)', placeholder='예: 홍길동')
    mode = st.selectbox('모드 선택', ['일반/암','소아(일상/호흡기)','소아(감염질환)'])
    group = None; cancer=None; infect_sel=None; ped_topic=None

    if mode == '일반/암':
        group = st.selectbox('암 그룹 선택', ['미선택/일반','혈액암','고형암','소아암','희귀암'])
        if group == '혈액암':
            cancer = st.selectbox('혈액암 종류', ['AML','APL','ALL','CML','CLL'])
        elif group == '고형암':
            cancer = st.selectbox('고형암 종류', ['폐암(Lung cancer)','유방암(Breast cancer)','위암(Gastric cancer)','대장암(Cololoractal cancer)','간암(HCC)','췌장암(Pancreatic cancer)','담도암(Cholangiocarcinoma)','자궁내막암(Endometrial cancer)','구강암/후두암','피부암(흑색종)','육종(Sarcoma)','신장암(RCC)','갑상선암','난소암','자궁경부암','전립선암','뇌종양(Glioma)','식도암','방광암'])
        elif group == '소아암':
            cancer = st.selectbox('소아암 종류', ['Neuroblastoma','Wilms tumor'])
        elif group == '희귀암':
            cancer = st.selectbox('희귀암 종류', ['담낭암(Gallbladder cancer)','부신암(Adrenal cancer)','망막모세포종(Retinoblastoma)','흉선종/흉선암(Thymoma/Thymic carcinoma)','신경내분비종양(NET)','간모세포종(Hepatoblastoma)','비인두암(NPC)','GIST'])

    anc_place = st.radio('현재 식사 장소(ANC 가이드용)', ['가정','병원'], horizontal=True)
    table_mode = st.checkbox('⚙️ PC용 표 모드(가로형)')

    # 2) 기본 수치
    st.divider(); st.header('2️⃣ 기본 혈액 검사 수치 (입력한 값만 해석)')
    vals={}
    def _add(name, k):
        dec = 2 if name==LBL_CRP else 1
        vals[name]=_num(name, key=k, decimals=dec)
    if not table_mode:
        for nm in ORDER: _add(nm, f'v_{nm}')
    else:
        l,r=st.columns(2); half=(len(ORDER)+1)//2
        with l:
            for nm in ORDER[:half]: _add(nm, f'l_{nm}')
        with r:
            for nm in ORDER[half:]: _add(nm, f'r_{nm}')

    # 3) 암별 디테일
    extra_vals={}
    if mode=='일반/암' and group and group!='미선택/일반' and cancer:
        items={
            'AML':[('PT','PT','sec',1),('aPTT','aPTT','sec',1),('Fibrinogen','Fibrinogen','mg/dL',1),('D-dimer','D-dimer','µg/mL',2)],
            'APL':[('PT','PT','sec',1),('aPTT','aPTT','sec',1),('Fibrinogen','Fibrinogen','mg/dL',1),('D-dimer','D-dimer','µg/mL',2),('DIC Score','DIC Score','pt',0)],
            '폐암(Lung cancer)':[('CEA','CEA','ng/mL',1),('CYFRA 21-1','CYFRA 21-1','ng/mL',1),('NSE','NSE','ng/mL',1)]
        }.get(cancer,[])
        if items:
            st.divider(); st.header('3️⃣ 암별 디테일 수치')
            for key,label,unit,decs in items:
                extra_vals[key]=_num(f"{label}"+(f" ({unit})" if unit else ""), key=f"extra_{key}", decimals=decs)

    # 4) 약물 입력
    st.divider(); st.header('4️⃣ 약물 입력')
    try:
        from .data.drugs import ANTICANCER, ABX_GUIDE
    except Exception:
        pass
    meds={}; extras={'abx':{}}
    heme_by_cancer={'AML':['ARA-C','Daunorubicin','Idarubicin','Cyclophosphamide','Etoposide','Fludarabine','Hydroxyurea','MTX','ATRA','G-CSF']}
    solid_by_cancer={'폐암(Lung cancer)':['Cisplatin','Carboplatin','Paclitaxel','Docetaxel','Gemcitabine','Pemetrexed','Gefitinib','Osimertinib','Alectinib','Bevacizumab','Pembrolizumab','Nivolumab']}
    default=[]
    if mode=='일반/암' and cancer:
        if group=='혈액암': default=heme_by_cancer.get(cancer,[])
        elif group=='고형암': default=solid_by_cancer.get(cancer,[])
    drug_search=st.text_input('🔍 항암제 검색')
    drug_choices=[d for d in (default or list(ANTICANCER.keys())) if not drug_search or drug_search.lower() in d.lower() or drug_search.lower() in ANTICANCER.get(d,{}).get('alias','').lower()]
    selected=st.multiselect('항암제 선택', drug_choices, default=[])
    for d in selected:
        alias=ANTICANCER.get(d,{}).get('alias','')
        if d=='ATRA':
            tabs=_num(f'{d} ({alias}) - 캡슐 개수', key=f'med_{d}', as_int=True)
            if tabs: meds[d]={'tabs':tabs}
        elif d=='ARA-C':
            form=st.selectbox(f'{d} ({alias}) - 제형', ['정맥(IV)','피하(SC)','고용량(HDAC)'], key=f'form_{d}')
            dose=_num(f'{d} ({alias}) - 용량/일', key=f'dose_{d}', decimals=1)
            if dose: meds[d]={'form':form,'dose':dose}
        else:
            amt=_num(f'{d} ({alias}) - 용량/알약', key=f'med_{d}', decimals=1)
            if amt: meds[d]={'dose_or_tabs':amt}

    st.markdown('#### 🧪 항생제')
    abx_search=st.text_input('🔍 항생제 검색(계열/키워드)')
    abx_choices=[a for a in ABX_GUIDE.keys() if not abx_search or abx_search.lower() in a.lower() or any(abx_search.lower() in tip.lower() for tip in ABX_GUIDE[a])]
    sel_abx=st.multiselect('항생제 계열 선택', abx_choices, default=[])
    for a in sel_abx:
        extras['abx'][a]=_num(f'{a} - 복용/주입량', key=f'abx_{a}', decimals=1)

    st.markdown('#### 💧 동반 약물/상태')
    extras['diuretic_amt']=_num('이뇨제(복용량/회/일)', key='diuretic_amt', decimals=1, placeholder='예: 1')

    # 실행
    st.divider()
    if st.button('🔎 해석하기', use_container_width=True):
        # interpret robust
        try:
            lines = interpret_labs(vals, extras)
        except TypeError:
            try: lines = interpret_labs(vals)
            except TypeError: lines = interpret_labs(extras, vals)
        for l in (lines or []): st.write(l)

        if meds:
            st.markdown('### 💊 항암제 부작용·상호작용 요약')
            for l in summarize_meds(meds): st.write(l)
        if extras.get('abx'):
            st.markdown('### 🧪 항생제 주의 요약')
            for l in abx_summary(extras['abx']): st.write(l)

        st.markdown('### 🌡️ 발열 가이드'); st.write(FEVER_GUIDE)
        fs = food_suggestions(vals, anc_place)
        if fs: st.markdown('### 🥗 음식 가이드'); [st.markdown(x) for x in fs]

        # 저장 + 그래프용 레코드 누적
        if nickname and nickname.strip():
            rec = {
                'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'mode': mode, 'group': group, 'cancer': cancer,
                'labs': {k: vals.get(k) for k in ORDER if entered(vals.get(k))},
                'extra': {k: v for k, v in (locals().get('extra_vals') or {}).items() if entered(v)},
                'meds': meds, 'extras': extras
            }
            st.session_state.records.setdefault(nickname, []).append(rec)
            st.success('✅ 별명으로 저장되었습니다. 아래 추세 그래프에서 확인하세요.')

        # 리포트
        from .utils.reports import build_report, md_to_pdf_bytes_fontlocked
        meta={'mode':mode,'group':group,'cancer':cancer,'anc_place':anc_place}
        meds_lines=summarize_meds(meds) if meds else []
        abx_lines=abx_summary(extras.get('abx', {})) if extras.get('abx') else []
        report_md=build_report(mode, meta, vals, [], extra_vals, meds_lines, fs, abx_lines)
        st.download_button('📥 보고서(.md) 다운로드', data=report_md.encode('utf-8'),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                           mime='text/markdown')

        try:
            pdf_bytes=md_to_pdf_bytes_fontlocked(report_md)
            st.download_button('🖨️ 보고서(.pdf) 다운로드', data=pdf_bytes,
                               file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                               mime='application/pdf')
        except Exception:
            st.info('PDF 모듈(reportlab) 미설치 또는 폰트 미지정 — .md 다운로드를 사용하세요.')

    # 그래프/스케줄
    from .utils.graphs import render_graphs
    render_graphs(nickname, ORDER, st.session_state.records)
    from .utils.schedule import render_schedule
    render_schedule(nickname)

    st.markdown('---'); st.caption(FOOTER_CAFE); st.markdown('> '+DISCLAIMER)
