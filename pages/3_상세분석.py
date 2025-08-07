import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.ui_helpers import display_metric_with_help, display_large_metric_row, display_advanced_metrics_with_help, display_correlation_with_help

st.set_page_config(
    page_title="상세 분석",
    page_icon="📈",
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
            📈 상세 분석
        </div>
        <div style="font-size: 12px; color: #6b7280; margin-top: 5px;">
            위험 지표 및 성과 분석
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

st.title("ETF 상세 분석")

# 추천 결과 확인
if 'recommendations' not in st.session_state:
    st.warning("먼저 추천 결과를 확인해주세요.")
    if st.button("추천 결과 보기"):
        st.switch_page("pages/2_추천결과.py")
    st.stop()

recommendations = st.session_state.recommendations
recommender = st.session_state.recommender

st.subheader("개별 ETF 상세 분석")

# ETF 선택
selected_etf_name = st.selectbox(
    "분석할 ETF를 선택하세요:",
    options=[f"{row['Ticker']} - {row['Name']}" for _, row in recommendations.iterrows()],
    index=0
)

selected_ticker = selected_etf_name.split(' - ')[0]
selected_etf = recommendations[recommendations['Ticker'] == selected_ticker].iloc[0]

# 선택된 ETF 정보 표시
st.markdown(f"### {selected_etf['Name']} 상세 정보")
st.markdown(f"**카테고리**: {selected_etf['Category']} | **시장**: {selected_etf['Market']}")

# 기본 지표
basic_metrics = [
    {
        "label": "1년 수익률",
        "value": f"{selected_etf['Return_1Y']:.1f}%",
        "help": "최근 1년간의 투자 수익률입니다. 과거 성과가 미래 수익을 보장하지는 않습니다."
    },
    {
        "label": "변동성",
        "value": f"{selected_etf['Volatility']:.1f}%",
        "help": "가격 변동의 정도를 나타냅니다. 높을수록 위험하지만 수익 기회도 클 수 있습니다."
    },
    {
        "label": "샤프 비율",
        "value": f"{selected_etf['Sharpe_Ratio']:.2f}",
        "help": "위험 대비 수익률 지표입니다. 1.0 이상이면 우수한 성과를 의미합니다."
    },
    {
        "label": "최대 낙폭",
        "value": f"{selected_etf['Max_Drawdown']:.1f}%",
        "help": "과거 최고점 대비 최대 하락폭입니다. 투자 시 감내해야 할 최대 손실을 의미합니다."
    }
]

display_large_metric_row(basic_metrics)

# 고급 지표
advanced_metrics = [
    {
        "label": "소르티노 비율",
        "value": f"{selected_etf['Sortino_Ratio']:.2f}",
        "help": "하방 위험만을 고려한 위험 조정 수익률입니다. 샤프 비율보다 정확한 위험 측정이 가능합니다."
    },
    {
        "label": "칼마 비율",
        "value": f"{selected_etf['Calmar_Ratio']:.2f}",
        "help": "연간 수익률을 최대 낙폭으로 나눈 비율입니다. 높을수록 안정적인 수익 창출 능력을 의미합니다."
    },
    {
        "label": "오메가 비율",
        "value": f"{selected_etf['Omega_Ratio']:.2f}",
        "help": "목표 수익률 이상의 수익과 이하의 손실 비율입니다. 1.0 이상이면 양호한 성과입니다."
    },
    {
        "label": "추천 점수",
        "value": f"{selected_etf['Recommendation_Score']:.3f}",
        "help": "AI가 계산한 종합 추천 점수입니다. 높을수록 귀하의 투자 성향에 적합합니다."
    }
]

st.markdown("#### 고급 위험 지표")
display_large_metric_row(advanced_metrics)

# 위험-수익 매트릭스
st.subheader("위험-수익 매트릭스")

fig_matrix = px.scatter(
    recommendations,
    x='Volatility',
    y='Return_1Y',
    size='AUM',
    color='Category',
    hover_name='Name',
    hover_data=['Sharpe_Ratio', 'Max_Drawdown', 'Recommendation_Score'],
    title='추천 ETF들의 위험-수익 분포',
    labels={
        'Volatility': '변동성 (%)',
        'Return_1Y': '1년 수익률 (%)',
        'AUM': '자산규모'
    }
)

# 선택된 ETF 강조
fig_matrix.add_scatter(
    x=[selected_etf['Volatility']],
    y=[selected_etf['Return_1Y']],
    mode='markers',
    marker=dict(size=20, color='red', symbol='star'),
    name=f'선택된 ETF: {selected_etf["Name"]}',
    showlegend=True
)

fig_matrix.update_layout(height=600)
st.plotly_chart(fig_matrix, use_container_width=True)

# 성과 지표 비교
st.subheader("성과 지표 상세 비교")

col1, col2 = st.columns(2)

with col1:
    # 위험 조정 수익률 지표
    risk_metrics = ['Sharpe_Ratio', 'Sortino_Ratio', 'Calmar_Ratio', 'Omega_Ratio']
    risk_values = [selected_etf[metric] for metric in risk_metrics]
    risk_labels = ['샤프 비율', '소르티노 비율', '칼마 비율', '오메가 비율']
    
    fig_risk = go.Figure(data=[
        go.Bar(x=risk_labels, y=risk_values, 
               marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
    ])
    fig_risk.update_layout(
        title='위험 조정 수익률 지표',
        yaxis_title='비율',
        height=400
    )
    st.plotly_chart(fig_risk, use_container_width=True)

with col2:
    # 수익률 및 위험 지표
    perf_metrics = ['Return_1Y', 'Volatility', 'Max_Drawdown']
    perf_values = [selected_etf['Return_1Y'], selected_etf['Volatility'], abs(selected_etf['Max_Drawdown'])]
    perf_labels = ['1년 수익률', '변동성', '최대 낙폭']
    
    fig_perf = go.Figure(data=[
        go.Bar(x=perf_labels, y=perf_values,
               marker_color=['#2ca02c', '#ff7f0e', '#d62728'])
    ])
    fig_perf.update_layout(
        title='수익률 및 위험 지표 (%)',
        yaxis_title='퍼센트 (%)',
        height=400
    )
    st.plotly_chart(fig_perf, use_container_width=True)

# 추천 ETF 전체 비교
st.subheader("추천 ETF 전체 성과 비교")

# 다중 지표 비교 차트
metrics_to_compare = ['Return_1Y', 'Volatility', 'Sharpe_Ratio', 'Max_Drawdown']
metric_names = ['1년 수익률 (%)', '변동성 (%)', '샤프 비율', '최대 낙폭 (%)']

fig_compare = make_subplots(
    rows=2, cols=2,
    subplot_titles=metric_names,
    specs=[[{"secondary_y": False}, {"secondary_y": False}],
           [{"secondary_y": False}, {"secondary_y": False}]]
)

colors = px.colors.qualitative.Set3

for i, (metric, name) in enumerate(zip(metrics_to_compare, metric_names)):
    row = (i // 2) + 1
    col = (i % 2) + 1
    
    values = recommendations[metric].tolist()
    if metric == 'Max_Drawdown':
        values = [abs(v) for v in values]
    
    fig_compare.add_trace(
        go.Bar(
            x=recommendations['Name'],
            y=values,
            name=name,
            marker_color=colors[i % len(colors)],
            showlegend=False
        ),
        row=row, col=col
    )

fig_compare.update_layout(height=800, title_text="추천 ETF 주요 지표 비교")
fig_compare.update_xaxes(tickangle=45)
st.plotly_chart(fig_compare, use_container_width=True)

# 상관관계 분석
if hasattr(recommender, 'returns_df') and recommender.returns_df is not None:
    st.subheader("ETF 간 상관관계 분석")
    
    recommended_tickers = recommendations['Ticker'].tolist()
    available_tickers = [t for t in recommended_tickers if t in recommender.returns_df.columns]
    
    if len(available_tickers) >= 2:
        correlation_matrix = recommender.returns_df[available_tickers].corr()
        
        fig_corr = px.imshow(
            correlation_matrix,
            text_auto=True,
            aspect="auto",
            title="추천 ETF 간 상관관계 매트릭스",
            color_continuous_scale="RdBu_r",
            zmin=-1, zmax=1
        )
        fig_corr.update_layout(height=600)
        st.plotly_chart(fig_corr, use_container_width=True)
        
        st.info("""
        **상관관계 해석:**
        - **1에 가까울수록**: 두 ETF가 같은 방향으로 움직임 (높은 상관관계)
        - **0에 가까울수록**: 두 ETF가 독립적으로 움직임 (낮은 상관관계)
        - **-1에 가까울수록**: 두 ETF가 반대 방향으로 움직임 (음의 상관관계)
        
        **포트폴리오 구성 시**: 상관관계가 낮은 ETF들을 조합하면 분산 효과를 얻을 수 있습니다.
        """)

# AI 인사이트
st.subheader("AI 분석 인사이트")

def generate_etf_insight(etf_data):
    insights = []
    
    if etf_data['Return_1Y'] > 15:
        insights.append("**높은 수익률**: 지난 1년간 우수한 성과를 보였습니다.")
    elif etf_data['Return_1Y'] < 0:
        insights.append("**마이너스 수익률**: 지난 1년간 손실이 발생했습니다.")
    else:
        insights.append("**안정적 수익률**: 지난 1년간 양호한 성과를 보였습니다.")
    
    if etf_data['Volatility'] > 25:
        insights.append("**높은 변동성**: 가격 변동이 큰 고위험 자산입니다.")
    elif etf_data['Volatility'] < 10:
        insights.append("**낮은 변동성**: 상대적으로 안정적인 자산입니다.")
    else:
        insights.append("**중간 변동성**: 적절한 수준의 위험을 가지고 있습니다.")
    
    if etf_data['Sharpe_Ratio'] > 1.5:
        insights.append("**우수한 샤프 비율**: 위험 대비 수익률이 매우 좋습니다.")
    elif etf_data['Sharpe_Ratio'] < 0.5:
        insights.append("**낮은 샤프 비율**: 위험 대비 수익률이 아쉽습니다.")
    else:
        insights.append("**양호한 샤프 비율**: 위험 대비 적절한 수익률을 제공합니다.")
    
    if abs(etf_data['Max_Drawdown']) > 30:
        insights.append("**큰 최대 낙폭**: 과거 큰 손실을 경험한 적이 있습니다.")
    elif abs(etf_data['Max_Drawdown']) < 10:
        insights.append("**작은 최대 낙폭**: 상대적으로 안정적인 가격 움직임을 보였습니다.")
    
    return insights

insights = generate_etf_insight(selected_etf)

for insight in insights:
    st.write(f"• {insight}")

# 투자 제안
st.subheader("투자 제안")

user_profile = st.session_state.user_profile
risk_tolerance = user_profile['risk_tolerance']

if risk_tolerance <= 2 and selected_etf['Volatility'] > 20:
    st.warning("**주의**: 선택하신 ETF는 보수적인 투자 성향에 비해 변동성이 높습니다. 신중한 검토가 필요합니다.")
elif risk_tolerance >= 4 and selected_etf['Volatility'] < 10:
    st.info("**제안**: 적극적인 투자 성향에 비해 안정적인 ETF입니다. 더 높은 수익을 원한다면 다른 옵션도 고려해보세요.")
else:
    st.success("**적합**: 선택하신 ETF는 귀하의 투자 성향과 잘 맞습니다.")

# 다음 단계
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("추천 결과로 돌아가기", use_container_width=True):
        st.switch_page("pages/2_추천결과.py")

with col2:
    if st.button("포트폴리오 구성하기", use_container_width=True):
        st.switch_page("pages/4_포트폴리오.py")

with col3:
    if st.button("설문 다시하기", use_container_width=True):
        for key in ['user_profile', 'recommendations', 'recommender']:
            if key in st.session_state:
                del st.session_state[key]
        st.switch_page("pages/1_투자성향설문.py")

