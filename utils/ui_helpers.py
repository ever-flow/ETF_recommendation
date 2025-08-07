import streamlit as st

def display_metric_with_help(label, value, help_text, delta=None, delta_color="normal"):
    """
    큰 숫자와 도움말 버튼이 있는 메트릭 표시
    
    Args:
        label: 메트릭 라벨
        value: 표시할 값
        help_text: 도움말 텍스트
        delta: 변화량 (선택사항)
        delta_color: 변화량 색상 (normal, inverse)
    """
    col1, col2 = st.columns([4, 1])
    
    with col1:
        if delta is not None:
            st.metric(label=label, value=value, delta=delta, delta_color=delta_color)
        else:
            st.metric(label=label, value=value)
    
    with col2:
        st.markdown(f"""
        <div style="margin-top: 10px;">
            <span title="{help_text}" style="
                cursor: help;
                background-color: #f0f2f6;
                border-radius: 50%;
                width: 20px;
                height: 20px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                color: #666;
                border: 1px solid #ddd;
            ">❓</span>
        </div>
        """, unsafe_allow_html=True)

def display_large_metric_row(metrics_data):
    """
    여러 메트릭을 한 행에 표시
    
    Args:
        metrics_data: 메트릭 데이터 리스트
        [{"label": "라벨", "value": "값", "help": "도움말"}, ...]
    """
    cols = st.columns(len(metrics_data))
    
    for i, metric in enumerate(metrics_data):
        with cols[i]:
            display_metric_with_help(
                label=metric["label"],
                value=metric["value"],
                help_text=metric["help"],
                delta=metric.get("delta"),
                delta_color=metric.get("delta_color", "normal")
            )

def create_help_tooltip(text, help_text):
    """
    텍스트 옆에 도움말 아이콘 생성
    
    Args:
        text: 표시할 텍스트
        help_text: 도움말 내용
    
    Returns:
        HTML 문자열
    """
    return f"""
    <div style="display: inline-flex; align-items: center; gap: 5px;">
        <span>{text}</span>
        <span title="{help_text}" style="
            cursor: help;
            background-color: #f0f2f6;
            border-radius: 50%;
            width: 16px;
            height: 16px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            color: #666;
            border: 1px solid #ddd;
        ">❓</span>
    </div>
    """

def display_etf_card_with_help(etf_data, rank=None):
    """
    ETF 카드를 도움말과 함께 표시
    
    Args:
        etf_data: ETF 데이터 딕셔너리
        rank: 순위 (선택사항)
    """
    # 카드 헤더
    if rank:
        st.markdown(f"### #{rank} {etf_data['ticker']} ETF")
    else:
        st.markdown(f"### {etf_data['ticker']} ETF")
    
    st.markdown(f"**{etf_data.get('name', 'ETF 이름')}**")
    st.markdown(f"카테고리: {etf_data.get('category', 'N/A')} | 시장: {etf_data.get('market', 'N/A')}")
    
    if 'recommendation_score' in etf_data:
        st.markdown(f"**추천 점수: {etf_data['recommendation_score']:.3f}**")
    
    # 메트릭 데이터 준비
    metrics = []
    
    if 'annual_return' in etf_data:
        metrics.append({
            "label": "1년 수익률",
            "value": f"{etf_data['annual_return']:.1f}%",
            "help": "최근 1년간의 연간 수익률입니다. 과거 성과가 미래 수익을 보장하지는 않습니다."
        })
    
    if 'volatility' in etf_data:
        metrics.append({
            "label": "변동성",
            "value": f"{etf_data['volatility']:.1f}%",
            "help": "가격 변동의 정도를 나타냅니다. 높을수록 위험하지만 수익 기회도 클 수 있습니다."
        })
    
    if 'sharpe_ratio' in etf_data:
        metrics.append({
            "label": "샤프 비율",
            "value": f"{etf_data['sharpe_ratio']:.2f}",
            "help": "위험 대비 수익률을 나타내는 지표입니다. 1.0 이상이면 우수한 성과로 평가됩니다."
        })
    
    # 첫 번째 행 메트릭 표시
    if len(metrics) >= 3:
        display_large_metric_row(metrics[:3])
        remaining_metrics = metrics[3:]
    else:
        display_large_metric_row(metrics)
        remaining_metrics = []
    
    # 두 번째 행 메트릭 준비
    second_row_metrics = []
    
    if 'max_drawdown' in etf_data:
        second_row_metrics.append({
            "label": "최대 낙폭",
            "value": f"{etf_data['max_drawdown']:.1f}%",
            "help": "과거 최고점 대비 최대 하락폭입니다. 투자 시 감수해야 할 최대 손실 가능성을 나타냅니다."
        })
    
    if 'aum' in etf_data:
        second_row_metrics.append({
            "label": "자산규모",
            "value": etf_data['aum'],
            "help": "ETF가 운용하는 총 자산 규모입니다. 클수록 안정적이고 유동성이 좋습니다."
        })
    
    if 'expense_ratio' in etf_data:
        second_row_metrics.append({
            "label": "비용비율",
            "value": f"{etf_data['expense_ratio']:.2f}%",
            "help": "연간 운용 수수료입니다. 낮을수록 투자자에게 유리합니다."
        })
    
    # 두 번째 행 메트릭 표시
    if second_row_metrics:
        display_large_metric_row(second_row_metrics)

