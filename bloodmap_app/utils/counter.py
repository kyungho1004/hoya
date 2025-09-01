
import os, json, datetime
AN_FILE = os.path.join(os.path.dirname(__file__), "..", "analytics.json")
def _load():
    try:
        with open(AN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"visits": 0, "downloads": 0}
def _save(d):
    os.makedirs(os.path.dirname(AN_FILE), exist_ok=True)
    with open(AN_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
def bump_visit_once(session):
    d=_load()
    if not session.get("_counted"):
        d["visits"]=int(d.get("visits",0))+1; _save(d); session["_counted"]=True
    return d
def bump_download():
    d=_load(); d["downloads"]=int(d.get("downloads",0))+1; _save(d); return d
def stats(): return _load()
