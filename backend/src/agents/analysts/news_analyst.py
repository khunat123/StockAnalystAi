"""
News Analyst - News sentiment analysis
"""

import os
from src.agents.base_agent import BaseAgent
from src.data.tools.data_tools import get_news


class NewsAnalyst(BaseAgent):
    """Analyzes news sentiment for stocks"""
    
    def __init__(self):
        super().__init__("NewsAnalyst")

    def analyze(self, ticker: str) -> dict:
        """
        Analyze news sentiment for a stock
        
        Args:
            ticker: Stock symbol
            
        Returns:
            dict with sentiment and report_section
        """
        self.log(f"Fetching news for {ticker}...")
        
        # Try fetching news from Tavily first
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.log(f"Tavily API Key found: {'Yes' if tavily_api_key else 'No'}")
        news_items = []
        
        if tavily_api_key:
            try:
                self.log("Attempting to fetch news from Tavily...")
                from tavily import TavilyClient
                tavily = TavilyClient(api_key=tavily_api_key)
                response = tavily.search(query=f"{ticker} stock news", topic="news", max_results=5)
                self.log(f"Tavily response keys: {response.keys()}")
                
                if 'results' in response:
                    for item in response['results']:
                        news_items.append({
                            "title": item['title'],
                            "publisher": item['url'].split('/')[2],
                            "link": item['url'],
                            "published": item.get('published_date', 'Unknown')
                        })
                    self.log(f"Fetched {len(news_items)} news items from Tavily.")
            except Exception as e:
                self.log(f"Tavily error: {e}. Falling back to yfinance.")
        
        # Fallback to yfinance
        if not news_items:
            news_items = get_news(ticker)
        
        # Prepare news summary
        news_summary = ""
        if news_items:
            news_summary = "| # | ชื่อข่าว | ผู้เผยแพร่ | ลิงก์ |\n"
            news_summary += "|---|---------|----------|------|\n"
            for i, item in enumerate(news_items[:5], 1):
                title = item.get('title') or 'No title'
                title = title[:80] + "..." if len(title) > 80 else title
                publisher = item.get('publisher') or 'Unknown'
                link = item.get('link') or '#'
                news_summary += f"| {i} | {title} | {publisher} | {link} |\n"
        
        if not news_summary:
            news_summary = "No recent news found."
            
        system_prompt = """You are a professional news analyst. 
        Your job is to read the provided news headlines and write a sentiment analysis report.
        **IMPORTANT: Write the entire report in Thai language.**
        Use Markdown formatting.
        Conclude with a clear sentiment score: POSITIVE, NEGATIVE, or NEUTRAL."""
        
        user_prompt = f"""
        Analyze the following news for {ticker}:
        
        {news_summary}
        
        Please provide:
        1. A summary of the key news topics.
        2. An analysis of the overall market sentiment towards the company.
        3. A final sentiment verdict (POSITIVE/NEGATIVE/NEUTRAL).
        
        **CRITICAL:** Cite the source with a clickable link for every claim.
        Format: [Publisher Name](URL)
        
        Format the output as a clean Markdown section starting with '## 3. NEWS ANALYST REPORT'.
        **Remember: The output must be in Thai.**
        """
        
        self.log(f"Asking LLM to analyze news for {ticker}...")
        report = self.call_llm(system_prompt, user_prompt)
        
        # Extract sentiment
        sentiment = "NEUTRAL"
        if "POSITIVE" in report.upper():
            sentiment = "POSITIVE"
        elif "NEGATIVE" in report.upper():
            sentiment = "NEGATIVE"
            
        return {
            "sentiment": sentiment,
            "report_section": report
        }