def display_advanced_metrics_with_help(etf_data):
    """
    고급 지표들을 도움말과 함께 표시
    
    Args:
        etf_data: ETF 데이터 딕셔너리
    """
    advanced_metrics = []
    
    if 'sortino_ratio' in etf_data:
        advanced_metrics.append({
            "label": "소르티노 비율",
            "value": f"{etf_data['sortino_ratio']:.2f}",
            "help": "하방 위험만을 고려한 위험 조정 수익률입니다. 샤프 비율보다 정확한 위험 측정이 가능합니다."
        })
    
    if 'calmar_ratio' in etf_data:
        advanced_metrics.append({
            "label": "칼마 비율",
            "value": f"{etf_data['calmar_ratio']:.2f}",
            "help": "연간 수익률을 최대 낙폭으로 나눈 비율입니다. 높을수록 안정적인 수익 창출 능력을 의미합니다."
        })
    
    if 'omega_ratio' in etf_data:
        advanced_metrics.append({
            "label": "오메가 비율",
            "value": f"{etf_data['omega_ratio']:.2f}",
            "help": "목표 수익률 이상의 수익과 이하의 손실 비율입니다. 1.0 이상이면 양호한 성과입니다."
        })
    
    if advanced_metrics:
        st.markdown("#### 고급 위험 지표")
        display_large_metric_row(advanced_metrics)

def display_correlation_with_help(correlation_value, etf1_name, etf2_name):
    """
    상관관계를 도움말과 함께 표시
    
    Args:
        correlation_value: 상관관계 값
        etf1_name: 첫 번째 ETF 이름
        etf2_name: 두 번째 ETF 이름
    """
    # 상관관계 해석
    if abs(correlation_value) <= 0.1:
        interpretation = "매우 낮음 (거의 독립적)"
        color = "green"
    elif abs(correlation_value) <= 0.3:
        interpretation = "낮음 (분산 효과 우수)"
        color = "lightgreen"
    elif abs(correlation_value) <= 0.5:
        interpretation = "보통 (어느 정도 분산 효과)"
        color = "orange"
    elif abs(correlation_value) <= 0.7:
        interpretation = "높음 (분산 효과 제한적)"
        color = "red"
    else:
        interpretation = "매우 높음 (분산 효과 거의 없음)"
        color = "darkred"
    
    display_metric_with_help(
        label=f"{etf1_name} ↔ {etf2_name} 상관관계",
        value=f"{correlation_value:.3f}",
        help_text=f"두 ETF 간의 상관관계입니다. -1에서 1 사이의 값으로, 0에 가까울수록 분산 투자 효과가 큽니다. 현재 수준: {interpretation}"
    )
    
    st.markdown(f"<span style='color: {color}; font-weight: bold;'>해석: {interpretation}</span>", 
                unsafe_allow_html=True)

