"""
미드폼 분석 대본 프롬프트 생성기
---------------------------------
국내주식 / 미국주식 / 코인 현물 기반 유튜브 미드폼 대본 초안 / 생성용 프롬프트 생성 앱.
"""

import streamlit as st
import datetime
import requests
from bs4 import BeautifulSoup

# ──────────────────────────────────────────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MRP 대본 프롬프트 생성기",
    page_icon="🎬",
    layout="wide",
)

# ──────────────────────────────────────────────────────────────────────────────
# 스타일
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0e1117; }
.block-container { padding-top: 1.4rem; max-width: 1200px; }

/* 헤더 서브텍스트 */
.tagline {
    font-size: 0.8rem;
    color: #4f5a7a;
    letter-spacing: 0.03em;
    margin-top: -0.8rem;
    margin-bottom: 0.8rem;
}

/* 섹션 라벨 */
.sec-label {
    font-size: 0.78rem;
    font-weight: 700;
    color: #7a8aab;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin: 1.4rem 0 0.35rem 0;
}

/* 구역 구분 카드 */
.zone-card {
    background: #161b27;
    border: 1px solid #252d40;
    border-radius: 12px;
    padding: 1.1rem 1.3rem 0.8rem 1.3rem;
    margin-bottom: 0.8rem;
}

/* 뉴스 블록 */
.news-block {
    background: #1a2035;
    border: 1px solid #2a3455;
    border-radius: 8px;
    padding: 0.8rem 0.9rem;
    margin-bottom: 0.5rem;
}

/* 생성 버튼 */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4f8ef7, #6c63ff);
    color: #fff;
    font-weight: 700;
    font-size: 1.05rem;
    padding: 0.65rem 2.5rem;
    border: none;
    border-radius: 9px;
    width: 100%;
    transition: opacity 0.18s;
}
div.stButton > button[kind="primary"]:hover { opacity: 0.82; }

