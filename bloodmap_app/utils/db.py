
import os,json,time
DATA_ROOT=os.path.join(os.path.dirname(__file__),"data")
R=os.path.join; RECORDS_PATH=R(DATA_ROOT,"records.json"); COUNTER_PATH=R(DATA_ROOT,"counter.json")
def _load(p,d): 
    try: return json.load(open(p,"r",encoding="utf-8"))
    except: return d
def _save(p,o): 
    os.makedirs(os.path.dirname(p),exist_ok=True); json.dump(o,open(p,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
def bump_counter():
    x=_load(COUNTER_PATH,{"visits":0}); x["visits"]=int(x.get("visits",0))+1; x["ts"]=int(time.time()); _save(COUNTER_PATH,x); return x["visits"]
def get_counter(): return int(_load(COUNTER_PATH,{"visits":0}).get("visits",0))
def save_record(uid,rec): d=_load(RECORDS_PATH,{}); d.setdefault(uid,[]).append(rec); _save(RECORDS_PATH,d)
def get_records(uid): return _load(RECORDS_PATH,{}).get(uid,[])
