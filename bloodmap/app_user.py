# -*- coding: utf-8 -*-
from importlib import import_module

def main():
    return import_module("bloodmap_app.app").main()

def app():
    return main()

def run():
    return main()
