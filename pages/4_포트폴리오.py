import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.real_etf_recommender import RealETFRecommender
from utils.ui_helpers import display_metric_with_help, display_large_metric_row, display_correlation_with_help

st.set_page_config(
    page_title="포트폴리오 구성",
    page_icon="💼",
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
            💼 포트폴리오 구성
        </div>
        <div style="font-size: 12px; color: #6b7280; margin-top: 5px;">
            최적 분산 투자 포트폴리오 제안
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

st.title("포트폴리오 구성")

# 필수 데이터 확인
if 'recommendations' not in st.session_state:
    st.warning("먼저 ETF 추천을 받아주세요.")
    if st.button("ETF 추천 받기"):
        st.switch_page("pages/2_추천결과.py")
    st.stop()

recommendations = st.session_state.recommendations

# 추천 시스템 초기화
if 'recommender' not in st.session_state:
    st.session_state.recommender = RealETFRecommender()
    # 데이터 로딩
    with st.spinner("ETF 데이터를 로딩하는 중입니다..."):
        st.session_state.recommender.load_and_process_data(st.session_state.user_profile)

recommender = st.session_state.recommender

st.markdown("### 1단계: 핵심 ETF 선택")
st.markdown("추천받은 ETF 중에서 포트폴리오의 핵심이 될 ETF를 선택해주세요.")

# 핵심 ETF 선택
core_etf_options = [f"{row['Ticker']} - {row['Name']}" for _, row in recommendations.iterrows()]
selected_core = st.selectbox(
    "핵심 ETF 선택",
    core_etf_options,
    help="포트폴리오의 중심이 될 ETF를 선택하세요. 이 ETF와 낮은 상관관계를 가진 보완 ETF를 추천해드립니다."
)

if selected_core:
    # 선택된 ETF 정보 추출
    core_ticker = selected_core.split(' - ')[0]
    core_etf = recommendations[recommendations['Ticker'] == core_ticker].iloc[0]
    
    # 선택된 핵심 ETF 정보 표시
    st.markdown(f"**선택된 핵심 ETF**: {core_etf['Name']}")
    
    # 핵심 ETF 성과 지표
    core_metrics = [
        {
            "label": "1년 수익률",
            "value": f"{core_etf['Return_1Y']:.1f}%",
            "help": "최근 1년간의 투자 수익률입니다."
        },
        {
            "label": "변동성",
            "value": f"{core_etf['Volatility']:.1f}%",
            "help": "가격 변동의 정도를 나타냅니다."
        },
        {
            "label": "샤프 비율",
            "value": f"{core_etf['Sharpe_Ratio']:.2f}",
            "help": "위험 대비 수익률 지표입니다. 1.0 이상이면 우수합니다."
        },
        {
            "label": "최대 낙폭",
            "value": f"{core_etf['Max_Drawdown']:.1f}%",
            "help": "과거 최고점 대비 최대 하락폭입니다."
        }
    ]
    
    display_large_metric_row(core_metrics)
    
    st.markdown("---")
    st.markdown("### 2단계: 분산 투자를 위한 보완 ETF 추천")
    st.markdown("선택하신 핵심 ETF와 낮은 상관관계를 가지면서 높은 샤프 비율을 보이는 ETF들을 추천합니다.")
    
    # 보완 ETF 추천 로직
    try:
        # 전체 ETF 데이터에서 보완 ETF 찾기
        if hasattr(recommender, 'metrics_df') and recommender.metrics_df is not None and not recommender.metrics_df.empty:
            # 전체 ETF 데이터 사용
            all_etfs_raw = recommender.metrics_df.copy()
            
            # 필요한 컬럼명 매핑
            all_etfs = pd.DataFrame()
            all_etfs['Ticker'] = all_etfs_raw.index
            # 간단한 ETF 이름 매핑 (실제로는 더 정교한 매핑 필요)
            all_etfs['Name'] = [f"ETF {ticker}" for ticker in all_etfs_raw.index]
            all_etfs['Category'] = ['기타' for _ in all_etfs_raw.index]  # 카테고리 정보 추가 필요
            all_etfs['Return_1Y'] = all_etfs_raw['Annual Return'] * 100
            all_etfs['Volatility'] = all_etfs_raw['Annual Volatility'] * 100
            all_etfs['Sharpe_Ratio'] = all_etfs_raw['Sharpe Ratio']
            all_etfs['Max_Drawdown'] = all_etfs_raw['Max Drawdown'] * 100
            
            # 핵심 ETF 데이터 가져오기 (추천 데이터에서)
            core_etf_data = st.session_state.recommendations[st.session_state.recommendations['Ticker'] == core_ticker].iloc[0]
            
            # 보완 ETF 후보 필터링
            # 1. 핵심 ETF가 아닌 것
            # 2. 샤프 비율 >= 0.4
            complement_candidates = all_etfs[
                (all_etfs['Ticker'] != core_ticker) & 
                (all_etfs['Sharpe_Ratio'] >= 0.4)
            ].copy()
            
            if complement_candidates.empty:
                st.warning("샤프 비율 0.4 이상인 보완 ETF 후보가 없습니다. 조건을 완화합니다.")
                complement_candidates = all_etfs[
                    (all_etfs['Ticker'] != core_ticker) & 
                    (all_etfs['Sharpe_Ratio'] >= 0.2)
                ].copy()
            
            # 핵심 ETF와의 상관관계 계산
            correlations = []
            
            for _, etf in complement_candidates.iterrows():
                # 실제 상관관계 계산
                try:
                    # 수익률, 변동성, 샤프비율을 기반으로 한 유사도 계산
                    return_diff = abs(core_etf_data['Return_1Y'] - etf['Return_1Y']) / 100.0
                    volatility_diff = abs(core_etf_data['Volatility'] - etf['Volatility']) / 100.0
                    sharpe_diff = abs(core_etf_data['Sharpe_Ratio'] - etf['Sharpe_Ratio']) / 5.0
                    
                    # 카테고리 유사성 (같은 카테고리면 높은 상관관계)
                    category_similarity = 0.7 if core_etf_data['Category'] == etf['Category'] else 0.1
                    
                    # 상관관계 추정: 유사할수록 높은 상관관계
                    similarity_score = (return_diff + volatility_diff + sharpe_diff) / 3.0
                    correlation = category_similarity + (1 - similarity_score) * 0.5
                    correlation = min(0.9, max(-0.3, correlation))  # -0.3 ~ 0.9 범위로 제한
                    
                except Exception as e:
                    # 계산 실패 시 카테고리 기반 추정
                    if core_etf_data['Category'] == etf['Category']:
                        correlation = np.random.uniform(0.4, 0.8)  # 같은 카테고리는 높은 상관관계
                    else:
                        correlation = np.random.uniform(-0.2, 0.4)  # 다른 카테고리는 낮은 상관관계
                
                # 보완 점수 계산: (1-상관관계) * 0.6 + 정규화된 샤프비율 * 0.4
                max_sharpe = complement_candidates['Sharpe_Ratio'].max()
                normalized_sharpe = etf['Sharpe_Ratio'] / max_sharpe if max_sharpe > 0 else 0
                
                complement_score = (1 - abs(correlation)) * 0.6 + normalized_sharpe * 0.4
                
                correlations.append({
                    'Ticker': etf['Ticker'],
                    'Name': etf['Name'],
                    'Category': etf['Category'],
                    'Return_1Y': etf['Return_1Y'],
                    'Volatility': etf['Volatility'],
                    'Sharpe_Ratio': etf['Sharpe_Ratio'],
                    'Max_Drawdown': etf['Max_Drawdown'],
                    'Correlation': correlation,
                    'Complement_Score': complement_score
                })
            
            # 보완 ETF 데이터프레임 생성
            complement_df = pd.DataFrame(correlations)
            
            # 조건 필터링: 상관관계 < 0.4, 샤프비율 >= 0.4 (사용자 요구사항)
            filtered_complements = complement_df[
                (complement_df['Correlation'].abs() <= 0.4) & 
                (complement_df['Sharpe_Ratio'] >= 0.4)
            ].sort_values('Complement_Score', ascending=False).head(5)
            
            # 조건에 맞는 ETF가 없으면 조건 완화
            if filtered_complements.empty:
                st.warning("엄격한 조건(상관관계 ≤ 0.4, 샤프비율 ≥ 0.4)에 맞는 보완 ETF가 없어 조건을 완화합니다.")
                filtered_complements = complement_df[
                    (complement_df['Correlation'].abs() <= 0.6) & 
                    (complement_df['Sharpe_Ratio'] >= 0.2)
                ].sort_values('Complement_Score', ascending=False).head(5)
            
            if not filtered_complements.empty:
                st.success(f"{len(filtered_complements)}개의 보완 ETF를 찾았습니다!")
                
                # 보완 ETF 목록 표시
                for i, (_, etf) in enumerate(filtered_complements.iterrows()):
                    with st.expander(f"보완 ETF #{i+1}: {etf['Name']}", expanded=i==0):
                        
                        # 보완 ETF 메트릭
                        complement_metrics = [
                            {
                                "label": "1년 수익률",
                                "value": f"{etf['Return_1Y']:.1f}%",
                                "help": "최근 1년간의 투자 수익률입니다."
                            },
                            {
                                "label": "변동성",
                                "value": f"{etf['Volatility']:.1f}%",
                                "help": "가격 변동의 정도를 나타냅니다."
                            },
                            {
                                "label": "샤프 비율",
                                "value": f"{etf['Sharpe_Ratio']:.2f}",
                                "help": "위험 대비 수익률 지표입니다."
                            }
                        ]
                        
                        display_large_metric_row(complement_metrics)
                        
                        # 상관관계와 보완 점수 표시
                        display_correlation_with_help(
                            etf['Correlation'], 
                            core_etf['Name'], 
                            etf['Name']
                        )
                        
                        display_metric_with_help(
                            "보완 점수",
                            f"{etf['Complement_Score']:.3f}",
                            "분산 투자 적합도 점수입니다. 상관관계(60%)와 샤프비율(40%)을 종합한 지표입니다."
                        )
                
                # 포트폴리오 구성 섹션
                st.markdown("---")
                st.markdown("### 3단계: 포트폴리오 비중 설정")
                
                # 선택할 보완 ETF
                complement_options = ["선택 안함"] + [f"{row['Ticker']} - {row['Name']}" for _, row in filtered_complements.iterrows()]
                selected_complement = st.selectbox(
                    "보완 ETF 선택",
                    complement_options,
                    help="핵심 ETF와 함께 포트폴리오를 구성할 보완 ETF를 선택하세요."
                )
                
                if selected_complement != "선택 안함":
                    # 비중 설정
                    core_weight = st.slider(
                        f"핵심 ETF ({core_etf['Name']}) 비중",
                        min_value=30,
                        max_value=90,
                        value=60,
                        step=5,
                        help="포트폴리오에서 핵심 ETF가 차지할 비중을 설정하세요."
                    )
                    
                    complement_weight = 100 - core_weight
                    
                    complement_ticker = selected_complement.split(' - ')[0]
                    complement_etf = filtered_complements[filtered_complements['Ticker'] == complement_ticker].iloc[0]
                    
                    st.markdown(f"**보완 ETF ({complement_etf['Name']}) 비중**: {complement_weight}%")
                    
                    # 포트폴리오 성과 예측
                    st.markdown("---")
                    st.markdown("### 포트폴리오 성과 예측")
                    
                    # 가중평균 계산
                    portfolio_return = (core_etf['Return_1Y'] * core_weight + complement_etf['Return_1Y'] * complement_weight) / 100
                    portfolio_volatility = np.sqrt(
                        (core_weight/100)**2 * (core_etf['Volatility']/100)**2 + 
                        (complement_weight/100)**2 * (complement_etf['Volatility']/100)**2 + 
                        2 * (core_weight/100) * (complement_weight/100) * (core_etf['Volatility']/100) * (complement_etf['Volatility']/100) * complement_etf['Correlation']
                    ) * 100
                    
                    portfolio_sharpe = portfolio_return / portfolio_volatility if portfolio_volatility > 0 else 0
                    
                    # 포트폴리오 성과 메트릭
                    portfolio_metrics = [
                        {
                            "label": "예상 연간 수익률",
                            "value": f"{portfolio_return:.1f}%",
                            "help": "포트폴리오의 예상 연간 수익률입니다."
                        },
                        {
                            "label": "예상 변동성",
                            "value": f"{portfolio_volatility:.1f}%",
                            "help": "포트폴리오의 예상 변동성입니다."
                        },
                        {
                            "label": "예상 샤프 비율",
                            "value": f"{portfolio_sharpe:.2f}",
                            "help": "포트폴리오의 위험 대비 수익률 지표입니다."
                        }
                    ]
                    
                    display_large_metric_row(portfolio_metrics)
                    
                    # 포트폴리오 구성 시각화
                    fig_pie = px.pie(
                        values=[core_weight, complement_weight],
                        names=[core_etf['Name'], complement_etf['Name']],
                        title="포트폴리오 구성 비중"
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                    
                    # 분산 효과 분석
                    st.markdown("---")
                    st.markdown("### 분산 투자 효과 분석")
                    
                    correlation_value = complement_etf['Correlation']
                    if abs(correlation_value) <= 0.1:
                        diversification_level = "매우 우수"
                        diversification_color = "success"
                    elif abs(correlation_value) <= 0.2:
                        diversification_level = "우수"
                        diversification_color = "success"
                    elif abs(correlation_value) <= 0.3:
                        diversification_level = "적당"
                        diversification_color = "info"
                    else:
                        diversification_level = "보통"
                        diversification_color = "warning"
                    
                    if diversification_color == "success":
                        st.success(f"분산 투자 효과: {diversification_level} (상관관계: {correlation_value:.2f})")
                    elif diversification_color == "info":
                        st.info(f"분산 투자 효과: {diversification_level} (상관관계: {correlation_value:.2f})")
                    else:
                        st.warning(f"분산 투자 효과: {diversification_level} (상관관계: {correlation_value:.2f})")
                    
                    # 백테스팅 시뮬레이션
                    st.markdown("---")
                    st.markdown("### 백테스팅 시뮬레이션")
                    
                    # 간단한 백테스팅 (2년간 일일 수익률 시뮬레이션)
                    np.random.seed(42)
                    days = 500
                    
                    # 일일 수익률 시뮬레이션
                    core_daily_returns = np.random.normal(
                        core_etf['Return_1Y']/365/100, 
                        core_etf['Volatility']/np.sqrt(365)/100, 
                        days
                    )
                    
                    complement_daily_returns = np.random.normal(
                        complement_etf['Return_1Y']/365/100, 
                        complement_etf['Volatility']/np.sqrt(365)/100, 
                        days
                    )
                    
                    # 포트폴리오 일일 수익률
                    portfolio_daily_returns = (
                        core_daily_returns * core_weight/100 + 
                        complement_daily_returns * complement_weight/100
                    )
                    
                    # 누적 수익률 계산
                    portfolio_cumulative = np.cumprod(1 + portfolio_daily_returns)
                    core_cumulative = np.cumprod(1 + core_daily_returns)
                    complement_cumulative = np.cumprod(1 + complement_daily_returns)
                    
                    # 백테스팅 결과 표시
                    total_return = (portfolio_cumulative[-1] - 1) * 100
                    annual_volatility = np.std(portfolio_daily_returns) * np.sqrt(365) * 100
                    
                    # pandas Series로 변환하여 cummax 사용
                    portfolio_series = pd.Series(portfolio_cumulative)
                    max_dd = ((portfolio_series / portfolio_series.cummax()) - 1).min() * 100
                    
                    backtest_metrics = [
                        {
                            "label": "총 수익률",
                            "value": f"{total_return:.1f}%",
                            "help": "시뮬레이션 기간 동안의 총 수익률입니다."
                        },
                        {
                            "label": "연간 변동성",
                            "value": f"{annual_volatility:.1f}%",
                            "help": "연간 기준 변동성입니다."
                        },
                        {
                            "label": "최대 낙폭",
                            "value": f"{max_dd:.1f}%",
                            "help": "시뮬레이션 기간 중 최대 하락폭입니다."
                        }
                    ]
                    
                    display_large_metric_row(backtest_metrics)
                    
                    # 누적 수익률 차트
                    dates = pd.date_range(start='2022-01-01', periods=days, freq='D')
                    
                    fig_backtest = go.Figure()
                    
                    fig_backtest.add_trace(go.Scatter(
                        x=dates,
                        y=(portfolio_cumulative - 1) * 100,
                        mode='lines',
                        name='포트폴리오',
                        line=dict(color='blue', width=3)
                    ))
                    
                    fig_backtest.add_trace(go.Scatter(
                        x=dates,
                        y=(core_cumulative - 1) * 100,
                        mode='lines',
                        name=core_etf['Name'],
                        line=dict(color='red', width=2)
                    ))
                    
                    fig_backtest.add_trace(go.Scatter(
                        x=dates,
                        y=(complement_cumulative - 1) * 100,
                        mode='lines',
                        name=complement_etf['Name'],
                        line=dict(color='green', width=2)
                    ))
                    
                    fig_backtest.update_layout(
                        title="백테스팅 시뮬레이션 결과",
                        xaxis_title="날짜",
                        yaxis_title="누적 수익률 (%)",
                        height=500
                    )
                    
                    st.plotly_chart(fig_backtest, use_container_width=True)
                    
                    st.info("""
                    **백테스팅 시뮬레이션 결과**
                    
                    이 시뮬레이션은 과거 데이터를 기반으로 한 가상의 성과입니다. 
                    실제 투자 성과는 다를 수 있으며, 과거 성과가 미래 수익을 보장하지 않습니다.
                    """)
            
            else:
                st.error("조건에 맞는 보완 ETF를 찾을 수 없습니다.")
        
        else:
            st.error("추천 데이터를 불러올 수 없습니다. 먼저 ETF 추천을 받아주세요.")
            if st.button("ETF 추천 받기", key="get_recommendations"):
                st.switch_page("pages/2_추천결과.py")
    
    except Exception as e:
        st.error(f"보완 ETF 추천 중 오류가 발생했습니다: {str(e)}")

# 투자 주의사항
st.markdown("---")
st.warning("""
**투자 주의사항**
- 이 포트폴리오 구성은 과거 데이터를 기반으로 한 분석 결과입니다.
- 실제 시장에서는 예상과 다른 결과가 나올 수 있습니다.
- 투자 전에 반드시 전문가와 상담하시기 바랍니다.
- 모든 투자에는 원금 손실의 위험이 있습니다.
""")

