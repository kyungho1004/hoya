
# -*- coding: utf-8 -*-
import os, json, datetime
from typing import Dict, Any

ANALYTICS_FILE = os.path.join(os.path.dirname(__file__), "..", "analytics.json")

def _safe_parent(path: str) -> str:
    p = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return p

def load_analytics() -> Dict[str, Any]:
    try:
        with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"visits": 0, "runs": 0, "last_reset": None}

def save_analytics(data: Dict[str, Any]) -> None:
    parent = _safe_parent(ANALYTICS_FILE)
    os.makedirs(parent, exist_ok=True)
    with open(ANALYTICS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def bump_visit(session_key: str) -> int:
    data = load_analytics()
    # avoid double-counting within a session (caller should pass unique key)
    data["visits"] = int(data.get("visits", 0)) + 1
    data["last_reset"] = data.get("last_reset") or str(datetime.date.today())
    save_analytics(data)
    return data["visits"]

def bump_run() -> int:
    data = load_analytics()
    data["runs"] = int(data.get("runs", 0)) + 1
    save_analytics(data)
    return data["runs"]

def mk_report_md(summary: str, details: str) -> str:
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    header = f"# 피수치 가이드 요약\n\n- 생성시각: {ts}\n- 버전: v3.14-fixed\n"
    return header + "\n## 요약\n" + summary + "\n\n## 상세\n" + details + "\n"
