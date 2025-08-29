
from datetime import datetime
from ..config import (ORDER, LBL_CRP, DISCLAIMER)
def build_report(mode, meta, vals, compare_lines, extra_vals, meds_lines, food_lines, abx_lines):
    buf=[f"# BloodMap 보고서 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n"]
    for k in ORDER:
        v=vals.get(k); 
        if v is not None: buf.append(f"- {k}: {v}\n")
    buf.append("\n> "+DISCLAIMER+"\n")
    return "".join(buf)
def md_to_pdf_bytes_fontlocked(md_text: str) -> bytes:
    return md_text.encode("utf-8")  # placeholder (PDF 모듈이 없어도 동작)
