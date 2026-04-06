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
        if infographic_code and "%% 다이어그램 생성 실패" not in infographic_code:
            report_text = report_text + f"\n\n### 📊 한눈에 보는 요약\n```mermaid\n{infographic_code}\n```"
            
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
    아래는 수집된 최신 가전제품 뉴스 기사 목록입니다.
    이를 바탕으로 가장 많이 언급된 브랜드, 제품군(정수기, 공기청정기, 로봇청소기 등), 혹은 최신 트렌드를 보여주는 인포그래픽용 다이어그램을 **Mermaid.js** 문법으로만 작성해주세요.
    
    [가이드라인]
    1. Pie chart(파이차트) 또는 Mindmap 중 하나를 사용하여 내용을 도식화 하세요.
    2. 응답에는 오직 ```mermaid 로 시작하고 ``` 로 끝나는 코드 블록만 포함해야 합니다.
    3. 코드 문법 오류가 나지 않도록 매우 조심하세요.
    
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
        if "```mermaid" in text:
            text = text.split("```mermaid")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].strip()
        return text
    except Exception as e:
        return f"%% 다이어그램 생성 실패: {str(e)}"

