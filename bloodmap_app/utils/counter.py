
import os, json

_PATH = "visit_counter.json"

def bump():
    data = {"count": 0}
    if os.path.exists(_PATH):
        try:
            data = json.load(open(_PATH, "r"))
        except Exception:
            data = {"count": 0}
    data["count"] = int(data.get("count", 0)) + 1
    json.dump(data, open(_PATH, "w"))
    return data["count"]

def count():
    if os.path.exists(_PATH):
        try:
            return int(json.load(open(_PATH, "r")).get("count", 0))
        except Exception:
            return 0
    return 0
