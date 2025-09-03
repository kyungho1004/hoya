from io import BytesIO

def build_report(mode, meta, vals, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines):
    lines = [f"# BloodMap Report ({mode})", ""]
    lines.append("## 메타")
    for k, v in (meta or {}).items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 기본 수치")
    for k, v in (vals or {}).items():
        if v is not None:
            lines.append(f"- {k}: {v}")
    if extra_vals:
        lines.append("")
        lines.append("## 암별 디테일 수치")
        for k, v in extra_vals.items():
            if v is not None:
                lines.append(f"- {k}: {v}")
    if cmp_lines:
        lines.append("")
        lines.append("## 수치 변화 비교")
        lines.extend(cmp_lines)
    if meds_lines:
        lines.append("")
        lines.append("## 항암제 요약")
        lines.extend(meds_lines)
    if abx_lines:
        lines.append("")
        lines.append("## 항생제 주의 요약")
        lines.extend(abx_lines)
    if food_lines:
        lines.append("")
        lines.append("## 음식 가이드")
        lines.extend(food_lines)
    return "\n".join(lines)

def md_to_pdf_bytes_fontlocked(report_md):
    # 간단한 대체: PDF 모듈 미포함 시 txt로 대체
    return report_md.encode("utf-8")
