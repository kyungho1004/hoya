
from datetime import datetime
import json, os, streamlit as st
from .config import APP_TITLE,PAGE_TITLE,MADE_BY,CAFE_LINK_MD,FOOTER_CAFE,DISCLAIMER,ORDER
from .utils import db
from .utils.graphs import line_graph
from .utils.interpret import interpret_basic, interpret_special, anc_food_rules
from pathlib import Path
APP_DIR=Path(__file__).parent; DATA=APP_DIR/"utils"/"data"
def data_path(name): return str((DATA/name).resolve())

def _load_json(name): 
    with open(data_path(name),"r",encoding="utf-8") as f: 
        return json.load(f)
def _num(label,key,decimals=1,placeholder=""):
    raw=st.text_input(label,key=key,placeholder=placeholder)
    if raw is None or raw=="": return None
    try: return round(float(raw),decimals) if decimals>0 else int(float(raw))
    except: return None
def _ent(x): return x is not None and str(x).strip()!=""
def main():
    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    st.title(APP_TITLE); st.markdown(MADE_BY); st.markdown(CAFE_LINK_MD)
    try: st.caption(f"👀 누적 방문: {db.bump_counter()}")
    except: st.caption("👀 방문 카운터 초기화 중…")
    st.divider(); st.header("사용자")
    c1,c2=st.columns(2); nickname=c1.text_input("별명"); pin=c2.text_input("PIN 4자리",max_chars=4)
    user_id=f"{nickname}#{pin}" if nickname and pin.isdigit() and len(pin)==4 else None
    if not user_id: st.info("별명+PIN 입력 시 저장/그래프 활성화")
    st.divider(); st.header("기본 혈액 검사")
    vals={}
    for name in ORDER:
        ph="예: 0.12" if name=="CRP" else "예: 1200" if name in ("WBC(백혈구)","호중구(ANC)","AST","ALT","LDH","BNP(선택)","Glucose(혈당)") else "예: 3.5"
        vals[name]=_num(name,key=f"lab_{name}",decimals=(2 if name=='CRP' else 1),placeholder=ph)
    with st.expander("🧪 특수검사"):
        sp={}
        for k in ("C3","C4","단백뇨","혈뇨","요당"):
            sp[k]=_num(k,f"sp_{k}",0,"0~4+" if k!="C3" and k!="C4" else "정수")
    if st.button("🔎 해석하기", use_container_width=True):
        st.subheader("📋 해석 결과")
        for ln in interpret_basic(vals): st.write(ln)
        s_lines=interpret_special(sp)
        if s_lines: 
            st.markdown("### 특수검사 해석"); 
            for ln in s_lines: st.write(ln)
        for ln in anc_food_rules(vals.get("호중구(ANC)")): st.write(ln)
        if user_id:
            rec={"ts":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"labs":{k:v for k,v in vals.items() if _ent(v)},"special":sp}
            db.save_record(user_id,rec); st.success("저장 완료!"); st.markdown("#### 📈 추이 그래프"); line_graph(db.get_records(user_id),"Trends")
    st.caption(FOOTER_CAFE); st.markdown("> "+DISCLAIMER)
