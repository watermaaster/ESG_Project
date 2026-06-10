import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="지능형 ESG 통합 플랫폼", layout="wide")

# 대문 홈 화면 UI 디자인
st.title(" 지능형 ESG 수질-탄소 통합 관리 플랫폼")
st.markdown("---")

st.subheader(" 플랫폼 핵심 서비스 로드맵")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ###  1. 우리 공장 종합 관제탑 (`Dashboard`)
    * 로그인한 기업의 실시간 수질 상태 및 누적 탄소 배출량 모니터링
    * 환경부 법령 기준 초과 시 실시간 리스크 비용 산출
    """)
    # 1번 페이지(대시보드) 이동
    if st.button(" 관제탑으로 이동하기", type="primary"):
        st.switch_page("pages/1_Dashboard.py")
    
    st.markdown("---")
    
    st.markdown("""
    ###  2. 지역·업종별 벤치마킹 (`Analytics`)
    * WAMIS(국가수자원관리) 데이터 기반 전국 업종별 원단위 비교
    * 지자체별 상이한 환경 조례 및 규제 매칭 시스템
    """)
    # [연동 완료] 방금 만든 2번 페이지(Analytics)로 바로 점프합니다.
    if st.button(" 전국 벤치마킹 보러가기", type="primary"):
        st.switch_page("pages/2_Analytics.py")

with col2:
    st.markdown("""
    ###  3. 실시간 데이터 셋업룸 (`Data Management`)
    * 기상청 API 연동을 통한 실시간 강수량 및 공장 유량 데이터 수집
    * **4페이지 AI 모델**에 공급될 실시간 데이터 파이프라인 관리
    """)
    # 3번 페이지(Data_Hub) 이동
    if st.button(" 데이터 셋업룸으로 이동하기", type="primary"):
        st.switch_page("pages/3_Data_Hub.py")
        
    st.markdown("---")
        
    st.markdown("""
    ###  4. AI 미래 리스크 예보 (`AI Forecast`)
    * LSTM 신경망 기반 향후 7일간의 오염 농도($C_0$) 정밀 예측
    * **운영 최적화 공식**을 적용한 에너지 비용 vs 벌금 리스크 시뮬레이션
    """)
    # 4번 페이지(AI 예보) 이동
    if st.button(" AI 예보창으로 이동하기", type="primary"):
        st.switch_page("pages/4_AI_Forecast.py")