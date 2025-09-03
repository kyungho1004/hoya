# -*- coding: utf-8 -*-
"""레거시 호환: 일부 런처가 `bloodmap.app_user`의 main/app/run 을 찾습니다.
이 모듈은 모두 `bloodmap_app.app.main`으로 포워딩합니다.
"""
from importlib import import_module

def main():
    return import_module("bloodmap_app.app").main()

def app():
    return main()

def run():
    return main()
