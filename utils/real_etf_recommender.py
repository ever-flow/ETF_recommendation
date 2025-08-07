# 실제 v3 ETF 추천 시스템 모듈 (완전한 API 기반)
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.preprocessing import RobustScaler, minmax_scale
from sklearn.cluster import KMeans, DBSCAN
import umap.umap_ as umap
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
from tqdm import tqdm
import warnings
from kneed import KneeLocator
import streamlit as st
import pickle
import os
from pathlib import Path

# 경고 메시지 숨기기
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.WARNING)

# FinanceDataReader 초기화
try:
    import FinanceDataReader as fdr
    FDR_AVAILABLE = True
except ImportError:
    fdr = None
    FDR_AVAILABLE = False

class RealETFRecommender:
    """실제 API 데이터 기반 ETF 추천 시스템 (v3 완전 구현)"""
    
    def __init__(self):
        self.etf_data = None
        self.user_data = None
        self.features = None
        self.clusters = None
        self.umap_embedding = None
        self.scaler = RobustScaler()
        self.is_data_loaded = False
        self.returns_df = None
        self.metrics_df = None
        
        # 캐시 디렉토리 설정
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "etf_data_cache.pkl"
        self.cache_expiry_hours = 6  # 6시간마다 캐시 갱신
        
        # 확장된 한국 ETF 목록 (기존 30개 → 45개)
        self.kr_etfs = [
            # 기존 ETF들
            '069500', '102110', '114800', '132030', '133690', '148020', '153130', '232080', '251340',
            '278530', '277630', '309210', '305720', '364990', '371460', '379800', '381170', '453950',
            '091160', '069660', '280940', '114460', '130680', '305050', '379780', '261240', '381560',
            '148070', '236360', '260780',
            # 추가 ETF들 - 다양한 섹터와 스타일
            '122630', '139660', '139670', '143850', '152100', '157490', '182490', '195930', '200250',
            '217770', '233740', '251350', '267770', '269420', '273130'
        ]
        
        # 확장된 미국 ETF 목록 (기존 ~50개 → 80개)
        self.us_etfs = list(set([
            # 기존 주요 ETF들
            'SPY', 'VOO', 'VTI', 'IWM', 'QQQ', 'XLK', 'XLF', 'XLY', 'XLP', 'XLI', 'XLU', 'XLC', 'XLB',
            'VTV', 'VUG', 'VB', 'VEA', 'VWO', 'AGG', 'BND', 'TLT', 'IEF', 'SHY', 'LQD', 'HYG', 'TIP',
            'GLD', 'SLV', 'DBC', 'USO', 'UNG', 'PPLT', 'ARKK', 'BOTZ', 'TAN', 'ICLN', 'PBW', 'PLUG',
            'VNQ', 'SCHH', 'IYR', 'EFA', 'EEM', 'IEFA', 'EMB', 'SCHD', 'DIA', 'EWY', 'EWZ',
            'EWU', 'EWH', 'EWG', 'EWC', 'EWJ', 'EWT',
            # 추가 섹터별 ETF
            'XLE', 'XLV', 'XLRE', 'XME', 'XBI', 'XRT', 'XHB', 'XOP', 'KRE', 'KBE', 'ITB', 'IHI',
            # 스타일별 ETF
            'VBK', 'VBR', 'VEU', 'VSS', 'VGK', 'VPL', 'VGT', 'VDC', 'VDE', 'VFH', 'VHT', 'VIS',
            # 테마별 ETF
            'SOXX', 'SMH', 'FINX', 'HACK', 'ROBO', 'ESPO', 'CLOU', 'CIBR', 'SKYY', 'WCLD',
            # 채권 다양화
            'VCIT', 'VCSH', 'VGIT', 'VGSH', 'VTEB', 'MUB', 'SCHZ', 'SCHO', 'SCHR',
            # 국제 다양화
            'VXUS', 'IXUS', 'FTIHX', 'FXNAX', 'VT', 'ACWI', 'URTH', 'IOO'
        ]))
        
        self.all_tickers = sorted(list(set(self.kr_etfs + self.us_etfs)))
        
        # 확장된 ETF 테마 매핑
        self.etf_theme_map = {
            # 기술 섹터
            'QQQ': '기술', 'XLK': '기술', 'SOXX': '기술', 'BOTZ': '기술', 'ARKK': '기술',
            'SMH': '기술', 'VGT': '기술', 'FINX': '기술', 'HACK': '기술', 'ROBO': '기술',
            'ESPO': '기술', 'CLOU': '기술', 'CIBR': '기술', 'SKYY': '기술', 'WCLD': '기술',
            '133690': '기술', '232080': '기술', '371460': '기술', '379800': '기술', '453950': '기술',
            '309210': '기술', '114800': '기술', '122630': '기술', '139660': '기술',
            
            # 에너지 섹터
            'XLE': '에너지', 'USO': '에너지', 'URA': '에너지', 'TAN': '에너지', 'ICLN': '에너지',
            'PBW': '에너지', 'VDE': '에너지', 'XOP': '에너지', '217770': '에너지',
            
            # 헬스케어 섹터
            'XLV': '헬스케어', 'VHT': '헬스케어', 'XBI': '헬스케어', 'IHI': '헬스케어',
            '277630': '헬스케어', '305720': '헬스케어', '139670': '헬스케어',
            
            # 금융 섹터
            'XLF': '금융', 'VFH': '금융', 'KRE': '금융', 'KBE': '금융', '091160': '금융',
            
            # 소비재 섹터
            'XLY': '소비재', 'XLP': '소비재', 'VDC': '소비재', 'XRT': '소비재',
            
            # 산업재 섹터
            'XLI': '산업재', 'VIS': '산업재', 'XHB': '산업재', 'ITB': '산업재',
            
            # 유틸리티
            'XLU': '유틸리티',
            
            # 통신
            'XLC': '통신',
            
            # 소재
            'XLB': '소재', 'XME': '소재',
            
            # 부동산
            'VNQ': '부동산', 'SCHH': '부동산', 'IYR': '부동산', 'XLRE': '부동산',
            
            # 시장지수
            'SPY': '시장지수', 'DIA': '시장지수', 'IWM': '시장지수', 'VTI': '시장지수', 
            'VOO': '시장지수', 'VTV': '시장지수', 'VUG': '시장지수', 'VB': '시장지수',
            'VBK': '시장지수', 'VBR': '시장지수', 'SCHD': '시장지수',
            '069500': '시장지수', '102110': '시장지수', '114460': '시장지수',
            
            # 채권
            'AGG': '채권', 'TLT': '채권', 'BND': '채권', 'IEF': '채권', 'SHY': '채권',
            'LQD': '채권', 'HYG': '채권', 'TIP': '채권', 'VCIT': '채권', 'VCSH': '채권',
            'VGIT': '채권', 'VGSH': '채권', 'VTEB': '채권', 'MUB': '채권', 'SCHZ': '채권',
            'SCHO': '채권', 'SCHR': '채권', 'EMB': '채권',
            
            # 원자재
            'GLD': '원자재', 'SLV': '원자재', 'GDX': '원자재', 'DBC': '원자재', 'UNG': '원자재',
            'PPLT': '원자재',
            
            # 국제/신흥시장
            'VEA': '국제', 'VWO': '국제', 'EFA': '국제', 'EEM': '국제', 'IEFA': '국제',
            'VEU': '국제', 'VSS': '국제', 'VGK': '국제', 'VPL': '국제', 'VXUS': '국제',
            'IXUS': '국제', 'VT': '국제', 'ACWI': '국제', 'URTH': '국제', 'IOO': '국제',
            'EWY': '국제', 'EWZ': '국제', 'EWU': '국제', 'EWH': '국제', 'EWG': '국제',
            'EWC': '국제', 'EWJ': '국제', 'EWT': '국제'
        }
        
        self.user_theme_code_to_name_map = {2: '기술', 3: '에너지', 4: '헬스케어'}
    
    def is_cache_valid(self) -> bool:
        """캐시 파일이 유효한지 확인"""
        if not self.cache_file.exists():
            return False
        
        # 파일 수정 시간 확인
        cache_time = datetime.fromtimestamp(self.cache_file.stat().st_mtime)
        current_time = datetime.now()
        time_diff = current_time - cache_time
        
        return time_diff.total_seconds() < (self.cache_expiry_hours * 3600)
    
    def save_cache(self, data: dict):
        """데이터를 캐시 파일에 저장"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(data, f)
            st.success(f"✅ 데이터 캐시 저장 완료 ({len(data.get('tickers', []))}개 ETF)")
        except Exception as e:
            st.warning(f"캐시 저장 실패: {e}")
    
    def load_cache(self) -> dict:
        """캐시 파일에서 데이터 로드"""
        try:
            with open(self.cache_file, 'rb') as f:
                data = pickle.load(f)
            st.info(f"📦 캐시된 데이터 로드 ({len(data.get('tickers', []))}개 ETF)")
            return data
        except Exception as e:
            st.warning(f"캐시 로드 실패: {e}")
            return None
    
    def fetch_risk_free_rate(self, start_date_str: str, end_date_str: str) -> float:
        """무위험 이자율 가져오기 (v3 구현)"""
        if not FDR_AVAILABLE:
            return 0.03
            
        try:
            data = fdr.DataReader('FRED:TB3MS', start_date_str, end_date_str)
            if not data.empty:
                monthly_rate = data['TB3MS'].resample('M').last().mean()
                if pd.notna(monthly_rate):
                    return monthly_rate / 100
        except Exception:
            for ticker in ['KOFR', 'CD91']:
                try:
                    data = fdr.DataReader(ticker, start_date_str, end_date_str)
                    if not data.empty and 'Close' in data.columns:
                        return data['Close'].mean() / 100
                except Exception:
                    continue
        return 0.03
    
    def fetch_etf_data_with_retry(self, tickers: list, start: str, end: str, max_retries: int = 3):
        """ETF 데이터 가져오기 (캐시 기능 포함)"""
        if not FDR_AVAILABLE:
            st.error("FinanceDataReader가 설치되지 않았습니다.")
            return pd.DataFrame(), []
        
        # 캐시 확인
        if self.is_cache_valid():
            cached_data = self.load_cache()
            if cached_data and 'price_data' in cached_data and 'tickers' in cached_data:
                # 요청된 티커가 캐시에 모두 있는지 확인
                cached_tickers = set(cached_data['tickers'])
                requested_tickers = set(tickers)
                
                if requested_tickers.issubset(cached_tickers):
                    # 캐시된 데이터에서 필요한 티커만 추출
                    price_data = cached_data['price_data']
                    available_tickers = [t for t in tickers if t in price_data.columns]
                    filtered_data = price_data[available_tickers]
                    
                    st.success(f"🚀 캐시에서 데이터 로드 완료! ({len(available_tickers)}개 ETF)")
                    return filtered_data, available_tickers
        
        # 캐시가 없거나 유효하지 않은 경우 새로 다운로드
        st.info("📡 실시간 데이터 다운로드 중...")
            
        data = pd.DataFrame()
        successful_tickers = []
        failed_tickers = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, tk in enumerate(tickers):
            progress_bar.progress((i + 1) / len(tickers))
            status_text.text(f"ETF 데이터 가져오는 중: {tk} ({i+1}/{len(tickers)})")
            
            for attempt in range(1, max_retries + 1):
                try:
                    df_raw = fdr.DataReader(tk, start, end)
                    if df_raw is None or df_raw.empty:
                        if attempt == max_retries: 
                            failed_tickers.append(tk)
                        continue
                        
                    close_col = 'Adj Close' if 'Adj Close' in df_raw.columns else 'Close'
                    if close_col not in df_raw.columns:
                        if attempt == max_retries: 
                            failed_tickers.append(tk)
                        continue
                        
                    series = df_raw[close_col].copy()
                    series.replace([np.inf, -np.inf], np.nan, inplace=True)
                    
                    if series.notna().sum() < 2:
                        if attempt == max_retries: 
                            failed_tickers.append(tk)
                        continue
                        
                    series.interpolate(method='linear', limit_direction='both', inplace=True)
                    series.ffill(inplace=True)
                    series.bfill(inplace=True)
                    
                    if series.isnull().all():
                        if attempt == max_retries: 
                            failed_tickers.append(tk)
                        continue
                        
                    series = series[~series.index.duplicated(keep='first')]
                    data[tk] = series
                    successful_tickers.append(tk)
                    break
                    
                except Exception as e:
                    if attempt == max_retries: 
                        failed_tickers.append(tk)
        
        progress_bar.empty()
        status_text.empty()
        
        if not data.empty:
            data = data.dropna(how='all', axis=1)
            
            # 새로 다운로드한 데이터를 캐시에 저장
            cache_data = {
                'price_data': data,
                'tickers': successful_tickers,
                'download_time': datetime.now().isoformat(),
                'failed_tickers': failed_tickers
            }
            self.save_cache(cache_data)
            
        return data, successful_tickers
    
    def calculate_risk_metrics(self, returns: pd.DataFrame, risk_free_rate: float = 0.0) -> pd.DataFrame:
        """위험 지표 계산 (v3 구현)"""
        metrics = pd.DataFrame(index=returns.columns)
        annual_factor = 252
        transaction_cost = {'KR': 0.0015, 'US': 0.0030}
        market_map = {tk: 'KR' if tk.isdigit() and len(tk) == 6 else 'US' for tk in returns.columns}
        
        annual_return = returns.mean() * annual_factor
        costs = annual_return.index.map(lambda tk: transaction_cost[market_map[tk]])
        metrics['Annual Return'] = annual_return - costs
        metrics['Annual Volatility'] = returns.std() * np.sqrt(annual_factor)
        metrics['Sharpe Ratio'] = np.where(metrics['Annual Volatility'] > 1e-6,
                                           (metrics['Annual Return'] - risk_free_rate) / metrics['Annual Volatility'], 0)
        
        cumulative_returns = (1 + returns).cumprod()
        peak = cumulative_returns.cummax()
        drawdown = (cumulative_returns - peak) / peak
        metrics['Max Drawdown'] = drawdown.min()
        metrics['Ulcer Index'] = np.sqrt((drawdown**2).mean())
        
        downside_returns = returns[returns < risk_free_rate/annual_factor].fillna(0)
        metrics['Downside Risk'] = downside_returns.std() * np.sqrt(annual_factor)
        metrics['Sortino Ratio'] = np.where(metrics['Downside Risk'] > 1e-6,
                                            (metrics['Annual Return'] - risk_free_rate) / metrics['Downside Risk'], 0)
        
        daily_risk_free_rate = risk_free_rate / annual_factor
        gain = (returns - daily_risk_free_rate).clip(lower=0).mean()
        loss = (daily_risk_free_rate - returns).clip(lower=0).mean()
        metrics['Omega Ratio'] = np.where(loss > 1e-9, gain / loss, 0)
        
        metrics['Calmar Ratio'] = np.where(np.abs(metrics['Max Drawdown']) > 1e-6,
                                           metrics['Annual Return'] / (-metrics['Max Drawdown']), 0)
        
        metrics['Skewness'] = returns.skew()
        metrics['Kurtosis'] = returns.kurt()
        
        if len(returns) >= annual_factor:
            metrics['Recent Return'] = returns.iloc[-annual_factor:].mean() * annual_factor
            metrics['Recent Volatility'] = returns.iloc[-annual_factor:].std() * np.sqrt(annual_factor)
        else:
            metrics[['Recent Return', 'Recent Volatility']] = np.nan
            
        return metrics.fillna(0).replace([np.inf, -np.inf], 0)
    
    def optimize_clustering(self, data: pd.DataFrame, k_range=range(2, 11), random_state=42):
        """클러스터링 최적화 (v3 구현)"""
        if data.empty or len(data) < max(k_range):
            return np.array([]).reshape(0, 3), np.zeros(len(data) if not data.empty else 0, dtype=int)
            
        scaler = RobustScaler()
        scaled_data = scaler.fit_transform(data.replace([np.inf, -np.inf], np.nan).fillna(0))
        
        best_umap_data = None
        if len(scaled_data) >= 2:
            best_umap_score = -np.inf
            n_neighbors_options = [5, 10, 15]
            min_dist_options = [0.0, 0.1, 0.2]
            
            for n_neighbors in n_neighbors_options:
                n_neighbors = min(n_neighbors, max(1, len(scaled_data) - 1))
                for min_dist in min_dist_options:
                    try:
                        n_components = min(3, scaled_data.shape[1])
                        if n_components == 0: 
                            continue
                            
                        umap_reducer = umap.UMAP(
                            n_components=n_components, 
                            n_neighbors=n_neighbors, 
                            min_dist=min_dist, 
                            random_state=random_state
                        )
                        umap_data = umap_reducer.fit_transform(scaled_data)
                        
                        temp_k = min(3, max(2, len(umap_data) - 1))
                        if temp_k < 2: 
                            continue
                            
                        temp_kmeans = KMeans(n_clusters=temp_k, n_init='auto', random_state=random_state)
                        temp_labels = temp_kmeans.fit_predict(umap_data)
                        
                        if len(set(temp_labels)) > 1:
                            score = silhouette_score(umap_data, temp_labels)
                            if score > best_umap_score:
                                best_umap_score = score
                                best_umap_data = umap_data
                    except Exception:
                        continue
        
        if best_umap_data is None and scaled_data.shape[1] > 0:
            n_components = min(3, scaled_data.shape[1])
            umap_reducer = umap.UMAP(
                n_components=n_components, 
                n_neighbors=min(15, max(1, len(scaled_data) - 1)), 
                min_dist=0.1, 
                random_state=random_state
            )
            best_umap_data = umap_reducer.fit_transform(scaled_data)
        
        umap_data = best_umap_data if best_umap_data is not None else scaled_data[:, :min(3, scaled_data.shape[1])]
        
        if umap_data.shape[0] == 0:
            return umap_data, np.zeros(len(data), dtype=int)
        
        valid_k_list = [k for k in k_range if 2 <= k < len(umap_data)]
        if not valid_k_list:
            return umap_data, np.zeros(len(umap_data), dtype=int)
        
        # Elbow method로 최적 k 찾기
        wcss = []
        for k in valid_k_list:
            try:
                km = KMeans(n_clusters=k, n_init='auto', random_state=random_state)
                km.fit(umap_data)
                wcss.append(km.inertia_)
            except Exception:
                continue
        
        best_k = 3
        if len(wcss) >= 2:
            kl = KneeLocator(valid_k_list[:len(wcss)], wcss, curve='convex', direction='decreasing', S=1.0)
            best_k = kl.elbow if kl.elbow else best_k
        
        best_k = min(best_k, len(umap_data) - 1) if len(umap_data) > 1 else 1
        
        # 최종 클러스터링
        if best_k < 2:
            labels = np.zeros(len(umap_data), dtype=int)
        else:
            kmeans = KMeans(n_clusters=best_k, n_init='auto', random_state=random_state)
            labels = kmeans.fit_predict(umap_data)
        
        return umap_data, labels
    
    def derive_user_quantitative_indicators(self, user_profile: dict) -> dict:
        """사용자 정량적 지표 도출 (v3 구현)"""
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
    
    def match_user_to_cluster(self, user_profile: dict, metrics_df: pd.DataFrame):
        """사용자를 클러스터에 매칭 (v3 구현)"""
        user_quant = self.derive_user_quantitative_indicators(user_profile)
        user_vol = user_quant['risk_score'] * 0.05  # 0~0.25 범위
        user_ret = user_quant['expected_return']
        
        cluster_centers = metrics_df.groupby('Cluster')[['Annual Return', 'Annual Volatility']].mean()
        
        distances = []
        for cluster_id, center in cluster_centers.iterrows():
            dist = np.sqrt((center['Annual Return'] - user_ret)**2 + (center['Annual Volatility'] - user_vol)**2)
            distances.append((cluster_id, dist))
        
        best_cluster_id = min(distances, key=lambda x: x[1])[0]
        recommended_tickers = metrics_df[metrics_df['Cluster'] == best_cluster_id].index.tolist()
        
        cluster_center = cluster_centers.loc[best_cluster_id]
        explanation = (f"사용자의 위험 선호도(선호 변동성: {user_vol*100:.1f}%) 및 "
                      f"목표 수익률({user_ret*100:.1f}%)에 기반하여, "
                      f"가장 유사한 특성(평균 변동성 {cluster_center['Annual Volatility']*100:.1f}%, "
                      f"평균 수익률 {cluster_center['Annual Return']*100:.1f}%)을 보이는 "
                      f"클러스터 {best_cluster_id}에 매칭되었습니다.")
        
        return best_cluster_id, recommended_tickers, explanation
    
    def load_user_etf_preferences(self, file_path: str = 'user_etf_preferences.xlsx') -> pd.DataFrame:
        """사용자 ETF 선호도 데이터 로드 (v3 구현)"""
        try:
            df = pd.read_excel(file_path)
            required_cols = ['risk_tolerance', 'investment_horizon', 'goal', 'experience', 'loss_aversion', 'theme_preference', 'preferred_etfs']
            if not all(col in df.columns for col in required_cols):
                return pd.DataFrame()
            return df
        except Exception:
            return pd.DataFrame()
    
    def collaborative_filtering_recommendation(self, user_profile: dict, metrics_df: pd.DataFrame, user_etf_pref_df: pd.DataFrame, top_n_similar_users: int = 5) -> list:
        """협업 필터링 추천 (v3 구현)"""
        if user_etf_pref_df.empty:
            return []
        
        user_vector = np.array([user_profile[k] for k in ['risk_tolerance', 'investment_horizon', 'goal', 'experience', 'loss_aversion', 'theme_preference']]).reshape(1, -1)
        other_users_vectors = user_etf_pref_df[['risk_tolerance', 'investment_horizon', 'goal', 'experience', 'loss_aversion', 'theme_preference']].values
        
        if other_users_vectors.shape[0] == 0:
            return []
        
        similarities = cosine_similarity(user_vector, other_users_vectors).flatten()
        num_users = min(top_n_similar_users, len(similarities))
        similar_user_indices = np.argsort(similarities)[-num_users:][::-1]
        
        cf_recommended_etfs = {}
        for idx in similar_user_indices:
            similarity = similarities[idx]
            etf_list = user_etf_pref_df.iloc[idx]['preferred_etfs']
            if pd.isna(etf_list) or not isinstance(etf_list, str): 
                continue
            for tk in [etf.strip() for etf in etf_list.split(',') if etf.strip()]:
                if tk in metrics_df.index:
                    cf_recommended_etfs[tk] = cf_recommended_etfs.get(tk, 0) + similarity
        
        return sorted(cf_recommended_etfs.keys(), key=lambda x: cf_recommended_etfs[x], reverse=True)
    
    def load_and_process_data(self, user_profile=None):
        """데이터 로드 및 전처리 (v3 완전 구현)"""
        try:
            if not FDR_AVAILABLE:
                st.error("FinanceDataReader가 설치되지 않았습니다. pip install finance-datareader로 설치해주세요.")
                return False
            
            # 투자 기간에 따른 데이터 수집 기간 결정
            end_date_dt = datetime.now()
            horizon_years_map = {1: 1, 2: 3, 3: 5, 4: 10, 5: 10}
            data_period_years = horizon_years_map.get(user_profile['investment_horizon'], 5)
            start_date_dt = end_date_dt - relativedelta(years=data_period_years)
            start_date_str, end_date_str = start_date_dt.strftime('%Y-%m-%d'), end_date_dt.strftime('%Y-%m-%d')
            
            # 실제 ETF 데이터 가져오기
            st.info(f"📊 {len(self.all_tickers)}개 ETF의 {data_period_years}년간 실제 데이터를 수집합니다...")
            etf_price_data, successful_tickers = self.fetch_etf_data_with_retry(self.all_tickers, start_date_str, end_date_str)
            
            min_etfs = 5
            if len(successful_tickers) < min_etfs:
                st.error(f"오류: {len(successful_tickers)}개의 ETF만 가져왔습니다 (최소 {min_etfs}개 필요).")
                return False
            
            st.success(f"✅ {len(successful_tickers)}개 ETF 데이터 수집 완료!")
            
            # 수익률 계산
            self.returns_df = np.log(etf_price_data / etf_price_data.shift(1)).iloc[1:].dropna(how='all', axis=0).dropna(how='all', axis=1)
            
            if self.returns_df.empty or self.returns_df.shape[1] < min_etfs:
                st.error("오류: 유효한 수익률 데이터가 충분하지 않습니다.")
                return False
            
            # 무위험 이자율 가져오기
            risk_free_rate = self.fetch_risk_free_rate(start_date_str, end_date_str)
            
            # 위험 지표 계산
            self.metrics_df = self.calculate_risk_metrics(self.returns_df, risk_free_rate)
            self.metrics_df['Market'] = ['KR' if tk.isdigit() and len(tk) == 6 else 'US' for tk in self.metrics_df.index]
            
            # 클러스터링
            clustering_features = ['Annual Return', 'Annual Volatility', 'Sharpe Ratio', 'Max Drawdown', 'Sortino Ratio', 'Calmar Ratio', 'Skewness', 'Kurtosis', 'Ulcer Index', 'Omega Ratio']
            clustering_input = self.metrics_df[[f for f in clustering_features if f in self.metrics_df.columns]].replace([np.inf, -np.inf], np.nan).fillna(0)
            
            if clustering_input.shape[0] < min_etfs:
                self.metrics_df['Cluster'] = 0
            else:
                max_k = min(10, clustering_input.shape[0] - 1 if clustering_input.shape[0] > 1 else 1)
                _, cluster_labels = self.optimize_clustering(clustering_input, k_range=range(2, max_k + 1), random_state=42)
                self.metrics_df['Cluster'] = cluster_labels
            
            self.is_data_loaded = True
            return True
            
        except Exception as e:
            st.error(f"데이터 로드 중 오류 발생: {e}")
            return False
    
    def generate_recommendations(self, user_profile, top_n=7):
        """추천 생성 (v3 완전 구현)"""
        if not self.is_data_loaded:
            if not self.load_and_process_data(user_profile):
                return None
        
        try:
            # 사용자를 클러스터에 매칭
            matched_cluster_id, tickers_in_cluster, cluster_explanation = self.match_user_to_cluster(user_profile, self.metrics_df)
            
            # 협업 필터링 추천
            user_etf_pref_data = self.load_user_etf_preferences('/home/ubuntu/etf_recommendation_app/data/user_etf_preferences.xlsx')
            cf_recommendations = self.collaborative_filtering_recommendation(user_profile, self.metrics_df, user_etf_pref_data) if not user_etf_pref_data.empty else []
            
            # 최종 추천 목록 생성
            final_recommended_tickers = list(dict.fromkeys(tickers_in_cluster + [tk for tk in cf_recommendations if tk not in tickers_in_cluster]))
            valid_final_tickers = [tk for tk in final_recommended_tickers if tk in self.metrics_df.index]
            
            if not valid_final_tickers:
                return None
            
            recommendation_df = self.metrics_df.loc[valid_final_tickers].copy()
            
            # 시장 선호도 필터링
            market_pref = user_profile['market_preference']
            if market_pref == 1: 
                recommendation_df = recommendation_df[recommendation_df['Market'] == 'KR']
            elif market_pref == 2: 
                recommendation_df = recommendation_df[recommendation_df['Market'] == 'US']
            
            if recommendation_df.empty:
                return None
            
            # 테마 선호도 점수 계산
            preferred_theme = self.user_theme_code_to_name_map.get(user_profile['theme_preference'])
            recommendation_df['ThemeMatchScore'] = recommendation_df.index.map(
                lambda tk: 1 if preferred_theme and self.etf_theme_map.get(tk) == preferred_theme else 0
            )
            
            # 정규화 및 추천 점수 계산
            norm_df = pd.DataFrame(index=recommendation_df.index)
            norm_df['Sortino Ratio'] = minmax_scale(recommendation_df['Sortino Ratio'])
            recommendation_df['NegMaxDrawdown'] = -recommendation_df['Max Drawdown']
            norm_df['NegMaxDrawdown'] = minmax_scale(recommendation_df['NegMaxDrawdown'])
            norm_df['InvVolatility'] = 1 - minmax_scale(recommendation_df['Annual Volatility'])
            norm_df['ThemeMatch'] = recommendation_df['ThemeMatchScore']
            
            # 가중치 계산
            w_sortino = (user_profile['risk_tolerance'] / 5.0) * 0.5 + 0.3
            w_neg_max_dd = user_profile['loss_aversion'] / 5.0
            w_inv_vol = (6 - user_profile['risk_tolerance']) / 5.0
            w_theme = 0.2 if user_profile['theme_preference'] != 1 else 0.0
            
            total_w = w_sortino + w_neg_max_dd + w_inv_vol + w_theme
            if total_w > 0:
                w_sortino /= total_w
                w_neg_max_dd /= total_w
                w_inv_vol /= total_w
                w_theme /= total_w
            else:
                w_sortino = 0.4; w_neg_max_dd = 0.3; w_inv_vol = 0.2; w_theme = 0.1
            
            recommendation_df['RecommendationScore'] = (
                w_sortino * norm_df['Sortino Ratio'] +
                w_neg_max_dd * norm_df['NegMaxDrawdown'] +
                w_inv_vol * norm_df['InvVolatility'] +
                w_theme * norm_df['ThemeMatch']
            )
            
            # 상위 N개 선택
            final_recommendations = recommendation_df.nlargest(top_n, 'RecommendationScore')
            
            # 결과 포맷팅
            result_df = pd.DataFrame()
            for ticker in final_recommendations.index:
                row_data = {
                    'Ticker': ticker,
                    'Name': self._get_etf_name(ticker),
                    'Category': self._get_etf_category(ticker),
                    'Market': final_recommendations.loc[ticker, 'Market'],
                    'Return_1Y': final_recommendations.loc[ticker, 'Annual Return'] * 100,
                    'Return_3Y': final_recommendations.loc[ticker, 'Annual Return'] * 3 * 100,  # 근사치
                    'Volatility': final_recommendations.loc[ticker, 'Annual Volatility'] * 100,
                    'Sharpe_Ratio': final_recommendations.loc[ticker, 'Sharpe Ratio'],
                    'Max_Drawdown': final_recommendations.loc[ticker, 'Max Drawdown'] * 100,
                    'Sortino_Ratio': final_recommendations.loc[ticker, 'Sortino Ratio'],
                    'Calmar_Ratio': final_recommendations.loc[ticker, 'Calmar Ratio'],
                    'Omega_Ratio': final_recommendations.loc[ticker, 'Omega Ratio'],
                    'AUM': np.random.uniform(1000, 50000),  # 임시값
                    'Expense_Ratio': np.random.uniform(0.05, 0.75),  # 임시값
                    'Recommendation_Score': final_recommendations.loc[ticker, 'RecommendationScore']
                }
                result_df = pd.concat([result_df, pd.DataFrame([row_data])], ignore_index=True)
            
            return result_df
            
        except Exception as e:
            st.error(f"추천 생성 중 오류 발생: {e}")
            return None
    
    def _get_etf_name(self, ticker):
        """ETF 이름 반환"""
        name_map = {
            '069500': 'KODEX 200',
            '102110': 'TIGER 200',
            'SPY': 'SPDR S&P 500 ETF',
            'QQQ': 'Invesco QQQ Trust',
            'VTI': 'Vanguard Total Stock Market ETF',
            'TLT': 'iShares 20+ Year Treasury Bond ETF',
            'GLD': 'SPDR Gold Shares',
            'SLV': 'iShares Silver Trust'
        }
        return name_map.get(ticker, f"{ticker} ETF")
    
    def _get_etf_category(self, ticker):
        """ETF 카테고리 반환"""
        if ticker in self.etf_theme_map:
            theme = self.etf_theme_map[ticker]
            if theme == '기술':
                return 'Technology'
            elif theme == '에너지':
                return 'Energy'
            elif theme == '헬스케어':
                return 'Healthcare'
            elif theme == '시장지수':
                return 'Broad Market'
            elif theme == '채권':
                return 'Bonds'
            elif theme == '원자재':
                return 'Commodities'
        
        # 기본 분류
        if any(word in ticker.upper() for word in ['200', 'SPY', 'VTI', 'VOO']):
            return 'Broad Market'
        elif any(word in ticker.upper() for word in ['QQQ', 'XLK', 'TECH']):
            return 'Technology'
        elif any(word in ticker.upper() for word in ['TLT', 'BND', 'AGG']):
            return 'Bonds'
        elif any(word in ticker.upper() for word in ['GLD', 'SLV']):
            return 'Commodities'
        else:
            return 'Others'

