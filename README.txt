실행: streamlit run bloodmap_app/streamlit_app.py

폴더:
  bloodmap_app/
    streamlit_app.py
    config.py
    data/ (drugs.py, foods.py, ped.py)
    utils/ (inputs.py, interpret.py, reports.py, graphs.py, schedule.py)
    fonts/ (여기에 NanumGothic-Regular.ttf 등 넣기)

PDF 폰트:
  - fonts/NanumGothic-Regular.ttf (필수)
  - fonts/NanumGothic-Bold.ttf / NanumGothic-ExtraBold.ttf (선택)
Streamlit Cloud에서는 Main file path를 streamlit_app.py로 지정하세요.
