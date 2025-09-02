def num_input_generic(*a, **k): return None
def _parse_numeric(x, **k):
    try:
        return float(str(x).replace(',',''))
    except: return None
def entered(x):
    try:
        return x is not None and str(x) != ''
    except: return False
