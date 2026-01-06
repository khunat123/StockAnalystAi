"""
Risk Analyst - Risk assessment and volatility analysis
"""

from src.agents.base_agent import BaseAgent
from src.data.tools.data_tools import get_stock_data, get_financials


class RiskAnalyst(BaseAgent):
    """Assesses investment risk profile"""
    
    def __init__(self):
        super().__init__("RiskAnalyst")

    def analyze(self, ticker: str) -> dict:
        """
        Analyze risk profile
        
        Args:
            ticker: Stock symbol
            
        Returns:
            dict with risk_level and report_section
        """
        self.log(f"Assessing risk profile for {ticker}...")
        
        # Fetch data
        hist_data = get_stock_data(ticker)
        financials = get_financials(ticker)
        
        # Calculate volatility
        volatility = hist_data['Close'].pct_change().std() * (252 ** 0.5) if not hist_data.empty else 0
        
        system_prompt = """You are a Risk Management Specialist. 
        Your job is to assess the risks associated with investing in a specific stock.
        Consider volatility, market conditions, and company-specific risks.
        **IMPORTANT: Write the entire report in Thai language.**
        Use Markdown formatting.
        Conclude with a risk level: LOW, MEDIUM, or HIGH."""
        
        user_prompt = f"""
        Analyze the risk profile for {ticker}:
        
        **Annualized Volatility (Estimated):** {volatility:.2%}
        
        **Key Financials:**
        {financials}
        
        Please provide:
        1. An analysis of Market Risk (Beta, Volatility).
        2. An analysis of Company Risk (Debt, Earnings Stability).
        3. A final risk assessment (LOW/MEDIUM/HIGH) with mitigation strategies.
        
        Format the output as a clean Markdown section starting with '## 5. RISK ANALYST REPORT'.
        **Remember: The output must be in Thai.**
        """
        
        self.log(f"Asking LLM to analyze risk for {ticker}...")
        report = self.call_llm(system_prompt, user_prompt)
        
        # Extract signal
        risk_level = "MEDIUM"
        if "HIGH" in report.upper():
            risk_level = "HIGH"
        elif "LOW" in report.upper():
            risk_level = "LOW"
            
        return {
            "risk_level": risk_level,
            "report_section": report
        }
