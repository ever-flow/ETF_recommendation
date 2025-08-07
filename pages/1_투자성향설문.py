import streamlit as st

st.set_page_config(
    page_title="투자 성향 설문",
    page_icon="📋",
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
            📋 투자 성향 분석
        </div>
        <div style="font-size: 12px; color: #6b7280; margin-top: 5px;">
            7가지 질문을 통한 맞춤형 분석
        </div>
    </div>
    """, unsafe_allow_html=True)

st.title("투자 성향 설문")
st.markdown("### 맞춤형 ETF 추천을 위한 7가지 질문")

# 설문 진행률 초기화
if 'current_question' not in st.session_state:
    st.session_state.current_question = 1
    st.session_state.answers = {}

# 진행률 표시
progress = st.session_state.current_question / 7
st.progress(progress)
st.write(f"질문 {st.session_state.current_question}/7")

# 질문 정의
questions = [
    {
        "title": "1. 투자 위험에 대한 귀하의 성향은?",
        "options": [
            "매우 낮음 - 원금 손실을 절대 원하지 않음",
            "낮음 - 작은 손실도 부담스러움",
            "보통 - 적당한 위험은 감수 가능",
            "높음 - 높은 수익을 위해 위험 감수",
            "매우 높음 - 큰 손실도 감수하며 고수익 추구"
        ],
        "key": "risk_tolerance"
    },
    {
        "title": "2. 투자 예정 기간은?",
        "options": [
            "1년 미만 - 단기 투자",
            "1-3년 - 중단기 투자",
            "3-5년 - 중장기 투자",
            "5-10년 - 장기 투자",
            "10년 이상 - 초장기 투자"
        ],
        "key": "investment_horizon"
    },
    {
        "title": "3. 투자 목표는?",
        "options": [
            "자산 보존 - 인플레이션 대응 수준",
            "안정적 수익 - 예금 금리보다 조금 높은 수익",
            "시장 평균 - 주식시장 평균 수익률",
            "성장 - 시장 평균보다 높은 수익",
            "고수익 - 높은 위험을 감수하고 고수익 추구"
        ],
        "key": "goal"
    },
    {
        "title": "4. 선호하는 투자 시장은?",
        "options": [
            "한국 시장 - 국내 ETF 위주",
            "미국 시장 - 해외 ETF 위주",
            "상관없음 - 수익률이 좋다면 어디든"
        ],
        "key": "market_preference"
    },
    {
        "title": "5. 투자 경험은?",
        "options": [
            "초보 - 투자 경험이 거의 없음",
            "중급 - 몇 년간의 투자 경험",
            "고급 - 다양한 투자 상품 경험"
        ],
        "key": "experience"
    },
    {
        "title": "6. 손실에 대한 회피 성향은?",
        "options": [
            "매우 높음 - 손실을 절대 받아들일 수 없음",
            "높음 - 손실이 매우 부담스러움",
            "보통 - 적당한 손실은 감수 가능",
            "낮음 - 손실에 대해 비교적 담담함",
            "매우 낮음 - 손실도 투자의 일부로 받아들임"
        ],
        "key": "loss_aversion"
    },
    {
        "title": "7. 선호하는 투자 테마는?",
        "options": [
            "상관없음 - 수익률이 좋다면 어떤 테마든",
            "기술 - IT, 반도체, 인공지능 등",
            "에너지 - 신재생에너지, 원유 등",
            "헬스케어 - 바이오, 제약, 의료기기 등"
        ],
        "key": "theme_preference"
    }
]

# 현재 질문 표시
current_q = questions[st.session_state.current_question - 1]
st.subheader(current_q["title"])

# 라디오 버튼으로 선택지 표시
selected_option = st.radio(
    "다음 중 하나를 선택해주세요:",
    options=current_q["options"],
    index=None,
    key=f"q_{st.session_state.current_question}"
)

# 선택 확인 및 버튼
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    if st.session_state.current_question > 1:
        if st.button("이전 질문", use_container_width=True):
            st.session_state.current_question -= 1
            st.rerun()

with col3:
    if selected_option:
        if st.session_state.current_question < 7:
            if st.button("다음 질문", use_container_width=True, type="primary"):
                # 답변 저장 (1-5 점수로 변환)
                answer_value = current_q["options"].index(selected_option) + 1
                if current_q["key"] == "market_preference":
                    answer_value = current_q["options"].index(selected_option) + 1  # 1,2,3
                elif current_q["key"] == "experience":
                    answer_value = current_q["options"].index(selected_option) + 1  # 1,2,3
                else:
                    answer_value = current_q["options"].index(selected_option) + 1  # 1-5
                
                st.session_state.answers[current_q["key"]] = answer_value
                st.session_state.current_question += 1
                st.rerun()
        else:
            if st.button("설문 완료", use_container_width=True, type="primary"):
                # 마지막 답변 저장
                answer_value = current_q["options"].index(selected_option) + 1
                st.session_state.answers[current_q["key"]] = answer_value
                
                # 사용자 프로필 생성
                st.session_state.user_profile = st.session_state.answers
                
                # 설문 상태 초기화
                del st.session_state.current_question
                del st.session_state.answers
                
                st.success("설문이 완료되었습니다!")
                st.balloons()
                
                # 자동으로 추천 결과 페이지로 이동
                st.switch_page("pages/2_추천결과.py")

# 선택된 답변 표시
if selected_option:
    st.success(f"선택: {selected_option}")

# 설문 안내
with st.expander("설문 안내", expanded=False):
    st.markdown("""
    **설문 목적**: 귀하의 투자 성향을 파악하여 맞춤형 ETF를 추천합니다.
    
    **소요 시간**: 약 3-5분
    
    **주의사항**: 
    - 정확한 추천을 위해 솔직하게 답변해주세요
    - 각 질문은 투자 성향 분석에 중요한 요소입니다
    - 언제든지 이전 질문으로 돌아가 수정할 수 있습니다
    """)

