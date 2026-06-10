import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model

st.set_page_config(layout="wide")
st.title("📊 Intelligent ESG 수질-탄소 통합 관리 플랫폼")
st.subheader("안산시 반월공단 가상 센서 기반 BOD 예측 대시보드")

# 1. 데이터 및 AI 모델 로드
@st.cache_resource
def load_assets():
    df = pd.read_csv('ansan_lstm_ready_dataset.csv')
    model = load_model('industrial_bod_lstm_model.h5')
    return df, model

df, model = load_assets()

# 2. 데이터 전처리 (학습 때와 동일하게 세팅)
X_data = df[['Flow', 'Rain']].values
y_data = df['BOD'].values

scaler_X = MinMaxScaler().fit(X_data)
scaler_y = MinMaxScaler().fit(y_data.reshape(-1, 1))

X_scaled = scaler_X.transform(X_data)

# 3. 7일씩 묶어서 AI에게 예측시키기
window_size = 7
X_list = []
for i in range(len(X_scaled) - window_size):
    X_list.append(X_scaled[i:i+window_size])
X_input = np.array(X_list)

# AI의 예측값 계산 및 원래 BOD 단위로 복원
predictions_scaled = model.predict(X_input)
predictions = scaler_y.inverse_transform(predictions_scaled)

# 4. Streamlit 화면에 그래프 그리기
st.markdown("---")
st.write("### 📈 실제 측정치 vs AI 가상 센서 예측치 비교")

# 시각화를 위한 데이터프레임 구축
chart_df = pd.DataFrame({
    'Actual BOD (실제측정)': y_data[window_size:],
    'Predicted BOD (AI예측)': predictions.flatten()
}, index=df['Date'][window_size:])

# Streamlit 라인 차트 출력
st.line_chart(chart_df)

st.success("💡 인공지능이 유량과 강수량 패턴을 분석하여 실시간으로 BOD 오염도를 가상 예측하고 있습니다.")