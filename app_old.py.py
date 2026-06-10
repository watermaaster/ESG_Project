import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 페이지 기본 설정
st.set_page_config(page_title="지능형 ESG 수질-탄소 통합 관리 플랫폼", layout="wide")

st.markdown("""
    <style>
    h1, h2, h3 { color: #191f28 !important; font-weight: 700; }
    .stRadio>div { gap: 10px; }
    div[data-testid="stMetricText"] { font-weight: 700; color: #191f28; }
    </style>
""", unsafe_allow_html=True)

st.title("중소 식품·양조기업용 지능형 ESG 수질-탄소 통합 관리 플랫폼")
st.caption("본 플랫폼은 공정 가동률에 따른 수질 배출 부과금과 탄소 배출량의 상쇄(Trade-off) 관계를 분석하여 기업 최적의 경제적 운영 가이드라인을 제안합니다.")
st.markdown("---")

# 환경부 규제 및 공학 고정 상수
ENERGY_PER_BOD = 0.65       
CARBON_FACTOR = 0.4781      
BOD_BASE_FINE = 250        
FINE_INDEX = 5.8282         
LEGAL_BOD_LIMIT = 30.0      
CARBON_TAX_PER_KG = 35      

# 사이드바 제어 센터
st.sidebar.markdown("### 플랫폼 제어 센터")
st.sidebar.markdown("---")

data_source = st.sidebar.radio(
    "데이터 입력 방식 선택",
    ["조원 수집 샘플 데이터 사용", "실시간 수질 API / CSV 업로드"]
)

st.sidebar.markdown("<br>### 기업 환경 설정", unsafe_allow_html=True)
region_type = st.sidebar.selectbox("지역 구분 (배출 부과계수)", ["나 지역 (1.5)", "청정/가 지역 (2.0)", "특례지역 (1.0)"])
region_factor = 1.5 if "나" in region_type else (2.0 if "청정" in region_type else 1.0)

st.sidebar.markdown("<br>### 실시간 공정 제어", unsafe_allow_html=True)
target_removal_eff = st.sidebar.slider(
    "폐수 정화 장치 가동 세기 (목표 정화율 %)", 
    min_value=0, max_value=100, value=85, step=1,
    help="장치를 강하게 돌릴수록 수질은 깨끗해지지만 벌금 감소, 전력 소모가 늘어나 탄소 배출 비용이 증가합니다."
)

# 데이터 로드 파트
@st.cache_data
def load_team_data():
    np.random.seed(42)
    base_date = datetime(2026, 5, 1)
    date_list = [base_date + timedelta(days=x) for x in range(30)]
    
    input_bod = np.random.normal(loc=1500, scale=200, size=30)  
    flow_rate = np.random.uniform(low=0.01, high=0.05, size=30)  
    rainfall = np.random.choice([0.0, 0.0, 15.5, 0.0, 42.0, 5.0], size=30) 
    
    df = pd.DataFrame({
        "Date": date_list,
        "Input_BOD": input_bod,
        "Flow_Rate": flow_rate,
        "Rainfall": rainfall
    })
    return df

df_clean = load_team_data()

# 핵심 연산 엔진
df_clean['Output_BOD'] = df_clean['Input_BOD'] * (1 - target_removal_eff / 100)
df_clean['Daily_BOD_Load_kg'] = df_clean['Input_BOD'] * df_clean['Flow_Rate'] * 86.4
df_clean['Removed_BOD_kg'] = (df_clean['Input_BOD'] - df_clean['Output_BOD']) * df_clean['Flow_Rate'] * 86.4
df_clean['Carbon_Emissions_kg'] = df_clean['Removed_BOD_kg'] * ENERGY_PER_BOD * CARBON_FACTOR
df_clean['Carbon_Cost_Won'] = df_clean['Carbon_Emissions_kg'] * CARBON_TAX_PER_KG

