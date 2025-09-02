import os, json
_CNT_FILE='counter.json'
def bump():
    c=count()
    with open(_CNT_FILE,'w',encoding='utf-8') as f:
        json.dump({'n':c+1}, f)
def count():
    try:
        with open(_CNT_FILE,'r',encoding='utf-8') as f:
            return json.load(f).get('n',0)
    except Exception:
        return 0