/* 삭제 버튼 */
div.stButton > button[kind="secondary"] {
    font-size: 0.78rem;
    padding: 0.25rem 0.7rem;
    border-radius: 6px;
}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# 헬퍼: 섹션 라벨
# ──────────────────────────────────────────────────────────────────────────────
def sec(label: str):
    st.markdown(f'<div class="sec-label">{label}</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# 플롯 구조 설명 (tooltip caption)
# ──────────────────────────────────────────────────────────────────────────────
PLOT_CAPTIONS = {
    "정석형":     "자산 소개 → 배경 → 핵심 포인트 → 리스크 → 결론",
    "질문형":     "초반 질문·불안 제기로 시선 끌기 → 중반 해소 → 결론",
    "회수형":     "초반 궁금증 던지고 후반에서 회수",
    "능구렁이형": "중간중간 긴장감·궁금증을 자연스럽게 섞어 이탈 방지",
    "불스아이":   "숫자·기한·통념 뒤집기로 시작하고, 반박 처리와 요약까지 강하게 밀고 가는 구조",
    "3막 8장형":   "강한 후킹 후 3막 구조 내 8개 전개 포인트로 20분 장문 서사 전개",
}

PLOT_DETAIL = {
    "정석형":     "자산 소개 → 배경 설명 → 핵심 포인트 → 리스크 점검 → 결론 순서로 안정적으로 전개한다.",
    "질문형":     "오프닝에서 날카로운 질문이나 불안 요소를 던져 시청자의 시선을 단번에 끌고, 중반부에서 이를 풀어내는 방식으로 전개한다.",
    "회수형":     "오프닝에서 강한 궁금증을 던지고, 중반을 지나 후반부에서 그 답을 회수하면서 시청자를 끝까지 붙잡는 구조로 전개한다.",
    "능구렁이형": "특정 구조 없이 흐름 속에서 자연스럽게 긴장감과 궁금증을 반복 투입해 이탈 없이 끝까지 시청을 유도한다.",
    "불스아이":   "초반 3문장 안에 숫자·기한·위기감·대중의 오해 중 최소 1개를 활용해 '다들 A를 보지만 진짜 중요한 건 B다'라는 식으로 통념을 뒤집는다. 중반부에는 예상 반박이나 의문을 꺼내 논리로 받아치고, 후반부에는 핵심 요약(3포인트 등)을 정리하여 전체적으로 강한 흡입력과 서사성을 유지한다.",
    "3막 8장형":   "도입부에서 강한 궁금증을 만들고, 3막 구조 안에서 8개의 전개 포인트로 흐름을 나눠 긴 호흡으로 서사를 끌고 가는 구조. 기본적으로 20분 장문 대본에 적합하며, A4 4~5장 정도의 분량감을 기준으로 한다.",
}

# ──────────────────────────────────────────────────────────────────────────────
# 조회 함수 및 콜백
# ──────────────────────────────────────────────────────────────────────────────
def get_current_stock_price(query):
    try:
        url = f"https://search.naver.com/search.naver?query={query}+주가"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        selectors = [
            '.spt_con strong.t_nv',
            '.spt_con strong',
            'div.spt_tcon > strong',
            '.spt_con span.spt_txt',
            '.st_prc strong',
        ]
        for selector in selectors:
            price_tag = soup.select_one(selector)
            if price_tag and price_tag.text.strip():
                for blind in price_tag.select(".blind"):
                    blind.decompose()
                return price_tag.text.strip(), None
        return "", "HTML 구조 변경 또는 현재가를 찾을 수 없습니다."
    except Exception as e:
        return "", f"조회 중 에러 발생: {str(e)}"

def get_current_coin_price(query):
    try:
        query = query.strip().upper()
        coin_map = {
            "비트코인": "KRW-BTC", "BTC": "KRW-BTC",
            "이더리움": "KRW-ETH", "ETH": "KRW-ETH",
            "리플":     "KRW-XRP", "XRP": "KRW-XRP",
            "솔라나":   "KRW-SOL", "SOL": "KRW-SOL",
            "도지코인": "KRW-DOGE", "DOGE": "KRW-DOGE",
            "에이다":   "KRW-ADA", "ADA": "KRW-ADA",
            "아발란체": "KRW-AVAX", "AVAX": "KRW-AVAX",
        }
        if query in coin_map:
            market = coin_map[query]
        elif query.startswith("KRW-"):
            market = query
        else:
            market = f"KRW-{query}"

        url = f"https://api.upbit.com/v1/ticker?markets={market}"
        res = requests.get(url, headers={"accept": "application/json"})
        if res.status_code == 200:
            data = res.json()
            if data and len(data) > 0:
                price = data[0]['trade_price']
                formatted = f"{price:,.0f}" if price >= 100 else str(price)
                return formatted, None
        return "", f"업비트 API 조회 실패 (종목코드 확인: {market})"
    except Exception as e:
        return "", f"에러 발생: {str(e)}"

def fetch_price():
    query = st.session_state.get("ticker_name", "").strip()
    if not query:
        st.session_state.current_price = ""
        st.session_state.price_error = "종목명 또는 티커를 입력하세요."
        return
        
    atype = st.session_state.get("asset_type", "국내 주식")
    if atype in ["국내 주식", "해외 주식"]:
        price, err = get_current_stock_price(query)
    else:
        price, err = get_current_coin_price(query)
        
    if price:
        st.session_state.current_price = price
        if "price_error" in st.session_state:
            del st.session_state.price_error
    else:
        st.session_state.current_price = ""
        st.session_state.price_error = err

# ──────────────────────────────────────────────────────────────────────────────
# 프롬프트 빌더
# ──────────────────────────────────────────────────────────────────────────────
def build_prompt(opts: dict, inputs: dict) -> str:
    SEP = "─" * 64

    # ── 뉴스 텍스트
    news_lines = ""
    for i, n in enumerate(inputs["news_blocks"], 1):
        if not n["title"].strip():
            continue
        news_lines += f"  {i}. {n['title'].strip()}\n"
        if n["link"].strip():
            news_lines += f"     링크: {n['link'].strip()}\n"
    if not news_lines:
        news_lines = "  (입력 없음)\n"

    # ── 플롯
    plot_str = opts.get("plot_structure") or "(미설정)"
    plot_desc = PLOT_DETAIL.get(plot_str, "")

    # ── 3막 8장형 전용 보강 규칙
    three_act_eight_scene_rules = ""
    if plot_str == "3막 8장형":
        three_act_eight_scene_rules = """
[3막 8장형 전용 규칙]
- 도입부에서 강한 궁금증을 만들고, 단순 정보 나열로 시작하지 말 것
- 초반 3~5문장 안에 숫자, 기한, 위기감, 사람들이 흔히 갖는 오해 중 최소 1개를 활용해 왜 지금 이 주제를 봐야 하는지 강하게 전달할 것
- 3막 구조 안에서 8개의 전개 포인트가 자연스럽게 이어지게 구성할 것
- 20분 장문 대본 기준으로, A4 4~5장 정도의 분량감(대략 5,000자 전후)을 유지할 것
- 중간에는 반박, 의문, 전환 포인트를 넣어 흐름이 늘어지지 않게 할 것
- 후반부에는 반드시 핵심 정리 구간을 넣을 것
"""

    # ── 영상 길이 → 오프닝 강조 시간
    # 3막 8장형 선택 시 영상 길이는 20분 고정 취급
    target_length = "20분" if plot_str == "3막 8장형" else (opts.get("video_length") or "")
    length_map = {"5분": "30초", "7분": "40초", "10분": "1분", "15분": "1분 30초", "20분": "2분"}
    opening_time = length_map.get(target_length, "30초")
    rehook = "- 10분 이상 길이이므로 중간 재후킹(브릿지 멘트) 1회 이상 필수 삽입\n" \
             if target_length in ["10분", "15분", "20분"] else ""

    # ── 출력 모드 지시
    mode = opts.get("output_mode") or "구조형"
    if mode == "구조형":
        output_instr = (
            "[출력 형식 — 구조형]\n"
            "오프닝 / 배경 및 뉴스 / 핵심 분석 / 리스크 / 마무리 섹션별로\n"
            "말할 핵심 포인트를 bullet 형태로 정리한다. 완성 문장 불필요."
        )
    elif mode == "구조형 + 샘플 대사":
        output_instr = (
            "[출력 형식 — 구조형 + 샘플 대사]\n"
            "① 섹션별 핵심 포인트(구조형) 먼저 작성\n"
            "② 이후 아래 세 항목을 실제 대사 형태로 추가:\n"
            "   - 오프닝 예시 (첫 30초)\n"
            "   - 중간 전환 예시 (섹션 브릿지)\n"
            "   - 마무리 예시 (마지막 30초)"
        )
    else:  # 완전 대본형
        output_instr = (
            "[출력 형식 — 완전 대본형]\n"
            "오프닝부터 마무리까지 실제 방송에서 읽을 수 있는 완전 문장형 대본 작성.\n"
            "구어체 유지. 섹션 전환은 [섹션명] 태그로 표기."
        )

    # ── 코인 이벤트 섹션
    event_section = ""
    if opts.get("asset_type") == "코인" and opts.get("event_mode") == "사용함":
        ev_type = opts.get("event_type") or ""
        ev_name = opts.get("event_custom", "").strip() if ev_type == "기타 직접 입력" else ev_type
        if ev_name:
            event_section = f"""
[코인 이벤트 분석 — {ev_name}]
일반 자산 구조형과 달리, 아래 6가지를 반드시 포함해 작성한다:
  1. 이번 이벤트({ev_name})가 왜 중요한지 (시장 맥락)
  2. 시장이 왜 긴장하고 있는지 (심리·수급 관점)
  3. 어떤 자산이 가장 민감하게 반응하는지
  4. 발표 전 기대 심리 vs 위험 심리 대비
  5. 시나리오 분기 (긍정/부정 시나리오와 예상 반응)
  6. 발표 후 체크포인트 (투자자가 확인해야 할 지표)
"""

    # ── 참고 스크립트 섹션
    ref_section = ""
    ref_script = inputs.get("ref_script", "").strip()
    ref_strength = opts.get("script_ref_strength") or "참고만"

    if ref_script:
        ref_section = f"""
[참고 스크립트 반영 원칙 — {ref_strength}]
- 참고 스크립트의 문장과 표현을 그대로 재사용하지 말고, 전개 방식과 리듬만 참고해 현재 입력 기준으로 새롭게 작성할 것
- 참고 제목이나 원문 오프닝을 그대로 재사용하지 말고, 현재 입력한 주제와 정보 기준으로 새 제목과 오프닝을 작성할 것
- 참고 스크립트는 복사 대상이 아니라 잘되는 구조를 분석하는 데이터로 취급할 것

[참고 데이터 (원문 스크립트)]
{ref_script[:3000]}{'...(이하 생략)' if len(ref_script) > 3000 else ''}
"""

    # ── 조립
    ref_date = inputs.get('ref_date', '')
    content_type = inputs.get("content_type", "종목 분석형")
    ticker   = inputs.get('ticker_name', '').strip() or '(미입력)'
    current_price = inputs.get('current_price', '').strip()
    market_status = inputs.get('market_status', '')

    prompt_ref_date = f"- 기준 날짜   : {ref_date}\n" if ref_date else ""
    prompt_price = ""
    prompt_market = ""
    
    if content_type == '종목 분석형':
        if current_price:
            prompt_price = f"- 현재 주가   : {current_price}\n"
        if market_status:
            prompt_market = f"- 시장 상태   : {market_status}\n"
    # ── 서사 보정 원칙 블록
    narrative_compensation_rules = """
[서사 보정 원칙]
- 입력 정보가 적더라도 밋밋한 정보 나열이 되지 않도록 아래 흐름을 자동 반영할 것:
  1) 왜 지금 이 주제를 봐야 하는가
  2) 사람들이 흔히 어떻게 생각하는가
  3) 그런데 진짜 핵심 포인트는 무엇인가
  4) 핵심 축 2~3개
  5) 반박 또는 리스크
  6) 마지막 요약
- 뉴스나 추가 요청 사항이 부족해도, 현재 위치·시장 기대·핵심 논리·리스크·시나리오 중심으로 전개할 것
- 입력되지 않은 최신 사실은 임의로 지어내지 말고, 일반적인 시장 맥락 안에서만 확장할 것
"""

    # ── 사실 검증 원칙 블록
    fact_verification_rules = """
[사실 검증 원칙]
- 입력되지 않은 뉴스나 사실은 임의로 지어내지 말 것
- 최신 정보, 숫자, 일정, 계약, 정책, 이벤트는 가능한 한 공개 자료를 기준으로 보수적으로 다룰 것
- 확인되지 않은 내용은 사실처럼 단정하지 말고, 가능성 또는 시장 해석 수준으로 표현할 것
- 팩트와 해석을 구분해서 작성할 것
- 자극적인 서사보다 사실 정확성을 우선할 것
"""

    # ── 추가 작성 원칙 블록
    fixed_instructions = """
[추가 작성 원칙]
- 같은 말을 반복하거나 뻔한 수식어로 분량을 채우지 말 것
- 실제 유튜브 미드폼처럼 초반 흡입력, 중반 유지, 후반 정리가 살아 있는 자연스러운 구어체 대본으로 작성할 것
- 과장과 반복은 최소화하고, 실제 사람이 바로 수정해서 쓸 수 있는 초안 느낌을 유지할 것
"""

    prompt = f"""{SEP}
[미드폼 분석 대본 생성 프롬프트]
{SEP}

[채널 / 기준 정보]
{prompt_ref_date}- 콘텐츠 유형 : {content_type}
- {'종목명/티커 ' if content_type == '종목 분석형' else '주제명/이슈명'}: {ticker}
{prompt_price}{prompt_market}
[기본 설정]
- 자산 유형   : {opts.get('asset_type') or '(미설정)'}
- 목표 영상 길이: {target_length if plot_str == '3막 8장형' else (opts.get('video_length') or '(미설정)')}  {'(※ 3막 8장형은 20분 분량 고정)' if plot_str == '3막 8장형' else ''}
- 대본 톤     : {opts.get('script_tone') or '(미설정)'}

[플롯 구조]
- {plot_str}: {plot_desc}

[유튜브 미드폼 특성 — {target_length if plot_str == '3막 8장형' else (opts.get('video_length') or '')}]
- 오프닝 {opening_time}: 강력한 흡입력, 이탈 방지 최우선
- 중반부: 정보 밀도 + 흥미 유지, 지루함 방지
{rehook}- 후반부: 결론 명확히, 자연스러운 구독·좋아요 유도

[뉴스 / 이슈]
{news_lines.rstrip()}

[추가 요청 사항]
{inputs.get('extra_notes', '').strip() or '(입력 없음)'}
{event_section}
{output_instr}
{three_act_eight_scene_rules}{ref_section}
{SEP}
위 모든 조건을 종합해 대본 {'프롬프트' if mode == '구조형' else '초안을 완성'}으로 출력하라.
톤({opts.get('script_tone') or '미설정'}), 플롯({plot_str})을 처음부터 끝까지 일관되게 유지할 것.
{fixed_instructions}
{narrative_compensation_rules}
{fact_verification_rules}{SEP}"""

    return prompt


# ──────────────────────────────────────────────────────────────────────────────
# session_state 초기화
# ──────────────────────────────────────────────────────────────────────────────
if "news_blocks" not in st.session_state:
    st.session_state.news_blocks = [{"title": "", "link": ""}]

if "result" not in st.session_state:
    st.session_state.result = ""


# ──────────────────────────────────────────────────────────────────────────────
# 뉴스 블록 추가 / 삭제 콜백
# ──────────────────────────────────────────────────────────────────────────────
def add_news_block():
    st.session_state.news_blocks.append({"title": "", "link": ""})


def remove_news_block(idx: int):
    if len(st.session_state.news_blocks) > 1:
        st.session_state.news_blocks.pop(idx)


# ══════════════════════════════════════════════════════════════════════════════
# UI 렌더링
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 🎬 MRP 대본 프롬프트 생성기")
st.markdown("<div class='tagline'>Developed by J &amp; Ria</div>", unsafe_allow_html=True)
st.divider()

# ─────────────────────────────────────────────
# 헬퍼: selectbox (빈 기본값 포함)
# ─────────────────────────────────────────────
def sel(label, options, key, help=None):
    """index=None selectbox — 기본 상태에서 미선택."""
    return st.selectbox(
        label, options,
        index=None,
        placeholder="선택",
        key=key,
        help=help,
    )


# ─────────────────────────────────────────────
# ① 기본 정보
# ─────────────────────────────────────────────
sec("① 기본 정보")

with st.container(border=True):
    content_type = st.radio(
        "콘텐츠 유형",
        ["종목 분석형", "정보형 / 이슈형"],
        horizontal=True,
    )
    st.markdown("<div style='margin-bottom:0.8rem'></div>", unsafe_allow_html=True)

    use_ref_date = st.checkbox("기준 날짜 사용", value=True, key="use_ref_date")
    if use_ref_date:
        ref_date = st.date_input(
            "날짜 선택",
            value=datetime.date.today(),
            key="ref_date",
            label_visibility="collapsed"
        )
    else:
        ref_date = ""

    st.markdown("<div style='margin-bottom:0.4rem'></div>", unsafe_allow_html=True)
    asset_type = sel("자산 유형", ["국내 주식", "해외 주식", "코인"], "asset_type")
    
    st.markdown("<div style='margin-bottom:0.4rem'></div>", unsafe_allow_html=True)
    current_price = ""
    market_status = ""
    if content_type == "종목 분석형":
        ticker_name = st.text_input(
            "종목명 / 티커",
            placeholder="",
            key="ticker_name",
        )
        
        c1, c2 = st.columns([2.5, 1])
        with c1:
            current_price = st.text_input("현재 주가", key="current_price", placeholder="수동 입력 가능")
        with c2:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            btn_label = "🔄 업비트 현재가" if st.session_state.get("asset_type") == "코인" else "🔄 현재 주가"
            st.button(btn_label, on_click=fetch_price, use_container_width=True)
            
        if "price_error" in st.session_state:
            st.warning(f"조회 실패: {st.session_state.price_error}")
            
        if st.session_state.get("asset_type", "국내 주식") in ["국내 주식", "해외 주식"]:
            market_status = st.radio("시장 상태", ["장 중", "장 마감"], horizontal=True, key="market_status")
    else:
        ticker_name = st.text_input(
            "주제명 / 이슈명",
            placeholder="",
            key="ticker_name",
        )


# ─────────────────────────────────────────────
# ② 선택 옵션
# ─────────────────────────────────────────────
sec("② 선택 옵션")

with st.container(border=True):
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        video_length = sel("목표 영상 길이", ["5분", "7분", "10분", "15분", "20분"], "video_length")
        
        # 3막 8장형 안내 문구 표시 로직을 위해 세션 스테이트 참조 위치는 뒤로 밀리므로
        # 플롯 구조 선택 칸 다음에 처리하는 것이 UI 업데이트 상 자연스럽습니다.
        # Streamlit 동작상 selectbox의 값을 즉시 반영하려면 콜백이나 rerun이 필요하지만,
        # 프롬프트 빌더 내부에서 길이를 강제로 20분으로 덮어씌웁니다.
    with r1c2:
        script_tone = sel(
            "대본 톤",
            ["뉴스형", "해설형", "리서치형", "자신감형"],
            "script_tone",
            help=(
                "**뉴스형**: 뉴스 브리핑처럼 빠르고 간결한 톤\n\n"
                "**해설형**: 내용을 쉽게 풀어 설명하는 톤\n\n"
                "**리서치형**: 근거와 분석을 중심으로 설명하는 톤\n\n"
                "**자신감형**: 단호하고 힘 있게 말하는 톤"
            ),
        )

    st.markdown("<div style='margin-top:0.4rem'></div>", unsafe_allow_html=True)
    r2c1, r2c2 = st.columns(2)

    with r2c1:
        plot_structure = sel(
            "플롯 구조",
            list(PLOT_CAPTIONS.keys()),
            "plot_structure",
            help=(
                "**정석형**: 배경부터 핵심, 리스크, 결론까지 순서대로 정리하는 구조\n\n"
                "**질문형**: 초반에 질문을 던지고 그 답을 풀어가는 구조\n\n"
                "**회수형**: 초반에 던진 포인트를 뒤에서 다시 회수하는 구조\n\n"
                "**능구렁이형**: 중간중간 궁금한 포인트를 넣어 끝까지 보게 하는 구조\n\n"
                "**불스아이**: 숫자·기한·통념 뒤집기로 시작하고, 반박 처리와 요약까지 강하게 밀고 가는 구조\n\n"
                "**3막 8장형**: 도입부에서 강한 궁금증을 만들고, 3막 구조 안에서 8개의 전개 포인트로 흐름을 나눠 긴 호흡으로 서사를 끌고 가는 구조. 기본적으로 20분 장문 대본에 적합하며, A4 4~5장 정도의 분량감을 기준으로 한다."
            ),
        )
        if plot_structure == "3막 8장형":
            st.markdown("<div style='font-size: 0.75rem; color: #ffab40; margin-top: -0.5rem;'>💡 3막 8장형은 20분 기준 장문 구조로 자동 처리됩니다.</div>", unsafe_allow_html=True)

    with r2c2:
        output_mode = sel(
            "출력 모드",
            ["구조형", "구조형 + 샘플 대사", "완전 대본형"],
            "output_mode",
            help=(
                "**구조형**: 말할 내용의 흐름과 핵심만 정리해서 출력\n\n"
                "**구조형 + 샘플 대사**: 구조에 더해 예시 문장까지 같이 출력\n\n"
                "**완전 대본형**: 바로 읽을 수 있게 문장형 대본으로 출력"
            ),
        )


# ─────────────────────────────────────────────
# 🪙 코인 전용 옵션 (코인 선택 시에만 표시)
# ─────────────────────────────────────────────
event_mode   = None
event_type   = None
event_custom = ""

if asset_type == "코인":
    sec("🪙 코인 전용 옵션")

    with st.container(border=True):
        coin_c1, coin_c2, coin_c3 = st.columns(3)

        with coin_c1:
            event_mode = sel("이벤트 모드", ["사용 안 함", "사용함"], "event_mode")

        if event_mode == "사용함":
            event_type_options = [
                "CPI", "FOMC", "금리 인하 기대", "ETF 승인/거절",
                "토큰 언락", "대형 상장/상폐", "비트 도미넌스 변화", "기타 직접 입력",
            ]
            with coin_c2:
                event_type = sel("이벤트 유형", event_type_options, "event_type")
            if event_type == "기타 직접 입력":
                with coin_c3:
                    event_custom = st.text_input(
                        "기타 이벤트 내용",
                        placeholder="이벤트명 직접 입력",
                        key="event_custom",
                    )


# ─────────────────────────────────────────────
# ③ 입력 영역
# ─────────────────────────────────────────────
sec("③ 입력 영역")

with st.container(border=True):
    st.markdown("**📰 뉴스 / 이슈**")

    # 뉴스 블록 렌더링 (session_state 기반)
    for i, block in enumerate(st.session_state.news_blocks):
        with st.container(border=True):
            n_c1, n_c2, n_c3 = st.columns([2.8, 2.8, 0.4])
            with n_c1:
                block["title"] = st.text_input(
                    "뉴스 제목", value=block["title"],
                    key=f"news_title_{i}",
                    placeholder="뉴스 제목 입력",
                    label_visibility="collapsed" if i > 0 else "visible",
                )
            with n_c2:
                block["link"] = st.text_input(
                    "링크", value=block["link"],
                    key=f"news_link_{i}",
                    placeholder="",
                    label_visibility="collapsed" if i > 0 else "visible",
                )
            with n_c3:
                if len(st.session_state.news_blocks) > 1:
                    st.markdown("<div style='margin-top:1.65rem'></div>", unsafe_allow_html=True)
                    if st.button("✕", key=f"del_news_{i}", help="이 뉴스 블록 삭제"):
                        remove_news_block(i)
                        st.rerun()

    if st.button("＋ 뉴스 추가", key="add_news_btn"):
        add_news_block()
        st.rerun()

    ref_script = st.text_area(
        "📄 참고 스크립트  (유튜브 자막 / 대본 전체 붙여넣기 가능)",
        height=200,
        key="ref_script",
        placeholder=(
            "참고할 스크립트를 여기에 붙여넣으세요.\n"
            "말투, 문장 리듬, 오프닝·전개·마무리 방식에 반영합니다.\n"
            "내용(종목·뉴스·근거)은 복사하지 않고, 현재 입력 기준으로 새로 생성합니다."
        ),
    )

    # ── 참고 스크립트 반영 강도
    _ref_has_text = bool(ref_script.strip())
    script_ref_strength = st.selectbox(
        "📊 참고 스크립트 반영 강도",
        ["참고만", "우선 반영", "강하게 반영"],
        index=0,
        key="script_ref_strength",
        disabled=not _ref_has_text,
        help=(
            "**참고만**: 참고 스크립트 분위기만 가볍게 반영\n\n"
            "**우선 반영**: 참고 스크립트의 말투와 흐름을 우선 반영\n\n"
            "**강하게 반영**: 참고 스크립트 스타일을 최대한 따라가되 내용은 새로 작성"
        ) if _ref_has_text else "상단의 참고 스크립트를 입력하면 활성화됩니다.",
    )

    st.markdown("**📝 추가 요청 사항**")
    st.markdown(
        "<div style='font-size:0.8rem; color:#8a94a6; margin-top:-0.5rem; margin-bottom:0.5rem;'>"
        "강조하고 싶은 포인트, 원하는 전개 방향, 말투 톤, 꼭 반영할 사항을 자유롭게 적어주세요.</div>",
        unsafe_allow_html=True
    )
    extra_notes = st.text_area(
        "추가 요청 사항",
        height=130,
        key="extra_notes",
        placeholder="",
        label_visibility="collapsed",
    )


# ─────────────────────────────────────────────
# 생성 버튼
# ─────────────────────────────────────────────
st.markdown("")
gen_col, _ = st.columns([1.2, 4])
with gen_col:
    generate = st.button("🚀  프롬프트 생성", type="primary", key="generate_btn")


# ─────────────────────────────────────────────
# 입력 검증 + 생성
# ─────────────────────────────────────────────
REQUIRED_FIELDS = [
    ("asset_type",     "자산 유형"),
    ("video_length",   "목표 영상 길이"),
    ("script_tone",    "대본 톤"),
    ("plot_structure", "플롯 구조"),
    ("output_mode",    "출력 모드"),
]

if generate:
    missing = []

    # 공통 필수 항목
    for key, label in REQUIRED_FIELDS:
        if not st.session_state.get(key):
            missing.append(label)

    # 기본 정보 필수
    if not ticker_name.strip():
        missing.append("종목명" if content_type == "종목 분석형" else "주제명 / 이슈명")

    # 코인 이벤트
    if asset_type == "코인":
        if not event_mode:
            missing.append("이벤트 모드")
        if event_mode == "사용함" and not event_type:
            missing.append("이벤트 유형")
        if event_mode == "사용함" and event_type == "기타 직접 입력" and not event_custom.strip():
            missing.append("기타 이벤트 내용")

    if missing:
        st.error(f"❌ 필수 입력 누락: **{', '.join(missing)}**")
    else:
        opts = {
            "asset_type":          asset_type,
            "video_length":        video_length,
            "script_tone":         script_tone,
            "plot_structure":      plot_structure,
            "output_mode":         output_mode,
            "script_ref_strength": script_ref_strength,
            "event_mode":          event_mode,
            "event_type":          event_type,
            "event_custom":        event_custom,
        }
        inputs = {
            "ref_date":     str(ref_date) if use_ref_date else "",
            "content_type": content_type,
            "ticker_name":  ticker_name,
            "current_price": current_price,
            "market_status": market_status,
            "news_blocks":  st.session_state.news_blocks,
            "extra_notes":  extra_notes,
            "ref_script":   ref_script,
        }
        st.session_state.result = build_prompt(opts, inputs)


# ─────────────────────────────────────────────
# ④ 결과 영역
# ─────────────────────────────────────────────
if st.session_state.result:
    st.divider()
    sec("④ 결과")
    st.info(
        "아래 결과를 복사해서 ChatGPT, Claude 등 AI에 붙여넣으세요.  "
        "코드 블록 우측의 **복사 아이콘**을 클릭하면 바로 복사됩니다.",
        icon="📋",
    )
    st.code(st.session_state.result, language="text")


