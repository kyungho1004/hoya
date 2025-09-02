
import os, json
COUNTER_FILE = "counter.json"

def _read():
    if not os.path.exists(COUNTER_FILE):
        return {"count": 0}
    try:
        return json.load(open(COUNTER_FILE, "r"))
    except Exception:
        return {"count": 0}

def _write(d):
    with open(COUNTER_FILE, "w") as f:
        json.dump(d, f)

def bump():
    d=_read(); d["count"]=d.get("count",0)+1; _write(d)

def count():
    return _read().get("count", 0)
