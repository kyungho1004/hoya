
# -*- coding: utf-8 -*-
import os, json, datetime, uuid
try:
    import requests  # type: ignore
except Exception:
    requests = None

AN_FILE = os.path.join(os.path.dirname(__file__), "..", "analytics.json")

def _load():
    try:
        with open(AN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"visits": 0, "downloads": 0, "updated": None}

def _save(d):
    os.makedirs(os.path.dirname(AN_FILE), exist_ok=True)
    with open(AN_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def _ready():
    return (requests is not None) and bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"))

def _ins(event, sid):
    if not _ready():
        return
    try:
        url = os.getenv("SUPABASE_URL").rstrip("/") + "/rest/v1/analytics"
        headers = {
            "apikey": os.getenv("SUPABASE_KEY"),
            "Authorization": "Bearer " + os.getenv("SUPABASE_KEY"),
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        payload = {"event": event, "session_id": sid or None, "meta": {}}
        requests.post(url, headers=headers, json=payload, timeout=5)
    except Exception:
        pass

def ensure_sid(ss):
    if "_sid" not in ss:
        ss["_sid"] = str(uuid.uuid4())
    return ss["_sid"]

def bump_visit_once(ss):
    d = _load()
    if not ss.get("_counted"):
        d["visits"] = int(d.get("visits", 0)) + 1
        d["updated"] = datetime.datetime.now().isoformat(timespec="seconds")
        _save(d)
        ss["_counted"] = True
        _ins("visit", ss.get("_sid", ""))
    return d

def bump_download(ss=None):
    d = _load()
    d["downloads"] = int(d.get("downloads", 0)) + 1
    d["updated"] = datetime.datetime.now().isoformat(timespec="seconds")
    _save(d)
    _ins("download", (ss or {}).get("_sid", ""))
    return d

def stats():
    return _load()
