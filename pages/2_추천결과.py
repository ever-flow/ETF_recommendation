import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.real_etf_recommender import RealETFRecommender
from utils.ui_helpers import display_metric_with_help, display_large_metric_row, display_etf_card_with_help

st.set_page_config(
    page_title="ETF 추천 결과",
    page_icon="🎯",
    layout="wide"
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
    
    # 현재 단계 표시
    st.markdown("**현재 단계**")
    st.markdown("""
    <div style="background: #f8fafc; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
        <div style="font-size: 14px; color: #374151; font-weight: 600;">
            🎯 ETF 추천 결과
        </div>
        <div style="font-size: 12px; color: #6b7280; margin-top: 5px;">
            AI 분석을 통한 맞춤형 ETF 선별
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 사용자 프로필 정보
    if 'user_profile' in st.session_state:
        st.markdown("**투자 프로필**")
        profile = st.session_state.user_profile
        
        risk_level = ["매우 보수적", "보수적", "중립적", "적극적", "매우 적극적"][profile['risk_tolerance']-1]
        horizon = ["단기", "중단기", "중기", "중장기", "장기"][profile['investment_horizon']-1]
        
        st.markdown(f"""
        <div style="background: #f8fafc; padding: 15px; border-radius: 8px;">
            <div style="font-size: 13px; color: #374151; margin-bottom: 8px;">
                <strong>위험 성향:</strong> {risk_level}
            </div>
            <div style="font-size: 13px; color: #374151;">
                <strong>투자 기간:</strong> {horizon}
            </div>
        </div>
        """, unsafe_allow_html=True)

st.title("실제 데이터 기반 ETF 추천 결과")

# 설문 미완료 시 리다이렉트
if 'user_profile' not in st.session_state:
    st.warning("먼저 투자 성향 설문을 완료해주세요.")
    if st.button("투자 성향 설문하러 가기"):
        st.switch_page("pages/1_투자성향설문.py")
    st.stop()

# 사용자 프로필 요약
st.subheader("나의 투자 성향 요약")
profile = st.session_state.user_profile

col1, col2, col3 = st.columns(3)
with col1:
    risk_level = ["매우 낮음", "낮음", "보통", "높음", "매우 높음"][profile['risk_tolerance']-1]
    st.info(f"**위험 감수도**: {risk_level}")

with col2:
    horizon = ["1년 미만", "1-3년", "3-5년", "5-10년", "10년 이상"][profile['investment_horizon']-1]
    st.info(f"**투자 기간**: {horizon}")

with col3:
    goal = ["자산 보존", "안정적 수익", "시장 평균", "성장", "고수익"][profile['goal']-1]
    st.info(f"**투자 목표**: {goal}")

# ETF 추천 시스템 실행
st.markdown("---")
st.subheader("맞춤형 ETF 추천 (Top 7)")

if 'recommender' not in st.session_state:
    st.session_state.recommender = RealETFRecommender()

recommender = st.session_state.recommender

# 추천 결과 생성
if 'recommendations' not in st.session_state:
    with st.spinner("ETF 데이터를 분석하고 추천을 생성하는 중입니다..."):
        try:
            if recommender.load_and_process_data(st.session_state.user_profile):
                recommendations = recommender.generate_recommendations(st.session_state.user_profile, top_n=7)
                
                if recommendations is not None and not recommendations.empty:
                    st.session_state.recommendations = recommendations
                    st.success("추천이 완료되었습니다!")
                else:
                    st.error("추천 결과를 생성할 수 없습니다. 설문 조건을 다시 확인해주세요.")
                    st.stop()
            else:
                st.error("ETF 데이터 로딩에 실패했습니다.")
                st.stop()
        except Exception as e:
            st.error(f"추천 생성 중 오류 발생: {str(e)}")
            st.error("추천 결과를 생성할 수 없습니다. 설문 조건을 다시 확인해주세요.")
            st.stop()

recommendations = st.session_state.recommendations

# 추천 ETF 목록 표시
for i, (idx, etf) in enumerate(recommendations.iterrows()):
    with st.expander(f"#{i+1} {etf['Name']}", expanded=i==0):
        # ETF 데이터 구조 변환
        etf_data = {
            'ticker': etf['Ticker'],
            'name': etf['Name'],
            'category': etf['Category'],
            'market': etf['Market'],
            'recommendation_score': etf['Recommendation_Score'],
            'annual_return': etf['Return_1Y'],
            'volatility': etf['Volatility'],
            'sharpe_ratio': etf['Sharpe_Ratio'],
            'max_drawdown': etf['Max_Drawdown'],
            'aum': etf['AUM'],
            'expense_ratio': etf['Expense_Ratio']
        }
        
        # 새로운 UI 함수 사용
        display_etf_card_with_help(etf_data, rank=i+1)

# 추천 ETF 성과 비교 차트
st.markdown("---")
st.subheader("추천 ETF 성과 비교")

# 수익률 vs 위험도 산점도
# 샤프 비율을 양수로 변환 (size 속성용)
recommendations_plot = recommendations.copy()
recommendations_plot['Size_Sharpe'] = recommendations_plot['Sharpe_Ratio'].apply(lambda x: max(0.1, x + 2))  # 최소 0.1, 샤프비율 + 2

fig_scatter = px.scatter(
    recommendations_plot, 
    x='Volatility', 
    y='Return_1Y',
    size='Size_Sharpe',
    color='Category',
    hover_name='Name',
    hover_data=['Sharpe_Ratio', 'Max_Drawdown'],
    title="위험도 vs 수익률 분석",
    labels={
        'Volatility': '변동성 (%)',
        'Return_1Y': '1년 수익률 (%)',
        'Size_Sharpe': '샤프 비율 (크기)'
    }
)

fig_scatter.update_layout(
    xaxis_title="변동성 (%)",
    yaxis_title="1년 수익률 (%)",
    showlegend=True,
    height=500
)

st.plotly_chart(fig_scatter, use_container_width=True)

# 수익률 비교 막대차트
fig_return = px.bar(
    recommendations, 
    x='Name', 
    y='Return_1Y',
    color='Category',
    title="추천 ETF 1년 수익률 비교",
    labels={'Return_1Y': '1년 수익률 (%)', 'Name': 'ETF 이름'}
)

fig_return.update_layout(xaxis_tickangle=45, height=400)
st.plotly_chart(fig_return, use_container_width=True)

# 샤프 비율 비교
fig_sharpe = px.bar(
    recommendations, 
    x='Name', 
    y='Sharpe_Ratio',
    color='Sharpe_Ratio',
    color_continuous_scale='RdYlGn',
    title="추천 ETF 샤프 비율 비교",
    labels={'Sharpe_Ratio': '샤프 비율', 'Name': 'ETF 이름'}
)

fig_sharpe.update_layout(xaxis_tickangle=45, height=400)
st.plotly_chart(fig_sharpe, use_container_width=True)

# 다음 단계 안내
st.markdown("---")
st.subheader("다음 단계")

col1, col2 = st.columns(2)

with col1:
    if st.button("상세 분석 보기", use_container_width=True, type="primary"):
        st.switch_page("pages/3_상세분석.py")

with col2:
    if st.button("포트폴리오 구성", use_container_width=True):
        st.switch_page("pages/4_포트폴리오.py")

# 투자 주의사항
st.markdown("---")
st.info("""
**투자 주의사항**
- 이 추천은 과거 데이터를 기반으로 한 분석 결과입니다.
- 과거 성과가 미래 수익을 보장하지 않습니다.
- 실제 투자 전에 반드시 전문가와 상담하시기 바랍니다.
- 투자에는 원금 손실의 위험이 있습니다.
""")

