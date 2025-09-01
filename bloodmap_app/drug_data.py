# -*- coding: utf-8 -*-
"""약물/카테고리 데이터 (간단 샘플). 실제 서비스 데이터는 추후 채우세요."""

ANTICANCER = {
    "6-MP": {"alias": "6-mercaptopurine"},
    "MTX": {"alias": "methotrexate"},
    "Vesanoid": {"alias": "tretinoin, all-trans retinoic acid"},
}

ANTIBIOTICS = {
    "Amoxicillin": {"alias": "amox"},
    "Ceftriaxone": {"alias": "ctx"},
}

__all__ = ["ANTICANCER", "ANTIBIOTICS"]
