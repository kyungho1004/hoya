# -*- coding: utf-8 -*-
import os, json, time, uuid
from pathlib import Path

DATA_DIR = Path(os.environ.get("BLOODMAP_DATA_DIR", Path(__file__).resolve().parent))
COUNTER_FILE = DATA_DIR / "views.json"

def _read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def bump_view_count(session_key: str) -> int:
    \"\"\"Increase unique view counter once per session. Returns current total.\"\"\"
    data = _read_json(COUNTER_FILE)
    total = int(data.get("total", 0))
    sessions = set(data.get("sessions", []))
    if session_key not in sessions:
        total += 1
        sessions.add(session_key)
        data["total"] = total
        data["sessions"] = list(sessions)
        _write_json(COUNTER_FILE, data)
    else:
        # already counted
        pass
    return int(data.get("total", total))

def get_total_views() -> int:
    data = _read_json(COUNTER_FILE)
    return int(data.get("total", 0))

def ensure_storage_writable() -> bool:
    try:
        COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Touch the file if missing
        if not COUNTER_FILE.exists():
            _write_json(COUNTER_FILE, {"total": 0, "sessions": []})
        return True
    except Exception:
        return False