def calculate_env_fine(row):
    out_bod = row['Output_BOD']
    flow = row['Flow_Rate']
    if out_bod <= LEGAL_BOD_LIMIT:
        return 0
    excess_bod_kg = (out_bod - LEGAL_BOD_LIMIT) * flow * 86.4
    exceed_ratio = ((out_bod - LEGAL_BOD_LIMIT) / LEGAL_BOD_LIMIT) * 100
    
    if exceed_ratio < 20: multiplier = 3.0
    elif exceed_ratio < 40: multiplier = 4.0
    elif exceed_ratio < 80: multiplier = 4.5
    elif exceed_ratio < 100: multiplier = 5.0
    elif exceed_ratio < 200: multiplier = 5.5
    elif exceed_ratio < 300: multiplier = 6.0
    elif exceed_ratio < 400: multiplier = 6.5
    else: multiplier = 7.0
    
    return excess_bod_kg * BOD_BASE_FINE * FINE_INDEX * region_factor * multiplier

df_clean['Water_Fine_Won'] = df_clean.apply(calculate_env_fine, axis=1)
df_clean['Total_ESG_Cost_Won'] = df_clean['Carbon_Cost_Won'] + df_clean['Water_Fine_Won']

# 메인 화면 탭 구성
tab1, tab2, tab3 = st.tabs(["실시간 ESG 모니터링", "경영 최적화 시뮬레이션", "AI 기반 미래 예측"])

# 탭 1: 실시간 ESG 모니터링
with tab1:
    st.markdown("### 당월 누적 주요 ESG 지표")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("평균 방류수 BOD", f"{df_clean['Output_BOD'].mean():.1f} mg/L", 
                  delta=f"{df_clean['Output_BOD'].mean() - LEGAL_BOD_LIMIT:.1f} mg/L (기준: 30)", delta_color="inverse")
    with col2:
        st.metric("누적 온실가스 배출량", f"{df_clean['Carbon_Emissions_kg'].sum():,.0f} kg CO2eq")
    with col3:
        st.metric("예상 수질 배출 부과금", f"{df_clean['Water_Fine_Won'].sum():,.0f} 원", delta_color="inverse")
    with col4:
        st.metric("총 ESG 리스크 비용", f"{df_clean['Total_ESG_Cost_Won'].sum():,.0f} 원")

    st.markdown("<br>### 일별 수질 및 규제 준수 추이", unsafe_allow_html=True)
    
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=df_clean['Date'], y=df_clean['Output_BOD'], 
        name="방류수 BOD 농도", 
        line=dict(color='#0064ff', width=2.5),
        mode='lines+markers', marker=dict(size=5)
    ))
    fig1.add_trace(go.Scatter(
        x=df_clean['Date'], y=[LEGAL_BOD_LIMIT]*30, 
        name="법적 허용 한계선", 
        line=dict(color='#ef476f', width=2, dash='dash')
    ))
    fig1.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=40, t=20, b=40),
        xaxis=dict(showgrid=True, gridcolor='#f1f3f5'),
        yaxis=dict(showgrid=True, gridcolor='#f1f3f5', title="BOD 농도 (mg/L)"),
        legend=dict(orientation="h", ylink=1.1, y=1.05, x=0)
    )
    st.plotly_chart(fig1, use_container_width=True)

