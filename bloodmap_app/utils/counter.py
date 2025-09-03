\
import os, json

_COUNTER_PATH = "counter.json"

def _read():
    if not os.path.exists(_COUNTER_PATH):
        return {"count": 0}
    with open(_COUNTER_PATH, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {"count": 0}

def _write(data):
    with open(_COUNTER_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f)

def bump():
    d = _read()
    d["count"] = int(d.get("count", 0)) + 1
    _write(d)

def count():
    return int(_read().get("count", 0))
