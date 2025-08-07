import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="ETF 추천 시스템",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사이드바 - 전문적이고 간결한 디자인 (중복 제거)
with st.sidebar:
    # 브랜드 헤더
    st.markdown("""
    <div style="text-align: center; padding: 25px 0; border-bottom: 2px solid #e8ecf0; margin-bottom: 25px;">
        <h2 style="color: #1f2937; font-weight: 700; margin: 0; font-size: 22px; letter-spacing: -0.5px;">ETF 추천시스템</h2>
        <p style="color: #6b7280; font-size: 11px; margin: 8px 0 0 0; font-weight: 500;">AI-Powered Investment Solution</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 시스템 상태 및 정보
    survey_done = 'user_profile' in st.session_state
    recommendation_done = 'recommendations' in st.session_state
    
    # 사용자 프로필 정보 (설문 완료 시)
    if survey_done:
        st.markdown("**투자 프로필**")
        profile = st.session_state.user_profile
        
        risk_level = ["매우 보수적", "보수적", "중립적", "적극적", "매우 적극적"][profile['risk_tolerance']-1]
        horizon = ["단기", "중단기", "중기", "중장기", "장기"][profile['investment_horizon']-1]
        
        st.markdown(f"""
        <div style="background: #f8fafc; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <div style="font-size: 13px; color: #374151; margin-bottom: 8px;">
                <strong>위험 성향:</strong> {risk_level}
            </div>
            <div style="font-size: 13px; color: #374151;">
                <strong>투자 기간:</strong> {horizon}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 시스템 정보
    st.markdown("**시스템 정보**")
    st.markdown(f"""
    <div style="background: #f0f9ff; padding: 15px; border-radius: 8px; border-left: 4px solid #0ea5e9;">
        <div style="font-size: 12px; color: #0c4a6e; margin-bottom: 6px;">
            <strong>분석 대상:</strong> 125개 ETF
        </div>
        <div style="font-size: 12px; color: #0c4a6e; margin-bottom: 6px;">
            <strong>데이터 소스:</strong> FinanceDataReader API
        </div>
        <div style="font-size: 12px; color: #0c4a6e;">
            <strong>업데이트:</strong> 실시간 시장 데이터
        </div>
    </div>
    """, unsafe_allow_html=True)

# 메인 콘텐츠
st.title("ETF 추천 시스템")
st.markdown("### 개인 맞춤형 ETF 포트폴리오 구성 도구")

# 시작 안내
if 'user_profile' not in st.session_state:
    st.info("👈 왼쪽 사이드바에서 **투자성향설문** 페이지로 이동하여 시작하세요!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### 🎯 주요 기능
        - **AI 기반 ETF 추천**: 125개 ETF 중 맞춤형 선별
        - **실시간 데이터 분석**: FinanceDataReader API 활용
        - **고급 위험 지표**: 샤프, 소르티노, 칼마, 오메가 비율
        - **포트폴리오 최적화**: 상관관계 기반 분산 투자
        """)
    
    with col2:
        st.markdown("""
        #### 📊 분석 과정
        1. **투자 성향 분석** - 7가지 핵심 질문
        2. **ETF 추천** - AI 알고리즘 기반 선별
        3. **상세 분석** - 위험 지표 및 성과 분석
        4. **포트폴리오 구성** - 최적 분산 투자 제안
        """)

else:
    # 설문이 완료된 경우
    st.success("✅ 투자 성향 분석이 완료되었습니다!")
    st.info("👈 왼쪽 사이드바에서 **추천결과** 페이지로 이동하여 맞춤형 ETF 추천을 확인하세요!")
    
    # 사용자 프로필 요약 표시
    profile = st.session_state.user_profile
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        risk_level = ["매우 보수적", "보수적", "중립적", "적극적", "매우 적극적"][profile['risk_tolerance']-1]
        st.metric("위험 성향", risk_level)
    
    with col2:
        horizon = ["단기", "중단기", "중기", "중장기", "장기"][profile['investment_horizon']-1]
        st.metric("투자 기간", horizon)
    
    with col3:
        goal_map = {1: "안정성", 2: "성장성", 3: "수익성", 4: "균형"}
        goal = goal_map.get(profile['investment_goal'], "균형")
        st.metric("투자 목표", goal)

