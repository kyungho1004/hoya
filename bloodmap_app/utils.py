# -*- coding: utf-8 -*-
"""공통 유틸 모듈."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Lab:
    key: str
    label: str

ORDER = [
    Lab("WBC", "WBC(백혈구)"),
    Lab("Hb", "Hb(혈색소)"),
    Lab("PLT", "PLT(혈소판)"),
    Lab("ANC", "ANC(호중구)"),
]

def load_css(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def make_kv_table(data: Dict[str, Any]) -> str:
    """간단한 key-value HTML 테이블."""
    if not data:
        return "<p>데이터 없음</p>"
    rows = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in data.items())
    return f"""<table class="kv"><tbody>{rows}</tbody></table>"""
