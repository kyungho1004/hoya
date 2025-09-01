# -*- coding: utf-8 -*-
from __future__ import annotations
import streamlit as st
from typing import Dict, Tuple, List, Any
from pathlib import Path

def apply_css():
    """Load and inject style.css if present."""
    css_path = Path(__file__).parent / "style.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"""<style>{f.read()}</style>""", unsafe_allow_html=True)

def number_or_none(x):
    try:
        return float(x)
    except Exception:
        return None

def only_entered_values(d: Dict[str, Any]) -> Dict[str, float]:
    return {k: float(v) for k, v in d.items() if v is not None}

def food_recommendations(values: Dict[str, float]) -> List[Tuple[str, List[str]]]:
    """Return list of (title, foods) depending on entered values.
    단순 규칙 기반 샘플. (필요 시 확장)
    """
    recs: List[Tuple[str, List[str]]] = []
    if (v := values.get("Albumin")) is not None and v < 3.5:
        recs.append(("알부민 낮음", ["달걀", "연두부", "흰살 생선", "닭가슴살", "귀리죽"]))
    if (v := values.get("K")) is not None and v < 3.5:
        recs.append(("칼륨 낮음", ["바나나", "감자", "호박죽", "고구마", "오렌지"]))
    if (v := values.get("Hb")) is not None and v < 10.0:
        recs.append(("Hb 낮음", ["소고기", "시금치", "두부", "달걀 노른자", "렌틸콩"]))
    return recs
