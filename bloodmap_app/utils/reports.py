
from datetime import datetime
from io import BytesIO
from ..config import (ORDER, LBL_CRP, DISCLAIMER, FONT_PATH_REG, FONT_PATH_B, FONT_PATH_XB)
def build_report(*args, **kwargs): return "# report placeholder"
def md_to_pdf_bytes_fontlocked(md_text: str) -> bytes: return md_text.encode("utf-8")
