import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image
import re

st.set_page_config(page_title="Tài Xỉu Pro + OCR", page_icon="🎲", layout="wide")
st.title("🎲 Tài Xỉu Analyzer Pro + OCR")
st.caption("Hỗ trợ nhận diện tổng điểm từ ảnh chụp màn hình")

@st.cache_data
def theoretical_distribution():
    ways = {i: 0 for i in range(3, 19)}
    for a in range(1, 7):
        for b in range(1, 7):
            for c in range(1, 7):
                ways[a + b + c] += 1
    total = 216
    probs = {k: v / total for k, v in ways.items()}
    return ways, probs

theo_ways, theo_probs = theoretical_distribution()

if "history" not in st.session_state:
    st.session_state.history = []

# ====================== NHẬP LIỆU ======================
st.subheader("➕ Thêm phiên mới")

tab1, tab2 = st.tabs(["Nhập tay / Dán", "📷 OCR từ ảnh"])

with tab1:
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        new_total = st.number_input("Tổng điểm (3-18)", min_value=3, max_value=18, value=10, step=1, label_visibility="collapsed")
    with col2:
        if st.button("Thêm phiên", use_container_width=True, type="primary"):
            st.session_state.history.append(int(new_total))
            st.rerun()
    with col3:
        if st.button("Xóa phiên cuối", use_container_width=True):
            if st.session_state.history:
                st.session_state.history.pop()
                st.rerun()
    with col4:
        if st.button("Xóa tất cả", use_container_width=True):
            st.session_state.history = []
            st.rerun()

    with st.expander("Dán hàng loạt / Upload CSV"):
        raw = st.text_area("Dán danh sách tổng điểm", height=70)
        if st.button("Cập nhật từ ô nhập"):
            try:
                lst = [int(x) for x in raw.replace("\n", " ").split() if x.strip()]
                lst = [x for x in lst if 3 <= x <= 18]
                st.session_state.history = lst
                st.rerun()
            except:
                st.error("Dữ liệu không hợp lệ")

with tab2:
    st.info("Chụp màn hình kết quả tài xỉu → Upload ảnh vào đây. App sẽ cố gắng đọc số tổng điểm.")
    uploaded_image = st.file_uploader("Upload ảnh chụp màn hình", type=["png", "jpg", "jpeg"])

    if uploaded_image is not None:
        image = Image.open(uploaded_image)
        st.image(image, caption="Ảnh đã upload", use_container_width=True)

        if st.button("🔍 Nhận diện tổng điểm từ ảnh", type="primary"):
            with st.spinner("Đang nhận diện (lần đầu có thể hơi lâu)..."):
                try:
                    import easyocr
                    reader = easyocr.Reader(["en"], gpu=False, verbose=False)
                    result = reader.readtext(np.array(image), detail=0)
                    
                    # Lọc các số từ 3 đến 18
                    candidates = []
                    for text in result:
                        numbers = re.findall(r"\b([3-9]|1[0-8])\b", text)
                        candidates.extend([int(n) for n in numbers])
                    
                    if candidates:
                        # Lấy số xuất hiện nhiều nhất hoặc số lớn nhất hợp lý
                        most_common = Counter(candidates).most_common(1)[0][0]
                        st.success(f"Nhận diện được: **{most_common}**")
                        
                        if st.button(f"✅ Xác nhận thêm {most_common} vào lịch sử"):
                            st.session_state.history.append(most_common)
                            st.rerun()
                    else:
                        st.warning("Không tìm thấy số tổng điểm hợp lệ (3-18) trong ảnh. Hãy thử ảnh rõ hơn hoặc nhập tay.")
                except Exception as e:
                    st.error(f"Lỗi OCR: {e}")
                    st.info("Có thể do thư viện quá nặng với Streamlit Cloud. Hãy dùng cách nhập tay.")

# ====================== PHẦN PHÂN TÍCH (giữ nguyên logic cũ) ======================
history = st.session_state.history

if not history:
    st.info("Hãy thêm phiên để bắt đầu phân tích")
    st.stop()

n = len(history)
cnt = Counter(history)

xiu_count = sum(1 for x in history if x <= 10)
tai_count = n - xiu_count

m1, m2, m3, m4 = st.columns(4)
m1.metric("Tổng phiên", n)
m2.metric("Xỉu (3-10)", f"{xiu_count} ({xiu_count/n:.1%})")
m3.metric("Tài (11-18)", f"{tai_count} ({tai_count/n:.1%})")
m4.metric("Tổng nhiều nhất", f"{cnt.most_common(1)[0][0]} ({cnt.most_common(1)[0][1]} lần)")

# Cảnh báo chuỗi
def get_streak(data):
    if not data:
        return None, 0
    cur = data[-1]
    streak = 1
    for i in range(len(data)-2, -1, -1):
        if data[i] == cur:
            streak += 1
        else:
            break
    return cur, streak

cur_total, streak_total = get_streak(history)
same_pair = n >= 2 and history[-1] == history[-2]

if streak_total >= 3 or same_pair:
    st.error(f"⚠️ CẢNH BÁO: Tổng **{cur_total}** đang ra **{streak_total}** lần liên tiếp")
    if same_pair:
        st.error(f"⚠️ Vừa có cặp giống nhau **{history[-2]}-{history[-1]}** → Dễ bị bẻ")

st.warning("OCR chỉ mang tính hỗ trợ. Luôn kiểm tra lại số trước khi xác nhận.")
