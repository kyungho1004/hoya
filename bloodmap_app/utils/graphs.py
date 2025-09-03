
import streamlit as st, pandas as pd
def line_graph(records,title):
    if not records: st.info("저장된 기록이 없습니다."); return
    rows=[]
    for r in records:
        labs=r.get("labs",{})
        rows.append({"ts":r.get("ts",""),"WBC":labs.get("WBC(백혈구)"),"Hb":labs.get("Hb(혈색소)"),"PLT":labs.get("혈소판(PLT)"),"CRP":labs.get("CRP"),"ANC":labs.get("호중구(ANC)")})
    df=pd.DataFrame(rows); df["ts"]=pd.to_datetime(df["ts"],errors="coerce"); df=df.sort_values("ts"); st.line_chart(df.set_index("ts")[["WBC","Hb","PLT","CRP","ANC"]])
