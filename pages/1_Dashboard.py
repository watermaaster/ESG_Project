import streamlit as st
import numpy as np
import pandas as pd

# [서버 다운 방지] Matplotlib이 웹 환경에서 충돌을 일으키지 않도록 비대화형 백엔드로 강제 고정
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

import platform
import time

# --- [0. 토스 스타일의 디벨로퍼 지향 와이드 레이아웃] ---
st.set_page_config(page_title="B2B 데이터 연동 센터", layout="wide")

# 그래프 한글 깨짐 방지 폰트 설정
if platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
elif platform.system() == 'Darwin':
    plt.rc('font', family='AppleGothic')
else:
    plt.rc('font', family='NanumBarunGothic')
plt.rcParams['axes.unicode_minus'] = False 

# --- [1. 글로벌 SaaS UI를 위한 무채색 디자인 가이드] ---
st.markdown("""
    <style>
    /* 전체적인 자잘한 폰트 및 여백 정돈 */
    .reportview-container { background: #f8f9fa; }
    h1, h2, h3 { color: #191f28 !important; font-weight: 700; }
    .stButton>button { background-color: #0064ff; color: white; border-radius: 7px; border: none; font-weight: 600; }
    .stButton>button:hover { background-color: #1b74ff; color: white; }
    </style>
""", unsafe_allow_html=True)

# 메인 헤더
st.title("B2B 환경 데이터 연동 센터")
st.caption("기업 맞춤형 규제 환경 동기화 및 실시간 공장 TMS(원격수질모니터링) API 연결을 위한 온보딩 센터입니다.")
st.markdown("---")

# ---------------------------------------------------------
# 2페이지와 데이터 싱크를 맞춘 회원사 프리셋 데이터베이스
# ---------------------------------------------------------
COMPANY_DB = {
    "(주)진천그린푸드": {
        "industry": "식품 제조업",
        "location": "충청북도 진천군 (미호강 수계 - 특별대책지역)",
        "limit": 30.0
    },
    "(주)안성가온양조": {
        "industry": "양조 및 음료 제조업",
        "location": "경기도 안성시 (한강 수계 - 일반 가 지역)",
        "limit": 20.0
    },
    "(주)구미웰빙푸드": {
        "industry": "식품 제조업",
        "location": "경상북도 구미시 (낙동강 수계 - 공공하수처리구역)",
        "limit": 20.0
    },
    "(주)여수바이오음료": {
        "industry": "양조 및 음료 제조업",
        "location": "전라남도 여수시 (영산강·섬진강 수계 - 일반 나 지역)",
        "limit": 40.0
    }
}

# ---------------------------------------------------------
# 발표 시연용 현재 실시간 방류 수질(BOD) 세팅
# ---------------------------------------------------------
CURRENT_BOD_DB = {
    "(주)진천그린푸드": 27.5,   # 제한치 30.0 -> 기준치 80% 초과로 [주의] 세팅
    "(주)안성가온양조": 12.3,   # 제한치 20.0 -> 안정권으로 [정상] 세팅
    "(주)구미웰빙푸드": 23.8,   # 제한치 20.0 -> 기준치 초과로 [위험] 세팅
    "(주)여수바이오음료": 15.0   # 제한치 40.0 -> 안정권으로 [정상] 세팅
}

# 시연용 토글 상태 관리
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False

# --- [2. 2단 분할 레이아웃 (왼쪽: Request/설정 패널, 오른쪽: Response/모니터)] ---
col_left, col_right = st.columns([5, 5])

# --- [LEFT COLUMN: 설정 및 API 입력] ---
with col_left:
    
    # 1. 사업장 및 규제 설정 (선택 시 자동 연동 및 원천 잠금)
    with st.container(border=True):
        st.markdown("### 1. 사업장 및 규제 설정")
        
        # 기업명 선택 셀렉트박스
        selected_company = st.selectbox("대상 기업을 선택하세요", list(COMPANY_DB.keys()))
        
        # 선택된 기업의 정보 매핑
        comp_info = COMPANY_DB[selected_company]
        biz_name = selected_company
        biz_type = comp_info["industry"]
        selected_region = comp_info["location"]
        legal_limit = comp_info["limit"]
        
        # Grid 레이아웃으로 묶어서 보여주되, 수정 불가(disabled=True) 상태로 락 설정
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("회사명", value=biz_name, disabled=True)
        with c2:
            st.text_input("공장 유형", value=biz_type, disabled=True)
            
        st.text_input("공장 소재지 (규제 구역 자동 매칭)", value=selected_region, disabled=True)
        
        # 법적 기준 자동 매칭 및 잠금
        st.text_input(
            "해당 지역 법적 방류 기준 (BOD 제한치)", 
            value=f"{legal_limit} mg/L", 
            disabled=True,
            help="물환경보전법 시행규칙 별표 13에 의거하여 기업 주소지에 맞는 법적 기준이 자동으로 바인딩됩니다."
        )

    # 2. 환경 TMS API 연동 정보
    with st.container(border=True):
        st.markdown("### 2. 환경 TMS API 연동 정보")
        st.text_input("EndPoint URL", value="https://api.tms.environment.go.kr/v1/signals")
        st.text_input("API Auth Key (인증 토큰)", type="password", placeholder="귀사에 발급된 고유 API Secret Key를 입력하세요")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("API 연결 테스트 진행", use_container_width=True):
            with st.spinner("TMS 인프라 서버와 보안 통신을 인증하는 중..."):
                time.sleep(1.2) # 시연용 라이브 로딩 연출
            st.session_state.api_connected = True

