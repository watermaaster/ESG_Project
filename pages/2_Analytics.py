import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px  # X축 글씨 정렬 및 고도화된 시각화를 위해 도입

# 페이지 기본 설정
st.set_page_config(page_title="지역·업종별 벤치마킹", layout="wide")

st.title(" 지역·업종별 ESG 벤치마킹 가이드라인 ")
st.markdown("선택한 기업의 소재지와 업종 환경부 공인 통계 데이터를 기반으로 맞춤형 비교 분석을 수행합니다.")
st.markdown("---")

# ---------------------------------------------------------
# 백엔드 데이터베이스 정의 (1페이지 연동용 기업 프리셋 데이터)
# ---------------------------------------------------------
COMPANY_DB = {
    "(주)진천그린푸드": {
        "industry": "식품 제조업",
        "location": "충북 진천",
        "user_bod": 15.0,
        "revenue": 150,     # 억원
        "daily_flow": 20000, # 일일 폐수 방류량 (m3/day)
    },
    "(주)안성가온양조": {
        "industry": "양조 및 음료 제조업",
        "location": "경기 안성",
        "user_bod": 18.5,
        "revenue": 80,
        "daily_flow": 6500,
    },
    "(주)구미웰빙푸드": {
        "industry": "식품 제조업",
        "location": "경북 구미",
        "user_bod": 23.0,   # 법적 기준(20) 초과 시나리오 시연용
        "revenue": 220,
        "daily_flow": 31500,
    },
    "(주)여수바이오음료": {
        "industry": "양조 및 음료 제조업",
        "location": "전남 여수",
        "user_bod": 28.0,
        "revenue": 410,
        "daily_flow": 27500,
    }
}

INDUSTRY_STATS = {
    "식품 제조업": {
        "raw_bod": 950.0,       # 유입 수질 C0 (mg/L)
        "discharged_bod": 18.5, # 전국 평균 방류 수질 (mg/L)
        "carbon_intensity": 15.4,
        "desc": "농산물 원료 사용으로 초기 오염도(Raw BOD)가 높고 대규모 세척 공정으로 폐수량이 많음"
    },
    "양조 및 음료 제조업": {
        "raw_bod": 1600.0,      # 유입 수질 C0 (mg/L)
        "discharged_bod": 22.4, # 전국 평균 방류 수질 (mg/L)
        "carbon_intensity": 12.8,
        "desc": "발효 부산물로 인해 유기물 농도가 매우 높으며 살균/세척 에너지가 많이 소모됨"
    }
}

LOCATION_REGULATION = {
    "충북 진천": {"limit": 30.0, "zone": "금강 수계 상류 (가지역)"},
    "경기 안성": {"limit": 20.0, "zone": "한강 수계 상류 (가지역 - 엄격)"},
    "경북 구미": {"limit": 20.0, "zone": "낙동강 수계 (산단 특례 기준)"},
    "전남 여수": {"limit": 40.0, "zone": "영산강·섬진강 하류 (나지역)"}
}

# ---------------------------------------------------------
# 사이드바 컨트롤러 (1P 스타일로 기업 선택 시 하위 정보 자동 고정)
# ---------------------------------------------------------
st.sidebar.header(" 회원사 선택 가이드")

# 1. 회사명 선택
selected_company = st.sidebar.selectbox("대상 기업을 선택하세요", list(COMPANY_DB.keys()))

# 2. 선택된 회사 데이터 기반으로 업종, 소재지, 내부 데이터 자동 락(Lock)
comp_data = COMPANY_DB[selected_company]
current_industry = comp_data["industry"]
current_location = comp_data["location"]

# 사이드바 화면에 락 걸린 정보 시각화 표시 (수정 불가능하도록 고정)
st.sidebar.markdown("---")
st.sidebar.text_input(" 매칭된 업종 유형", value=current_industry, disabled=True)
st.sidebar.text_input(" 매칭된 공장 소재지", value=current_location, disabled=True)

# 실시간 분석용 변수 매핑
ind_data = INDUSTRY_STATS[current_industry]
loc_data = LOCATION_REGULATION[current_location]
user_bod = comp_data["user_bod"]
user_revenue = comp_data["revenue"]
user_daily_flow = comp_data["daily_flow"] 
raw_bod = ind_data["raw_bod"]             

# ---------------------------------------------------------
# 상단 관제 브리핑 대시보드
# ---------------------------------------------------------
st.subheader(f" {selected_company} 맞춤형 규제 제어 모드")
col_brief1, col_brief2, col_brief3 = st.columns(3)

