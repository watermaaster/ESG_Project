import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.graph_objects as go
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(page_title="AI 미래 리스크 예보 및 최적화", layout="wide")

# [핵심] 팀장님이 제공해주신 공학적 계수 및 공식 설정
A_COEFF = 6.5e-5  # 에너지 강도 (a)
B_COEFF = 0.2     # 고정 전력 (b)
LEGAL_LIMIT = 20.0 # 법적 배출 허용 기준 (mg/L, 안산 반월공단 가정)
ELEC_PRICE = 120   # kWh당 전기 요금 (가정치)
FINE_PER_KG = 5000 # 기준 초과 시 kg당 부과금 (가정치)

st.title(" AI 미래 리스크 예보 및 운영 최적화")
st.markdown("---")

# 🔍 파일 자동 추적 함수 (3, 4페이지 연동 안정성 확보)
def find_file(file_name_options):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    search_paths = [os.path.join(root_dir, name) for name in file_name_options] + \
                   [os.path.join(current_dir, name) for name in file_name_options]
    for path in search_paths:
        if os.path.exists(path): return path
    return None

@st.cache_resource
def load_assets():
    csv_path = find_file(['ansan_lstm_ready_dataset.csv', 'ansan_lstm_ready_dataset.csv.csv'])
    model_path = find_file(['industrial_bod_lstm_model.h5', 'industrial_bod_lstm_model.h5.h5'])
    
    # 🔍 [진단 추가] 만약 못 찾으면 현재 파이썬이 보는 파일 목록을 강제로 화면에 출력
    if not csv_path or not model_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        
        st.error("⚠️ 파이썬이 파일을 찾지 못했습니다. 아래 실제 경로와 파일 목록을 확인해 주세요.")
        st.info(f"📁 파이썬이 뒤진 최상위 폴더 경로: `{root_dir}`")
        try:
            st.warning(f"📄 그 폴더 안에 있는 실제 파일들: {os.listdir(root_dir)}")
        except Exception as e:
            st.error(f"폴더를 읽는 중 오류 발생: {e}")
        return None, None
    return pd.read_csv(csv_path), load_model(model_path)

df_raw, model = load_assets()

