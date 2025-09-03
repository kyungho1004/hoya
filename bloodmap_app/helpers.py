# -*- coding: utf-8 -*-
import io, json
from dataclasses import dataclass
from typing import Optional, List, Dict

def validate_pin(pin: str) -> bool:
    return pin.isdigit() and len(pin) == 4

@dataclass
class Labs:
    WBC: Optional[float]=None
    Hb: Optional[float]=None
    PLT: Optional[float]=None
    ANC: Optional[float]=None
    Ca: Optional[float]=None
    Na: Optional[float]=None
    K: Optional[float]=None
    Albumin: Optional[float]=None
    Glucose: Optional[float]=None
    TotalProtein: Optional[float]=None
    AST: Optional[float]=None
    ALT: Optional[float]=None
    LDH: Optional[float]=None
    CRP: Optional[float]=None
    Cr: Optional[float]=None
    UA: Optional[float]=None
    TB: Optional[float]=None
    BUN: Optional[float]=None
    BNP: Optional[float]=None

def as_md_report(meta: Dict, notes: List[str]) -> bytes:
    buf = io.StringIO()
    buf.write(f"# 피수치 가이드 보고서\n")
    buf.write(f"제작/자문: Hoya/GPT\n\n")
    buf.write(f"**별명**: {meta.get('nick','-')}  / **PIN**: {meta.get('pin','-')}\n\n")
    buf.write("## 결과 요약\n")
    if notes:
        for n in notes:
            buf.write(f"- {n}\n")
    else:
        buf.write("- 특이 위험 신호 없음\n")
    return buf.getvalue().encode("utf-8")
