
import os, json
STATE = "/mnt/data/_bloodmap_counter.json"
def bump():
    try:
        if os.path.exists(STATE):
            j = json.load(open(STATE,"r"))
        else:
            j = {"count":0}
        j["count"] += 1
        json.dump(j, open(STATE,"w"))
    except Exception:
        pass

def count():
    try:
        if os.path.exists(STATE):
            j = json.load(open(STATE,"r"))
            return j.get("count",0)
    except Exception:
        pass
    return 1
