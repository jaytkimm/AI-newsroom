import os
import streamlit as st
import google.generativeai as genai
from datetime import datetime

def get_gemini_api_key():
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    return os.environ.get("GEMINI_API_KEY", "")

def generate_daily_briefing(articles, model_name="gemini-2.5-flash"):
    """
    Generate a 1-page daily briefing report using Gemini API.
    """
    api_key = get_gemini_api_key()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found. Please set it in .streamlit/secrets.toml")
        
    genai.configure(api_key=api_key)
    
    # Initialize the model
    model = genai.GenerativeModel(model_name)
    
    if not articles:
        return "수집된 기사가 없습니다."
    
    # Format articles for the prompt using IDs instead of raw URLs to prevent truncation
    articles_text = ""
    for i, article in enumerate(articles, 1):
        articles_text += f"[ID: {i}]\n"
        articles_text += f"제목: {article['title']}\n"
        articles_text += f"출처: {article['feed_source']}\n"
        articles_text += f"요약: {article['summary'][:200]}...\n\n"
        
    prompt = f"""
    당신은 홈어플라이언스(가전제품) 산업의 전문 애널리스트이자 뉴스 에디터입니다.
    아래에 최근 72시간 동안 수집된 국내외 주요 가전제품 및 제조사(삼성, LG, 코웨이 등) 관련 뉴스 기사 목록이 있습니다.

    이 데이터를 분석하여, 경영진이 한눈에 파악할 수 있는 **1장 분량의 데일리 브리핑 보고서**를 마크다운(Markdown) 형식으로 작성해 주세요.

    [작성 가이드라인]
    1. **제목 (Title):** 🌟 AI 가전 뉴스룸 데일리 브리핑 ({datetime.now().strftime('%Y년 %m월 %d일')})
    2. **주요 이슈 요약 (Executive Summary):** 3~4줄로 핵심 트렌드를 요약해주세요.
    3. **주제별 그룹화 (Categorized Insights):** 기사들을 연관된 주제(예: 신제품 출시, 실적 발표, AI 기술 동향, 기업 간 경쟁 등)로 묶어 소제목을 달고 인사이트를 도출해주세요.
    4. **출처 링크 포함 (매우 중요):** 각 기사의 내용을 언급할 때, 반드시 마크다운 하이퍼링크 형식으로 출처를 달아주세요. 단, 실제 URL 경로 대신 제공된 기사의 ID 번호를 아래 형식과 같이 그대로 사용하세요. (절대 다른 방식으로 변형하지 마세요!)
       - 예시: [기사제목](ID:1) 또는 [원문보기](ID:2)
    5. 가독성이 좋도록 불릿 포인트, 굵은 글씨(`**`) 등을 적극 활용하세요.

    [수집된 기사 목록]
    {articles_text}
    """
    
    try:
        response = model.generate_content(prompt)
        report_text = response.text
        
        # Post-process: Replace placeholders with actual full URLs
        for i, article in enumerate(articles, 1):
            report_text = report_text.replace(f"(ID:{i})", f"({article['link']})")
            report_text = report_text.replace(f"(ID: {i})", f"({article['link']})")
            
        # Add Infographic logic
        infographic_code = generate_infographic(articles)
        if infographic_code and "다이어그램 생성 실패" not in infographic_code:
            report_text = report_text + f"\n\n### 📊 한눈에 보는 요약 (첨단 AI 인포그래픽)\n```html\n{infographic_code}\n```"
            
        return report_text
    except Exception as e:
        return f"리포트 생성 중 오류가 발생했습니다: {str(e)}"

def generate_infographic(articles):
    """
    Generate a Mermaid.js diagram code using nano-banana-pro-preview.
    """
    api_key = get_gemini_api_key()
    if not api_key:
        return ""
    genai.configure(api_key=api_key)
    if not articles:
        return ""
        
    articles_text = ""
    for i, article in enumerate(articles, 1):
        articles_text += f"{i}. {article['title']} ({article['feed_source']})\n"
        
    prompt = f"""
    아래는 수집된 최신 가전제품 및 IT 뉴스 기사 목록입니다.
    이를 바탕으로 기업 경영진이 한눈에 파악할 수 있는 **매우 화려하고 미래지향적인(사이버펑크) 다크 테마 기반의 HTML/CSS 종합 대시보드(인포그래픽)** 코드를 작성해주세요.
    
    [디자인 및 레이아웃 가이드라인]
    1. **Mermaid나 차트 라이브러리를 쓰지 마세요.** 오직 순수 HTML과 CSS(<style> 태그)만을 활용하여 화려한 UI를 설계해야 합니다.
    2. 전체 배경은 아주 짙은 어두운 색(블랙/다크 네이비)으로 지정하고, 각 요소의 테두리나 텍스트 그림자에 네온 블루(#00f3ff) 및 네온 퍼플(#b026ff) 같은 형광색(glow 효과)을 듬뿍 넣어 첨단 IT 관제 센터 느낌을 연출하세요.
    3. CSS Grid나 Flexbox를 이용해, 화면의 정중앙에는 가장 중요한 '핵심 트렌드 요약' 블록을 띄우고, 좌/우측이나 모서리 쪽에 4~5개의 세부 테마 블록들(예: AI 혁신, 금융 시장, 보안, 글로벌 트렌드 등 제공된 기사를 바탕으로 분류) 방사형 혹은 대칭 형태로 멋지게 배치하세요.
    4. 각 블록 안에는 뉴스 기사에서 분석한 핵심 인사이트 텍스트를 가독성 좋은 폰트 크기 및 색상으로 채워주세요. (불릿 포인트 리스트 적극 활용, 제목은 형광색 텍스트)
    5. 응답 결과는 반드시 ```html 로 시작하고 ``` 로 끝나는 단일 코드 블록 형태로만 제공해야 하며, 다른 부연 설명은 절대 적지 마세요.
    
    [기사 목록]
    {articles_text}
    """
    try:
        try:
            model = genai.GenerativeModel("models/nano-banana-pro-preview")
            response = model.generate_content(prompt)
        except Exception as preview_e:
            model = genai.GenerativeModel("models/gemini-2.5-flash")
            response = model.generate_content(prompt)
        text = response.text
        if "```html" in text:
            text = text.split("```html")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].strip()
        return text
    except Exception as e:
        return f"<!-- 다이어그램 생성 실패: {str(e)} -->"