# 탭 2: 경영 최적화 시뮬레이션
with tab2:
    st.markdown("### 폭기조 제어 효율에 따른 한계비용 절감 분석")
    st.caption("정화 장치를 강하게 가동할수록 환경부 배출 부과금은 감소하나, 전력 소비량 증가로 인한 탄소 배출 비용이 상승하는 트레이드오프 구간을 분석합니다.")
    
    eff_range = np.arange(0, 101, 1)
    sim_carbon_cost = []
    sim_fine_cost = []
    
    avg_row = df_clean.mean() 
    avg_input_bod = avg_row['Input_BOD']
    avg_flow = avg_row['Flow_Rate']
    
    for eff in eff_range:
        out_bod = avg_input_bod * (1 - eff / 100)
        rem_bod = (avg_input_bod - out_bod) * avg_flow * 86.4
        c_emissions = rem_bod * ENERGY_PER_BOD * CARBON_FACTOR
        c_cost = c_emissions * CARBON_TAX_PER_KG
        
        if out_bod <= LEGAL_BOD_LIMIT:
            f_cost = 0
        else:
            ex_bod = (out_bod - LEGAL_BOD_LIMIT) * avg_flow * 86.4
            ex_ratio = ((out_bod - LEGAL_BOD_LIMIT) / LEGAL_BOD_LIMIT) * 100
            if ex_ratio < 20: m = 3.0
            elif ex_ratio < 40: m = 4.0
            elif ex_ratio < 80: m = 4.5
            elif ex_ratio < 100: m = 5.0
            elif ex_ratio < 200: m = 5.5
            elif ex_ratio < 300: m = 6.0
            elif ex_ratio < 400: m = 6.5
            else: m = 7.0
            f_cost = ex_bod * BOD_BASE_FINE * FINE_INDEX * region_factor * m
            
        sim_carbon_cost.append(c_cost)
        sim_fine_cost.append(f_cost)
        
    sim_total_cost = np.array(sim_carbon_cost) + np.array(sim_fine_cost)
    optimal_eff = eff_range[np.argmin(sim_total_cost)]
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=eff_range, y=sim_carbon_cost, name="탄소 배출 비용", line=dict(color='#00c7ae', width=2)))
    fig2.add_trace(go.Scatter(x=eff_range, y=sim_fine_cost, name="수질 배출 부과금", line=dict(color='#ef476f', width=2)))
    fig2.add_trace(go.Scatter(x=eff_range, y=sim_total_cost, name="총 ESG 리스크 통합 비용", line=dict(color='#191f28', width=3)))
    
    fig2.add_vline(x=optimal_eff, line_width=2, line_dash="dash", line_color="#ffbb00")
    fig2.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=40, t=30, b=40),
        xaxis=dict(showgrid=True, gridcolor='#f1f3f5', title="BOD 제거 효율 (%)"),
        yaxis=dict(showgrid=True, gridcolor='#f1f3f5', title="일일 비용 (원)"),
        legend=dict(orientation="h", ylink=1.1, y=1.05, x=0)
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    st.info(f"현재 설정된 저감률은 {target_removal_eff}% 입니다. 법적 과태료 리스크를 최소화하고 에너지 비용을 방어하는 최적의 경영 운영 저감률은 {optimal_eff}% 임을 공학적으로 제안합니다.")

# 탭 3: AI 기반 미래 예측
with tab3:
    st.markdown("### AI 기반 향후 7일간 전력 탄소 배출량 선제 예측")
    st.info("과거 수질 트렌드 및 기상청 강우량 변수를 연동한 시계열 예측 구간입니다. 현재 베이스라인 가상 가동 중입니다.")
    
    future_dates = [df_clean['Date'].iloc[-1] + timedelta(days=x) for x in range(1, 8)]
    predicted_bod_load = np.random.normal(loc=1600, scale=100, size=7)
    predicted_carbon = predicted_bod_load * (target_removal_eff/100) * ENERGY_PER_BOD * CARBON_FACTOR
    
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=future_dates, y=predicted_carbon, 
        name="AI 예측 탄소 배출량", 
        marker_color='#0064ff',
        opacity=0.85
    ))
    fig3.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=40, t=20, b=40),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#f1f3f5', title="탄소 배출량 (kg CO2eq)"),
        showlegend=False
    )
    st.plotly_chart(fig3, use_container_width=True)
    
    st.markdown("""
        <div style='background-color:#f8f9fa; border-radius:7px; padding:15px; font-size:13px; color:#4e5968;'>
            <strong>팀장 가이드라인:</strong> 조원들이 LSTM 모델 인벤토리 학습을 완료하면, 추출된 웨이트 파일(.h5/.pkl)을 본 탭의 연산 엔진 파트와 동기화하여 실시간 데이터 연동 효율을 완성합니다.
        </div>
    """, unsafe_allow_html=True)