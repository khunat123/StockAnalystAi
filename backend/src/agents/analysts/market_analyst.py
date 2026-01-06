"""
Market Analyst - Technical analysis of price and volume data
"""

from src.agents.base_agent import BaseAgent
from src.data.tools.data_tools import get_stock_data, get_financials


class MarketAnalyst(BaseAgent):
    """Analyzes market price action and technical indicators"""
    
    def __init__(self):
        super().__init__("MarketAnalyst")

    def analyze(self, ticker: str) -> dict:
        """
        Analyze price trends and technical patterns
        
        Args:
            ticker: Stock symbol
            
        Returns:
            dict with signal and report_section
        """
        self.log(f"Fetching market data for {ticker}...")
        
        # Fetch real data
        hist_data = get_stock_data(ticker)
        financials = get_financials(ticker)
        
        # Prepare data for LLM
        recent_prices = hist_data.tail(5).to_string() if not hist_data.empty else "No data available"
        
        system_prompt = """You are a professional financial market analyst. 
        Your job is to analyze the provided stock data and write a detailed technical and fundamental analysis report.
        **IMPORTANT: Write the entire report in Thai language.**
        Use Markdown formatting. Include a table for key financial metrics.
        Conclude with a clear signal: BUY, SELL, or HOLD."""
        
        user_prompt = f"""
        Analyze the following data for {ticker}:
        
        **Recent Price History (Last 5 Days):**
        {recent_prices}
        
        **Key Financials:**
        {financials}
        
        Please provide:
        1. A table of the key financial metrics.
        2. A brief analysis of the recent price trend.
        3. An evaluation of the company's fundamental health based on the metrics.
        4. A final signal (BUY/SELL/HOLD) with reasoning.
        
        Format the output as a clean Markdown section starting with '## 1. MARKET ANALYST REPORT'.
        **Remember: The output must be in Thai.**
        """
        
        self.log(f"Asking LLM to analyze {ticker}...")
        report = self.call_llm(system_prompt, user_prompt)
        
        # Extract signal
        signal = "HOLD"
        if "BUY" in report.upper() and "SELL" not in report.upper():
            signal = "BUY"
        elif "SELL" in report.upper() and "BUY" not in report.upper():
            signal = "SELL"
            
        return {
            "signal": signal,
            "report_section": report
        }
