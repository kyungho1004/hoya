# -*- coding: utf-8 -*-
from __future__ import annotations
import math
from typing import Optional, Dict

def safe_float(x: str | float | int | None) -> Optional[float]:
    try:
        if x is None: return None
        return float(x)
    except Exception:
        return None

def anc_risk_badge(anc: Optional[float]) -> tuple[str,str]:
    if anc is None:
        return ("미입력", "badge")
    try:
        v = float(anc)
    except Exception:
        return ("오류", "badge danger")
    if v < 500: return ("중증 호중구감소", "badge danger")
    if v < 1000: return ("호중구감소", "badge warn")
    return ("안정", "badge ok")

def fmt_number(x: Optional[float]) -> str:
    return "-" if x is None else (f"{x:.2f}" if isinstance(x, float) and (x % 1) else f"{x}")

def kcal_reco(albumin: Optional[float]) -> str:
    if albumin is None: return "일반 균형식."
    if albumin < 3.0: return "고단백·고칼로리 식단(연두부, 흰살생선, 달걀 등)."
    return "균형 잡힌 일반식."