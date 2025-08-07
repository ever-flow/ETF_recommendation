# ETF 추천 시스템 유틸리티 모듈
# 기존 v3_ETF_추천시스템.py의 핵심 기능을 모듈화

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import RobustScaler
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class ETFRecommender:
    def __init__(self):
        self.user_etf_pref_df = None
        self.etf_data = None
        self.metrics_df = None
        
    @st.cache_data
    def load_user_preferences(_self, file_path='data/user_etf_preferences.xlsx'):
        """사용자 선호도 데이터 로드"""
        try:
            df = pd.read_excel(file_path)
            return df
        except Exception as e:
            st.error(f"데이터 로드 실패: {e}")
            return pd.DataFrame()
    
    def derive_user_quantitative_indicators(self, user_profile):
        """사용자 프로필을 정량적 지표로 변환"""
        risk_score = (user_profile['risk_tolerance'] + (6 - user_profile['loss_aversion'])) / 2.0
        
        expected_return_map = {1: 0.02, 2: 0.05, 3: 0.08, 4: 0.12, 5: 0.15}
        expected_return = expected_return_map.get(user_profile['goal'], 0.08)
        
        market_preference_scores = {
            1: {'KR': 1.0, 'US': 0.0}, 
            2: {'KR': 0.0, 'US': 1.0}, 
            3: {'KR': 0.5, 'US': 0.5}
        }
        market_scores = market_preference_scores.get(user_profile['market_preference'], {'KR': 0.5, 'US': 0.5})
        
        return {
            'risk_score': risk_score,
            'expected_return': expected_return,
            'market_scores': market_scores,
            'user_theme_preference_code': user_profile['theme_preference']
        }
    
    def collaborative_filtering_recommendation(self, user_profile, top_n_similar_users=5):
        """협업 필터링 기반 추천"""
        if self.user_etf_pref_df is None or self.user_etf_pref_df.empty:
            return []
        
        user_vector = np.array([
            user_profile[k] for k in ['risk_tolerance', 'investment_horizon', 'goal', 'experience', 'loss_aversion', 'theme_preference']
        ]).reshape(1, -1)
        
        other_users_vectors = self.user_etf_pref_df[
            ['risk_tolerance', 'investment_horizon', 'goal', 'experience', 'loss_aversion', 'theme_preference']
        ].values
        
        if other_users_vectors.shape[0] == 0:
            return []
        
        similarities = cosine_similarity(user_vector, other_users_vectors).flatten()
        num_users = min(top_n_similar_users, len(similarities))
        similar_user_indices = np.argsort(similarities)[-num_users:][::-1]
        
        cf_recommended_etfs = {}
        for idx in similar_user_indices:
            similarity = similarities[idx]
            etf_list = self.user_etf_pref_df.iloc[idx]['preferred_etfs']
            
            if pd.isna(etf_list) or not isinstance(etf_list, str):
                continue
                
            for tk in [etf.strip() for etf in etf_list.split(',')]:
                if tk:
                    cf_recommended_etfs[tk] = cf_recommended_etfs.get(tk, 0) + similarity
        
        return sorted(cf_recommended_etfs.items(), key=lambda x: x[1], reverse=True)
    
    def generate_mock_etf_data(self):
        """모의 ETF 데이터 생성 (실제 API 연결 대신)"""
        # 한국 ETF
        kr_etfs = {
            '069500': {'name': 'KODEX 200', 'category': '국내주식', 'annual_return': 0.08, 'volatility': 0.18, 'market': 'KR'},
            '133690': {'name': 'TIGER 미국나스닥100', 'category': '해외주식', 'annual_return': 0.12, 'volatility': 0.22, 'market': 'KR'},
            '232080': {'name': 'TIGER 미국S&P500', 'category': '해외주식', 'annual_return': 0.10, 'volatility': 0.16, 'market': 'KR'},
            '371460': {'name': 'TIGER 차이나전기차SOLACTIVE', 'category': '테마', 'annual_return': 0.15, 'volatility': 0.28, 'market': 'KR'},
            '277630': {'name': 'KBSTAR 미국S&P500', 'category': '해외주식', 'annual_return': 0.09, 'volatility': 0.17, 'market': 'KR'},
            '305720': {'name': 'KODEX 2차전지산업', 'category': '테마', 'annual_return': 0.18, 'volatility': 0.32, 'market': 'KR'},
        }
        
        # 미국 ETF
        us_etfs = {
            'SPY': {'name': 'SPDR S&P 500 ETF', 'category': '대형주', 'annual_return': 0.10, 'volatility': 0.16, 'market': 'US'},
            'QQQ': {'name': 'Invesco QQQ Trust', 'category': '기술주', 'annual_return': 0.13, 'volatility': 0.23, 'market': 'US'},
            'VOO': {'name': 'Vanguard S&P 500 ETF', 'category': '대형주', 'annual_return': 0.10, 'volatility': 0.16, 'market': 'US'},
            'VTI': {'name': 'Vanguard Total Stock Market', 'category': '전체시장', 'annual_return': 0.09, 'volatility': 0.17, 'market': 'US'},
            'ARKK': {'name': 'ARK Innovation ETF', 'category': '혁신기술', 'annual_return': 0.20, 'volatility': 0.35, 'market': 'US'},
            'XLV': {'name': 'Health Care Select Sector', 'category': '헬스케어', 'annual_return': 0.11, 'volatility': 0.15, 'market': 'US'},
            'XLK': {'name': 'Technology Select Sector', 'category': '기술', 'annual_return': 0.14, 'volatility': 0.21, 'market': 'US'},
            'SOXX': {'name': 'iShares Semiconductor ETF', 'category': '반도체', 'annual_return': 0.16, 'volatility': 0.26, 'market': 'US'},
            'ICLN': {'name': 'iShares Global Clean Energy', 'category': '청정에너지', 'annual_return': 0.12, 'volatility': 0.24, 'market': 'US'},
            'TAN': {'name': 'Invesco Solar ETF', 'category': '태양광', 'annual_return': 0.14, 'volatility': 0.28, 'market': 'US'},
        }
        
        all_etfs = {**kr_etfs, **us_etfs}
        
        # 추가 지표 계산
        for ticker, info in all_etfs.items():
            info['sharpe_ratio'] = (info['annual_return'] - 0.03) / info['volatility']
            info['max_drawdown'] = -np.random.uniform(0.1, 0.4)
            info['sortino_ratio'] = info['sharpe_ratio'] * 1.2
            info['calmar_ratio'] = info['annual_return'] / abs(info['max_drawdown'])
            
        return all_etfs
    
    def content_based_recommendation(self, user_profile, etf_data, top_n=10):
        """콘텐츠 기반 필터링 추천"""
        user_indicators = self.derive_user_quantitative_indicators(user_profile)
        
        scores = {}
        for ticker, info in etf_data.items():
            score = 0
            
            # 위험-수익 매칭
            expected_return = user_indicators['expected_return']
            risk_tolerance = user_indicators['risk_score'] / 5.0
            
            # 수익률 점수
            return_diff = abs(info['annual_return'] - expected_return)
            return_score = max(0, 1 - return_diff / 0.1)
            
            # 위험도 점수
            normalized_volatility = info['volatility'] / 0.4  # 정규화
            risk_score = 1 - abs(normalized_volatility - risk_tolerance)
            
            # 시장 선호도 점수
            market_score = user_indicators['market_scores'].get(info['market'], 0.5)
            
            # 테마 선호도 점수
            theme_score = 1.0
            if user_indicators['user_theme_preference_code'] == 2 and '기술' in info['category']:
                theme_score = 1.2
            elif user_indicators['user_theme_preference_code'] == 3 and '에너지' in info['category']:
                theme_score = 1.2
            elif user_indicators['user_theme_preference_code'] == 4 and '헬스케어' in info['category']:
                theme_score = 1.2
            
            # 최종 점수 계산
            final_score = (return_score * 0.3 + risk_score * 0.3 + market_score * 0.2 + 
                          info['sharpe_ratio'] * 0.1 + theme_score * 0.1)
            
            scores[ticker] = final_score
        
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    def hybrid_recommendation(self, user_profile, top_n=7):
        """하이브리드 추천 (협업 필터링 + 콘텐츠 기반)"""
        # 데이터 로드
        self.user_etf_pref_df = self.load_user_preferences()
        etf_data = self.generate_mock_etf_data()
        
        # 협업 필터링 추천
        cf_recommendations = self.collaborative_filtering_recommendation(user_profile)
        cf_dict = dict(cf_recommendations[:20])  # 상위 20개
        
        # 콘텐츠 기반 추천
        cb_recommendations = self.content_based_recommendation(user_profile, etf_data)
        cb_dict = dict(cb_recommendations)
        
        # 하이브리드 점수 계산
        all_tickers = set(cf_dict.keys()) | set(cb_dict.keys())
        hybrid_scores = {}
        
        for ticker in all_tickers:
            cf_score = cf_dict.get(ticker, 0)
            cb_score = cb_dict.get(ticker, 0)
            
            # 가중 평균 (협업 필터링 40%, 콘텐츠 기반 60%)
            hybrid_score = cf_score * 0.4 + cb_score * 0.6
            hybrid_scores[ticker] = hybrid_score
        
        # 상위 N개 선택
        final_recommendations = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        # ETF 정보와 함께 반환
        result = []
        for ticker, score in final_recommendations:
            if ticker in etf_data:
                etf_info = etf_data[ticker].copy()
                etf_info['ticker'] = ticker
                etf_info['recommendation_score'] = score
                result.append(etf_info)
        
        return result
    
    def generate_performance_chart(self, etf_list, days=252):
        """성과 차트 생성 (모의 데이터)"""
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        
        fig = go.Figure()
        
        for etf in etf_list:
            ticker = etf['ticker']
            annual_return = etf['annual_return']
            volatility = etf['volatility']
            
            # 모의 가격 데이터 생성
            daily_return = annual_return / 252
            daily_vol = volatility / np.sqrt(252)
            
            returns = np.random.normal(daily_return, daily_vol, days)
            prices = 100 * np.cumprod(1 + returns)
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=prices,
                mode='lines',
                name=f"{ticker} ({etf['name']})",
                line=dict(width=2)
            ))
        
        # 벤치마크 (S&P 500) 추가
        benchmark_returns = np.random.normal(0.10/252, 0.16/np.sqrt(252), days)
        benchmark_prices = 100 * np.cumprod(1 + benchmark_returns)
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=benchmark_prices,
            mode='lines',
            name='S&P 500 (벤치마크)',
            line=dict(width=2, dash='dash', color='gray')
        ))
        
        fig.update_layout(
            title='ETF 성과 비교 (1년)',
            xaxis_title='날짜',
            yaxis_title='누적 수익률 (%)',
            hovermode='x unified',
            height=500
        )
        
        return fig
    
    def create_risk_return_scatter(self, etf_list):
        """위험-수익률 산점도 생성"""
        tickers = [etf['ticker'] for etf in etf_list]
        names = [etf['name'] for etf in etf_list]
        returns = [etf['annual_return'] * 100 for etf in etf_list]
        volatilities = [etf['volatility'] * 100 for etf in etf_list]
        categories = [etf['category'] for etf in etf_list]
        
        fig = px.scatter(
            x=volatilities,
            y=returns,
            text=tickers,
            color=categories,
            size=[abs(etf['max_drawdown']) * 100 for etf in etf_list],
            hover_data={'이름': names, '샤프비율': [f"{etf['sharpe_ratio']:.2f}" for etf in etf_list]},
            title='ETF 위험-수익률 분석',
            labels={'x': '변동성 (%)', 'y': '연간 수익률 (%)'}
        )
        
        fig.update_traces(textposition="top center")
        fig.update_layout(height=500)
        
        return fig