# --- [RIGHT COLUMN: 실시간 데이터 관제 및 프리뷰] ---
with col_right:
    
    with st.container(border=True):
        st.markdown("### 데이터 동기화 모니터")
        
        # 연결 상태에 따른 스마트 상태 배지
        if not st.session_state.api_connected:
            st.markdown("#### `상태` <span style='color:#ef476f; font-weight:bold;'>🔴 데이터 연결 대기 중 (Disconnected)</span>", unsafe_allow_html=True)
            st.markdown("---")
            
            st.info(
                f"💡 **안내:** 왼쪽 패널에서 설정을 완료하고 **[API 연결 테스트 진행]** 버튼을 누르시면, "
                f"선택하신 지역의 법적 기준({legal_limit} mg/L)과 연동되어 팀장님 고유 공학 공식 기반의 "
                f"**'지능형 가동률 관제 시스템'** 프리뷰가 활성화됩니다."
            )
            
            st.markdown("""
                <div style='background-color:#f8f9fa; border:1px dashed #ced4da; border-radius:7px; padding:60px; text-align:center; color:#6c757d; font-size:14px;'>
                    공장 실시간 TMS 데이터 스트리밍 연결 시<br>
                    실시간 방류 수질 진단 및 법적 기준선 비교 그래프가 이곳에 렌더링됩니다.
                </div>
            """, unsafe_allow_html=True)
            
        else:
            # 연결 성공 시 화면 (초록불 켜지며 실시간 차트 오픈)
            st.markdown(f"#### `상태` <span style='color:#06d6a0; font-weight:bold;'>🟢 연결 완료 ({biz_name} TMS 데이터 동기화 중)</span>", unsafe_allow_html=True)
            st.markdown("---")
            
            st.success(f"인증 완료: 타겟 규제 한계치 `{legal_limit} mg/L`가 연산 모델 엔진에 정상 동기화되었습니다.")
            
            # 실시간 환경 리스크 상태 판정 로직 및 토스 스타일 UI 렌더링
            current_bod = CURRENT_BOD_DB[selected_company]
            
            if current_bod > legal_limit:
                status_text = "⚠️ 위험 (법적 방류 기준 초과)"
                status_color = "#ef476f"  # 토스 레드 핑크
                status_bg = "#ffeef2"
            elif current_bod >= legal_limit * 0.8:
                status_text = "🚨 주의 (환경 기준치 근접)"
                status_color = "#f7b500"  # 경고 옐로우
                status_bg = "#fffbeb"
            else:
                status_text = "✅ 정상 (안정적 관리 상태)"
                status_color = "#06d6a0"  # 안전 그린
                status_bg = "#e6fbf7"
                
            st.markdown(f"""
                <div style="background-color:{status_bg}; border-left: 5px solid {status_color}; padding: 18px; border-radius: 6px; margin-bottom: 20px;">
                    <span style="font-size: 13px; color: #4e5968; font-weight: 600; display: block; margin-bottom: 4px;">실시간 방류 수질 상태 진단</span>
                    <span style="font-size: 22px; color: {status_color}; font-weight: 800; letter-spacing: -0.5px;">{status_text}</span>
                    <div style="margin-top: 8px; font-size: 14px; color: #333d4b;">
                        현재 방류수 수질: <b style="font-size: 15px; color:{status_color};">{current_bod} mg/L</b> <span style="color:#b0b8c1;">|</span> 법적 기준치: <b>{legal_limit} mg/L</b>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # ---------------------------------------------------------
            # [수정] 그래프 데이터를 '유입'이 아니라 상단 카드와 일치하는 '방류수 트렌드'로 전면 수정
            # ---------------------------------------------------------
            np.random.seed(2026)
            hours_str = [f"{i:02d}:00" for i in range(24)]
            
            # 선택된 기업의 현재 방류수 수질(current_bod) 근처에서 자연스럽게 움직이도록 난수 생성 치환
            # (마지막 시간대 데이터는 현재 카드 수치와 정확히 일치시켜 개연성을 높임)
            realtime_effluent = np.random.normal(current_bod, current_bod * 0.05, 24) 
            realtime_effluent[-1] = current_bod 
            
            fig, ax = plt.subplots(figsize=(6, 3.5))
            ax.plot(hours_str, realtime_effluent, color='#0064ff', marker='o', markersize=4, linewidth=1.5, label='실시간 방류 수질 (BOD)')
            ax.axhline(y=legal_limit, color='#ef476f', linestyle='--', linewidth=1.5, label=f'법적 방류 한계선 ({legal_limit})')
            
            # 그래프 세부 설정 및 X축 가독성 교정
            ax.set_title(f"{biz_name} 시간별 방류 수질 및 기준선 트렌드", fontsize=10, fontweight='bold', pad=10)
            ax.set_ylabel("BOD 농도 (mg/L)", fontsize=8)
            
            # Y축의 범위를 가변적으로 조정하여 그래프가 박스 안에서 가장 이쁘게 보이도록 설정
            ax.set_ylim(0, max(legal_limit, current_bod) * 1.4)
            
            # X축 글씨가 똑바로 보이고 겹치지 않도록 3시간 간격으로 틱 설정 및 회전각 0도 고정
            ax.set_xticks(hours_str[::3])
            ax.tick_params(axis='x', rotation=0, labelsize=8)
            ax.tick_params(axis='y', labelsize=8)
            
            ax.legend(fontsize=8, loc='upper right')
            ax.grid(True, linestyle=':', alpha=0.5)
            
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)  # [메모리 해제] 백그라운드 스레드가 누적되어 멈추는 현상 원천 차단