with col_brief1:
    st.info(f"**지정 업종 표준**\n\n{current_industry}\n\n*{ind_data['desc']}*")
with col_brief2:
    st.warning(f"**소재지 관할 법령**\n\n{current_location}\n\n*적용 수계: {loc_data['zone']}*")
with col_brief3:
    st.error(f"**지역 법적 방류 기준치**\n\n### {loc_data['limit']} mg/L 이하")

st.markdown("---")

# ---------------------------------------------------------
# 1. 수질 오염물질 배출량 벤치마킹 (Plotly 기반 시각화)
# ---------------------------------------------------------
st.subheader(" 1. 수질 오염도(BOD) 지자체 기준 및 전국 평균 비교")

col_w1, col_w2 = st.columns([2, 1])

with col_w1:
    chart_data = pd.DataFrame({
        "비교 대상": ["전국 업종 평균", f"{selected_company} (현재)", "지자체 법적 기준"],
        "BOD 농도 (mg/L)": [ind_data["discharged_bod"], user_bod, loc_data["limit"]]
    })
    
    fig_bod = px.bar(
        chart_data, 
        x="비교 대상", 
        y="BOD 농도 (mg/L)", 
        color="비교 대상",
        text="BOD 농도 (mg/L)",
        color_discrete_sequence=["#5A738E", "#00d1ff", "#FF4B4B"]
    )
    
    fig_bod.update_xaxes(tickangle=0, title_text="")
    fig_bod.update_traces(texttemplate='%{text:.1f} mg/L', textposition='outside')
    fig_bod.update_layout(showlegend=False, height=400, margin=dict(t=10, b=10))
    
    st.plotly_chart(fig_bod, use_container_width=True)

with col_w2:
    st.markdown("#####  수질 벤치마킹 진단")
    st.write(f"현재 **{selected_company}**의 방류 수질은 **{user_bod} mg/L**입니다.")
    
    if user_bod > loc_data["limit"]:
        st.error(f"🚨 **법령 위반 상태:** {current_location}의 법적 기준치({loc_data['limit']} mg/L)를 초과했습니다! 과태료 처분 및 조업 정지 리스크가 있으므로 4페이지 AI 예보 제어 시스템 가동이 시급합니다.")
    elif user_bod > ind_data["discharged_bod"]:
        st.warning(f"⚠️ **경고:** 법적 규제선은 준수 중이나, 전국 동종 업계 평균({ind_data['discharged_bod']} mg/L)보다는 높습니다. 공정 정밀화 셋업을 권장합니다.")
    else:
        st.success(f"✅ **우수 등급:** 지자체 엄격 규제선 및 전국 업종 평균치보다 깨끗하게 관리되고 있는 모범 공장입니다.")

st.markdown("---")

# ---------------------------------------------------------
# 2. 탄소 배출 원단위 벤치마킹 (공학 알고리즘 연동)
# ---------------------------------------------------------
st.subheader(" 2. 매출액 대비 탄소 배출 원단위 비교")

# 공학식 기반 연산 파이프라인
user_daily_bod_load = user_daily_flow * (raw_bod - user_bod) / 1000
user_daily_power = user_daily_bod_load * 0.65
user_calculated_carbon = (user_daily_power * 0.4781) * 365 / 1000

user_intensity = round(user_calculated_carbon / user_revenue, 1)
avg_intensity = ind_data["carbon_intensity"]

with st.expander(" 오염 부하량 기반 온실가스(Scope 2) 실시간 추산 메커니즘 확인 (보고서 연동)"):
    st.markdown(f"***알고리즘 입력 활동도 데이터:* 일일 폐수량 $Q$ = {user_daily_flow:,} $m^3/\mathbf{{day}}$, 유입수 농도 $C_0$ = {raw_bod} $mg/\mathbf{{L}}$**")
    c_exp1, c_exp2, c_exp3 = st.columns(3)
    c_exp1.metric(label="일일 BOD 제거 부하량 [식2]", value=f"{user_daily_bod_load:,.1f} kg/day")
    c_exp2.metric(label="폐수 처리 일일 전력량 [식3]", value=f"{user_daily_power:,.1f} kWh/day")
    c_exp3.metric(label="추산 연간 온실가스 총량 [식4]", value=f"{user_calculated_carbon:,.1f} tCO2eq")

col_c1, col_c2 = st.columns([1, 2])

