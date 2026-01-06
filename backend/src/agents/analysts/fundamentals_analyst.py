"""
Fundamentals Analyst - Financial statement and ratio analysis
"""

from src.agents.base_agent import BaseAgent
from src.data.tools.data_tools import get_financials, get_detailed_financials


class FundamentalsAnalyst(BaseAgent):
    """Analyzes financial statements and fundamental metrics"""
    
    def __init__(self):
        super().__init__("FundamentalsAnalyst")

    def analyze(self, ticker: str) -> dict:
        """
        Analyze company financials and fundamental health
        
        Args:
            ticker: Stock symbol
            
        Returns:
            dict with signal and report_section
        """
        self.log(f"Fetching financial data for {ticker}...")
        
        # Fetch real data
        key_metrics = get_financials(ticker)
        detailed_fin = get_detailed_financials(ticker)
        
        # Check if this is a crypto asset
        is_crypto = ticker.endswith("-USD") or ticker.endswith("-USDT")
        
        # Check for missing data
        data_warning = ""
        if key_metrics.get("Market Cap") == "N/A" and not is_crypto:
            data_warning = "\n**WARNING: Key financial data is missing. The ticker symbol might be incorrect.**\n"

        if is_crypto:
            system_prompt = """You are a professional Cryptocurrency Analyst. 
            Your job is to analyze crypto assets based on market data.
            **IMPORTANT: Write the entire report in Thai language.**
            Use Markdown formatting with tables.
            Conclude with an outlook: BULLISH, BEARISH, or NEUTRAL."""
            
            user_prompt = f"""
            Analyze the following cryptocurrency data for {ticker}:
            
            **Key Metrics:**
            {key_metrics}
            
            Please provide:
            1. An analysis of Market Cap and its significance.
            2. An analysis of recent price trends and volatility.
            3. A discussion of adoption and network effects (if applicable).
            4. A final verdict (BULLISH/BEARISH/NEUTRAL) with reasoning.
            
            Format the output as a clean Markdown section starting with '## 2. FUNDAMENTALS ANALYST REPORT'.
            **Remember: The output must be in Thai.**
            """
        else:
            system_prompt = """You are a professional Fundamental Analyst. 
            Your job is to analyze the company's financial statements and key metrics.
            Focus on profitability, growth, health (debt/liquidity), and valuation.
            **IMPORTANT: Write the entire report in Thai language.**
            Use Markdown formatting with tables.
            Conclude with a fundamental outlook: BULLISH, BEARISH, or NEUTRAL."""
            
            user_prompt = f"""
            Analyze the following financial data for {ticker}:
            
            {data_warning}
            
            **Key Metrics:**
            {key_metrics}
            
            **Income Statement (Recent):**
            {detailed_fin.get('income_statement', 'N/A')}
            
            **Balance Sheet (Recent):**
            {detailed_fin.get('balance_sheet', 'N/A')}
            
            **Cash Flow (Recent):**
            {detailed_fin.get('cash_flow', 'N/A')}
            
            Please provide:
            1. An analysis of Profitability (Margins, ROE).
            2. An analysis of Financial Health (Debt, Liquidity).
            3. An analysis of Valuation (PE, PEG vs Peers if implied).
            4. A final fundamental verdict (BULLISH/BEARISH/NEUTRAL) with reasoning.
            
            Format the output as a clean Markdown section starting with '## 2. FUNDAMENTALS ANALYST REPORT'.
            **Remember: The output must be in Thai.**
            """
        
        self.log(f"Asking LLM to analyze financials for {ticker}...")
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