if df_raw is not None and model is not None:
    # ---------------------------------------------------------
    # 1. 사이드바 제어 설정 (컨트롤러)
    # ---------------------------------------------------------
    with st.sidebar:
        st.header("⚙ 시뮬레이션 제어")
        
        # 3페이지 연동 컨셉: 실시간 vs 가상 시나리오
        data_mode = st.radio("데이터 모드 선택", ["실시간 기상 API 연동", "가상 위기 시나리오"])
        
        scenario = "평시 상태"
        if data_mode == "가상 위기 시나리오":
            scenario = st.selectbox("위기 상황 설정", ["평시 상태", "기습 폭우 (강수량 폭증)", "극심한 가뭄"])
        
        st.markdown("---")
        st.header(" 공정 제어")
        # 팀장님의 핵심 무기: 정화 효율 슬라이더
        target_eta = st.slider("목표 정화 효율 (η)", 0.0, 0.99, 0.85, 0.01)
        
    # ---------------------------------------------------------
    # 2. AI 가상 센서 연산 (미래 7일 예측)
    # ---------------------------------------------------------
    # 스케일러 재구성 (학습 때와 동일한 기준)
    scaler_X = MinMaxScaler().fit(df_raw[['Flow', 'Rain']])
    scaler_y = MinMaxScaler().fit(df_raw[['BOD']])
    
    # 최근 7일 데이터 추출
    # 3페이지 실시간 API 데이터가 있으면 그걸 쓰고, 없으면 과거 데이터 보완
    if data_mode == "실시간 기상 API 연동" and os.path.exists("live_realtime_data.csv"):
        last_7_days = pd.read_csv("live_realtime_data.csv")
    else:
        last_7_days = df_raw.tail(7).copy()
    
    # 시나리오에 따른 미래 데이터 변동 (Mocking)
    # 시나리오에 따른 미래 데이터 변동 (Mocking)
    # 뒤에 .copy()를 붙여서 수정 가능한 배열로 만들어줍니다.
    future_input = last_7_days[['Flow', 'Rain']].values.copy()
    if scenario == "기습 폭우 (강수량 폭증)":
        future_input[:, 1] += 50.0  # 강수량 강제 증가
        future_input[:, 0] *= 1.5   # 유량 증가
    elif scenario == "극심한 가뭄":
        future_input[:, 1] = 0
        future_input[:, 0] *= 0.7
        
    # LSTM 예측 수행
    X_input = scaler_X.transform(future_input).reshape(1, 7, 2)
    pred_scaled = model.predict(X_input)
    C0_future = scaler_y.inverse_transform(pred_scaled)[0][0] # AI가 예측한 미래 유입 BOD (C0)

    # ---------------------------------------------------------
    # 3. 우측 메인 화면 (AI 리스크 예보 섹션)
    # ---------------------------------------------------------
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(" AI 기반 향후 7일 유입 오염도(C₀) 예보")
        # 미래 날짜 생성
        last_date = pd.to_datetime(df_raw['Date'].iloc[-1])
        future_dates = [(last_date + timedelta(days=i)).strftime("%m/%d") for i in range(1, 8)]
        
        # 가상의 시계열 흐름 생성 (예측값 기준 변동성 부여)
        future_bod_trend = [C0_future * (1 + np.random.uniform(-0.1, 0.1)) for _ in range(7)]
        
        fig_forecast = go.Figure()
        fig_forecast.add_trace(go.Scatter(x=future_dates, y=future_bod_trend, mode='lines+markers', 
                                         name='Predicted BOD', line=dict(color='#00d1ff', width=4)))
        fig_forecast.add_hline(y=LEGAL_LIMIT, line_dash="dash", line_color="red", annotation_text="배출기준선")
        fig_forecast.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_forecast, use_container_width=True)

    with col2:
        st.subheader("🚨 리스크 판정")
        if max(future_bod_trend) > LEGAL_LIMIT:
            st.error(f"**주의: 기준 초과 위험**\n\n향후 7일 내 오염도가 {max(future_bod_trend):.1f}mg/L까지 상승할 것으로 예측됩니다.")
        else:
            st.success("**안전: 정상 범위**\n\n예측 오염도가 법적 기준치 이하로 관리되고 있습니다.")
        
        st.metric("AI 예측 내일 오염도", f"{future_bod_trend[0]:.2f} mg/L")

    # ---------------------------------------------------------
    # 4. 하단 비용 최적화 섹션 (팀장님 공식 반영)
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader(" 비용 최적화 시뮬레이션 (Trade-off Analysis)")
    st.latex(r"E = a \cdot C_0 \cdot \eta \cdot (-\ln(1-\eta)) + b")

    # 최적화 연산 로직
    eta_range = np.linspace(0.1, 0.99, 100)
    
    # 팀장님의 에너지 공식 함수화
    def calc_energy(c0, eta):
        return A_COEFF * c0 * eta * (-np.log(1 - eta)) + B_COEFF

    # 현재 상태 연산
    current_energy = calc_energy(C0_future, target_eta)
    current_energy_cost = current_energy * ELEC_PRICE * 1000 # m3당 비용 가정
    
    # 방류 농도 및 벌금 계산
    Cf = C0_future * (1 - target_eta)
    current_fine = max(0, (Cf - LEGAL_LIMIT) * FINE_PER_KG) if Cf > LEGAL_LIMIT else 0

    # 그래프용 데이터 생성
    energy_costs = [calc_energy(C0_future, e) * ELEC_PRICE * 1000 for e in eta_range]
    fines = [max(0, (C0_future * (1 - e) - LEGAL_LIMIT) * FINE_PER_KG) for e in eta_range]
    total_costs = [ec + f for ec, f in zip(energy_costs, fines)]
    
    # 최적 지점 찾기
    opt_idx = np.argmin(total_costs)
    opt_eta = eta_range[opt_idx]

    # 시각화
    fig_opt = go.Figure()
    fig_opt.add_trace(go.Scatter(x=eta_range, y=energy_costs, name='운영 비용 (전기/약품)', line=dict(color='#00d1ff')))
    fig_opt.add_trace(go.Scatter(x=eta_range, y=fines, name='법적 리스크 (부과금)', line=dict(color='#ff4b4b')))
    fig_opt.add_trace(go.Scatter(x=eta_range, y=total_costs, name='총비용 (Total)', line=dict(color='#deff9a', width=4)))
    
    # 현재 선택 지점 표시
    fig_opt.add_trace(go.Scatter(x=[target_eta], y=[current_energy_cost + current_fine], 
                                mode='markers', marker=dict(size=15, color='white'), name='현재 설정값'))

    fig_opt.update_layout(title=f"C₀={C0_future:.1f} mg/L 일 때의 비용 곡선", xaxis_title="정화 효율 (η)", yaxis_title="비용 (원/m³)")
    st.plotly_chart(fig_opt, use_container_width=True)

    # 5. 결과 가이드라인
    c1, c2, c3 = st.columns(3)
    c1.info(f"**현재 정화 후 BOD:** {Cf:.2f} mg/L")
    c2.warning(f"**현재 총 예상 비용:** {int(current_energy_cost + current_fine):,} 원/m³")
    c3.success(f"**권장 최적 효율:** {opt_eta:.2%}")

    st.caption("💡 본 가이드는 AI가 예측한 유입 오염도와 팀장님이 설계한 에너지 강도 공식을 기반으로 산출되었습니다.")