import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="ETF 추천 시스템",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사이드바 - 미니멀하고 전문적인 디자인
with st.sidebar:
    # 브랜드 로고/제목
    st.markdown("""
    <div style="text-align: center; padding: 20px 0; border-bottom: 1px solid #e0e0e0; margin-bottom: 30px;">
        <h2 style="color: #2c3e50; font-weight: 600; margin: 0; font-size: 20px;">ETF 추천시스템</h2>
        <p style="color: #7f8c8d; font-size: 12px; margin: 5px 0 0 0;">AI-Powered Investment Solution</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 진행 상황 표시
    survey_done = 'user_profile' in st.session_state
    recommendation_done = 'recommendations' in st.session_state
    
    # 단계별 진행 상황
    steps = [
        ("투자 성향 분석", survey_done),
        ("ETF 추천", recommendation_done),
        ("상세 분석", False),
        ("포트폴리오 구성", False)
    ]
    
    st.markdown("**진행 단계**")
    for i, (step_name, is_done) in enumerate(steps, 1):
        if is_done:
            st.markdown(f"<div style='color: #27ae60; font-size: 14px; margin: 8px 0;'>✓ {i}. {step_name}</div>", unsafe_allow_html=True)
        elif i == 1 and not survey_done:
            st.markdown(f"<div style='color: #3498db; font-size: 14px; margin: 8px 0; font-weight: 500;'>→ {i}. {step_name}</div>", unsafe_allow_html=True)
        elif i == 2 and survey_done and not recommendation_done:
            st.markdown(f"<div style='color: #3498db; font-size: 14px; margin: 8px 0; font-weight: 500;'>→ {i}. {step_name}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='color: #bdc3c7; font-size: 14px; margin: 8px 0;'>{i}. {step_name}</div>", unsafe_allow_html=True)
    
    # 사용자 프로필 요약 (설문 완료 시만)
    if survey_done:
        st.markdown("<div style='margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0;'></div>", unsafe_allow_html=True)
        st.markdown("**투자 프로필**")
        profile = st.session_state.user_profile
        
        risk_level = ["매우 보수적", "보수적", "중립적", "적극적", "매우 적극적"][profile['risk_tolerance']-1]
        horizon = ["단기", "중단기", "중기", "중장기", "장기"][profile['investment_horizon']-1]
        
        st.markdown(f"<div style='font-size: 12px; color: #7f8c8d; margin: 5px 0;'>위험 성향: {risk_level}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 12px; color: #7f8c8d; margin: 5px 0;'>투자 기간: {horizon}</div>", unsafe_allow_html=True)

# 메인 콘텐츠
st.title("ETF 추천 시스템")
st.markdown("### 개인 맞춤형 ETF 포트폴리오 구성 도구")

# 시작 안내
if 'user_profile' not in st.session_state:
    st.info("투자 성향 설문을 통해 맞춤형 ETF 추천을 받아보세요.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("투자 성향 설문 시작", use_container_width=True, type="primary"):
            st.switch_page("pages/1_투자성향설문.py")

else:
    # 설문 완료 후 메뉴
    st.success("투자 성향 설문이 완료되었습니다!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 다음 단계")
        if st.button("ETF 추천 받기", use_container_width=True, type="primary"):
            st.switch_page("pages/2_추천결과.py")
        
        if 'recommendations' in st.session_state:
            if st.button("상세 분석 보기", use_container_width=True):
                st.switch_page("pages/3_상세분석.py")
            
            if st.button("포트폴리오 구성", use_container_width=True):
                st.switch_page("pages/4_포트폴리오.py")
    
    with col2:
        st.markdown("#### 설문 결과 요약")
        profile = st.session_state.user_profile
        
        st.write(f"• 위험 감수 수준: {profile['risk_tolerance']}/5")
        st.write(f"• 투자 기간: {['1년 미만', '1-3년', '3-5년', '5-10년', '10년 이상'][profile['investment_horizon']-1]}")
        st.write(f"• 투자 목표: {['자산 보존', '안정적 수익', '시장 평균', '성장', '고수익'][profile['goal']-1]}")
        
        if st.button("설문 다시하기", use_container_width=True):
            # 세션 상태 초기화
            for key in ['user_profile', 'recommendations', 'recommender']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

# 시스템 정보
st.markdown("---")
st.markdown("#### 시스템 특징")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **실제 데이터 기반**
    - 82개 ETF 실시간 데이터
    - FinanceDataReader API 활용
    - 실제 시장 성과 반영
    """)

with col2:
    st.markdown("""
    **고급 분석 알고리즘**
    - UMAP 차원축소
    - KMeans 클러스터링
    - 하이브리드 추천 시스템
    """)

with col3:
    st.markdown("""
    **종합 포트폴리오 도구**
    - 자산 배분 최적화
    - 백테스팅 시뮬레이션
    - 리스크 분석
    """)

