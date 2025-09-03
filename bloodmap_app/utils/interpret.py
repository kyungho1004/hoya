
NORMALS={"WBC(백혈구)":(4.0,10.0,"10^3/µL"),"Hb(혈색소)":(12.0,16.0,"g/dL"),"혈소판(PLT)":(150,450,"10^3/µL"),
"호중구(ANC)":(1500,8000,"/µL"),"Ca(칼슘)":(8.6,10.2,"mg/dL"),"P(인)":(2.5,4.5,"mg/dL"),"Na(나트륨)":(135,145,"mmol/L"),
"K(칼륨)":(3.5,5.1,"mmol/L"),"Albumin(알부민)":(3.5,5.2,"g/dL"),"Glucose(혈당)":(70,140,"mg/dL"),
"Total Protein(총단백)":(6.0,8.3,"g/dL"),"AST":(0,40,"U/L"),"ALT":(0,41,"U/L"),"LDH":(140,280,"U/L"),
"CRP":(0.0,0.5,"mg/dL"),"Creatinine(Cr)":(0.6,1.2,"mg/dL"),"Uric Acid(UA)":(3.4,7.0,"mg/dL"),
"Total Bilirubin(TB)":(0.2,1.2,"mg/dL"),"BUN":(8,23,"mg/dL"),"BNP(선택)":(0,100,"pg/mL")}
def _fmt(name,val,lo,hi,unit):
    try: v=float(val)
    except: return None
    if v<lo: return f"- **{name} 낮음**: {v} {unit} (정상 {lo}~{hi})"
    if v>hi: return f"- **{name} 높음**: {v} {unit} (정상 {lo}~{hi})"
    return f"- {name}: {v} {unit} (정상범위)"
def interpret_basic(vals):
    out=[]
    for k,(lo,hi,u) in NORMALS.items():
        if vals.get(k) is None or vals.get(k)=="": continue
        x=_fmt(k,vals.get(k),lo,hi,u); 
        if x: out.append(x)
    return out
def interpret_special(s):
    out=[]; c3=s.get("C3"); c4=s.get("C4"); pro=s.get("단백뇨"); hem=s.get("혈뇨"); glu=s.get("요당")
    try:
        if c3 is not None and float(c3)<90: out.append(f"- **C3 낮음** ({c3} mg/dL): 보체 소모 가능.")
    except: pass
    try:
        if c4 is not None and float(c4)<10: out.append(f"- **C4 낮음** ({c4} mg/dL): 보체 경로 소모 가능.")
    except: pass
    try:
        if pro is not None and float(pro)>=1: out.append(f"- **단백뇨** {pro}+ : 24h 단백정량 권장.")
    except: pass
    try:
        if hem is not None and float(hem)>=1: out.append(f"- **혈뇨** {hem}+ : 요로감염/결석/사구체염 감별 필요.")
    except: pass
    try:
        if glu is not None and float(glu)>=1: out.append(f"- **요당** {glu}+ : 혈당/당화혈색소 확인.")
    except: pass
    return out
def anc_food_rules(anc_value):
    try: anc=float(anc_value)
    except: return []
    out=[]
    if anc<500:
        out.append("- **호중구 매우 낮음**: 생야채/생과일 금지, 모든 음식 익혀 섭취(전자레인지 30초+).")
        out.append("- 멸균/살균 식품 권장, 조리 후 2시간 지난 음식 섭취 비권장.")
        out.append("- 껍질 있는 과일은 주치의와 상담 후 결정.")
    elif anc<1000: out.append("- **호중구 낮음**: 외식 자제, 위생 철저, 덜 익힌 음식 피하기.")
    return out
