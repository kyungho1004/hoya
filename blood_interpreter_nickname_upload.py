
import streamlit as st
import datetime
import json

st.set_page_config(page_title="피수치 자동 해석기", layout="centered")
st.title("🔬 피수치 자동 해석기 by Hoya")
st.write("입력한 수치에 따라 해석 결과와 식이 가이드를 제공합니다.")

nickname = st.text_input("👤 별명 (닉네임)", max_chars=20)
category = st.selectbox("📂 해석 카테고리", ["항암 치료", "일반 해석", "투석 환자", "당뇨"])

def float_input(label):
    val = st.text_input(label)
    return float(val) if val.strip() else None

# 수치 입력
wbc = float_input("WBC (백혈구)")
hb = float_input("Hb (적혈구)")
plt = float_input("혈소판 (PLT)")
anc = float_input("ANC (호중구)")
alb = float_input("알부민 (Albumin)")

# 항암제 일부 (예시)
chemo_dict = {}
for drug in ["6-MP", "MTX", "베사노이드"]:
    val = st.text_input(f"{drug} 복용량 (정)")
    chemo_dict[drug] = float(val) if val.strip() else None

diuretic = st.checkbox("💧 이뇨제 복용 중")

# 💾 저장 버튼
if st.button("💾 별명별 수치 저장"):
    data = {
        "nickname": nickname,
        "category": category,
        "date": str(datetime.date.today()),
        "inputs": {
            "WBC": wbc,
            "Hb": hb,
            "PLT": plt,
            "ANC": anc,
            "Albumin": alb,
            "Diuretic": diuretic,
            "Chemo": chemo_dict
        }
    }
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    st.download_button(
        label="📥 저장된 파일 다운로드 (.json)",
        data=json_str,
        file_name=f"{nickname}_data.json",
        mime="application/json"
    )

# 📤 업로드 기능
st.markdown("---")
st.subheader("📤 저장된 파일 불러오기")
uploaded = st.file_uploader("별명 수치 파일 업로드 (.json)", type="json")
if uploaded is not None:
    saved_data = json.load(uploaded)
    st.success(f"✅ {saved_data['nickname']}님의 수치를 불러왔습니다!")
    st.json(saved_data)