with col_c1:
    st.metric(label=f"{selected_company} 탄소 집약도", value=f"{user_intensity} tCO2eq/억원")
    st.metric(label="전국 동종 업종 평균 집약도", value=f"{avg_intensity} tCO2eq/억원", delta=round(user_intensity - avg_intensity, 1), delta_color="inverse")

with col_c2:
    carbon_chart_data = pd.DataFrame({
        "기업 구분": ["전국 업종 평균", "우리 공장 (현재)"],
        "탄소 원단위 (tCO2eq / 억원)": [avg_intensity, user_intensity]
    })
    
    fig_carbon = px.bar(
        carbon_chart_data, 
        x="기업 구분", 
        y="탄소 원단위 (tCO2eq / 억원)",
        color="기업 구분",
        text="탄소 원단위 (tCO2eq / 억원)",
        color_discrete_sequence=["#5A738E", "#deff9a"]
    )
    
    fig_carbon.update_xaxes(tickangle=0, title_text="")
    fig_carbon.update_traces(texttemplate='%{text:.1f} tCO2eq', textposition='outside')
    fig_carbon.update_layout(showlegend=False, height=400, margin=dict(t=10, b=10))
    
    st.plotly_chart(fig_carbon, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------
# 3. 종합 ESG 환경 등급 결합 체계 [보고서 2.2.3장 100% 동기화 리팩토링]
# ---------------------------------------------------------
st.subheader(" 3. 정량 지표 기반 통합 ESG 환경 등급")

# [수정포인트] 앞선 두 지표(수질, 탄소)의 연산 결과를 50점 만점씩 결합하는 프레임워크 구현

# (1) 수질 환경 관리 점수 계산 (50점 만점)
water_score = 0
half_limit = loc_data["limit"] * 0.5

if user_bod <= half_limit and user_bod < ind_data["discharged_bod"]:
    water_score = 50  # 최우수
elif user_bod <= loc_data["limit"]:
    water_score = 40  # 우수 (평균 이상 혹은 법적 기준 이하)
else:
    water_score = 20  # 취약 (법적 규제치 초과)

# (2) 기후변화 대응 탄소 효율 점수 계산 (50점 만점)
carbon_score = 0
if user_intensity <= avg_intensity:
    carbon_score = 50  # 최우수 (업종 평균 이하)
elif user_intensity <= avg_intensity * 1.5:
    carbon_score = 30  # 보통
else:
    carbon_score = 10  # 미흡 (업종 평균 150% 초과)

# (3) 종합 E-Score 합산 (100점 만점)
total_e_score = water_score + carbon_score

# (4) 중소벤처기업부 구간 가이드라인에 따른 최종 등급 매핑
if total_e_score >= 90:
    grade = "S 등급 (탁월)"
    color_func = st.success
    msg = " 규제 준수 상태가 완벽하며, 전국 업종 평균 대비 탄소 및 수질 관리 성과가 모두 최상위권인 ESG 모범 기업입니다."
elif total_e_score >= 80:
    grade = "A 등급 (우수)"
    color_func = st.info
    msg = " 안정적인 환경 규제 대응 능력을 갖추고 있으며, 업종 평균 이상의 우수한 환경 경영을 실천하고 있습니다."
elif total_e_score >= 70:
    grade = "B 등급 (보통)"
    color_func = st.warning
    msg = " 법적 방류 기준은 통과하였으나, 동종 업계 평균 대비 수질 정화 효율이나 탄소 원단위 측면에서 추가적인 공정 개선 여지가 존재합니다."
elif total_e_score >= 60:
    grade = "C 등급 (취약)"
    color_func = st.error
    msg = "⚠️ 간헐적인 법적 기준 초과 우려가 있거나, 매출액 대비 탄소 배출량이 과다하여 공급망 실사 대응에 취약할 수 있습니다."
else:
    grade = "D 등급 (위험)"
    color_func = st.error
    msg = "🚨 법적 방류 기준 초과 리스크가 상존하며, 탄소 배출 효율이 극히 저조하여 긴급한 공정 최적화 및 인프라 개선이 시급합니다."

# 화면 표출
st.metric(label="통합 환경 성과 스코어 (Total E-Score)", value=f"{total_e_score} / 100 점")
color_func(f"### 최종 매핑 환경 등급: {grade}")
st.markdown(f"**종합 결합 평가:** {msg}")

st.caption("※ 본 통계 자료 및 법적 기준 근거: 환경부 산업폐수 배출실태조사 결과보고서 / 온실가스종합정보센터 국가 온실가스 인벤토리 보고서 / 물환경보전법 시행규칙 [별표 13]")