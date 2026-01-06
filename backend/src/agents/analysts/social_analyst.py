"""
Social Analyst - Social media sentiment analysis
"""

import os
from src.agents.base_agent import BaseAgent
from src.data.tools.data_tools import get_news


class SocialAnalyst(BaseAgent):
    """Analyzes social media sentiment (Reddit, Twitter)"""
    
    def __init__(self):
        super().__init__("SocialAnalyst")

    def analyze(self, ticker: str) -> dict:
        """
        Analyze social media sentiment
        
        Args:
            ticker: Stock symbol
            
        Returns:
            dict with signal and report_section
        """
        self.log(f"Scanning social signals for {ticker}...")
        
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        social_data = []
        
        if tavily_api_key:
            try:
                from tavily import TavilyClient
                tavily = TavilyClient(api_key=tavily_api_key)
                
                # Search for Reddit discussions
                response = tavily.search(query=f"{ticker} stock reddit discussion", topic="general", max_results=5)
                for item in response.get('results', []):
                    social_data.append(f"Reddit: {item['title']} ({item['url']})")
                    
                # Search for Twitter/X sentiment
                response = tavily.search(query=f"{ticker} stock twitter sentiment", topic="general", max_results=5)
                for item in response.get('results', []):
                    social_data.append(f"Twitter/Web: {item['title']} ({item['url']})")
                    
                self.log(f"Fetched {len(social_data)} social signals from Tavily.")
            except Exception as e:
                self.log(f"Tavily error: {e}. Falling back to simulation.")
        
        # Fallback
        if not social_data:
            news_items = get_news(ticker)
            social_data = [f"Simulated (News): {item['title']}" for item in news_items[:5]]
        
        social_summary = "\n".join(social_data)
        
        system_prompt = """You are a Social Media Analyst. 
        Your job is to gauge the public sentiment and 'buzz' around a stock based on social media discussions.
        **IMPORTANT: Write the entire report in Thai language.**
        Use Markdown formatting.
        Conclude with a social sentiment score: BULLISH, BEARISH, or NEUTRAL."""
        
        user_prompt = f"""
        Analyze the social media sentiment for {ticker} based on these discussions:
        
        {social_summary}
        
        Please provide:
        1. A summary of what retail investors are discussing.
        2. An analysis of the 'Hype' vs 'Fear' levels.
        3. A final social sentiment verdict (BULLISH/BEARISH/NEUTRAL).
        
        Format the output as a clean Markdown section starting with '## 4. SOCIAL ANALYST REPORT'.
        **Remember: The output must be in Thai.**
        """
        
        self.log(f"Asking LLM to analyze social sentiment for {ticker}...")
        report = self.call_llm(system_prompt, user_prompt)
        
        # Extract signal
        signal = "NEUTRAL"
        if "BULLISH" in report.upper():
            signal = "BULLISH"
        elif "BEARISH" in report.upper():
            signal = "BEARISH"
            
        return {
            "signal": signal,
            "report_section": report
        }
