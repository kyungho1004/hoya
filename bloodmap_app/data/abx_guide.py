
from .drugs import ABX_GUIDE as ABX_GUIDE
CLASS_NOTICE = {
    "beta_lactam": ["과민반응 시 즉중단·진료","설사/발진 모니터링"],
    "cephalosporin": ["과민반응 주의","설사/복통"],
    "fluoroquinolone": ["힘줄통증/파열 의심 시 즉중단","어지럼/광과민","QT연장 병용 주의"],
    "macrolide": ["QT연장 소인 주의","상호작용 확인"],
    "glycopeptide": ["주입반응 주의","신장기능 모니터링 고려"],
}
KEYWORDS = {
    "beta_lactam": ["amoxi","ampicillin","piperacillin","tazobactam","cef","cefa","cefo","cfta"],
    "fluoroquinolone": ["floxacin"],
    "macrolide": ["-thromycin","azithro","clarithro","erythro"],
    "glycopeptide": ["vanco"],
}
def normalize(name:str)->str:
    return (name or "").strip().lower()
def match_exact(name:str):
    key = normalize(name)
    if key in ABX_GUIDE:
        return {"type":"exact","key":key,"entry":ABX_GUIDE[key]}
    return None
def match_keyword(name:str):
    key = normalize(name)
    for cls, toks in KEYWORDS.items():
        for t in toks:
            if t in key:
                return {"type":"class","class":cls}
    if "pip" in key and ("tazo" in key or "tazobactam" in key):
        return {"type":"class","class":"beta_lactam"}
    return None
