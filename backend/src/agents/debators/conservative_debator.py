"""
Conservative Debator Agent - Advocates for safe, low-risk strategies.
Part of the 3-way Risk Debate system.
"""
from src.agents.base_agent import BaseAgent


class ConservativeDebator(BaseAgent):
    """
    Agent that advocates for conservative, low-risk investment strategies.
    Prioritizes capital preservation and downside protection.
    """
    
    def __init__(self):
        super().__init__("ConservativeDebator")
    
    def debate(self, ticker: str, market_data: dict, fundamentals_data: dict,
               news_data: dict, risk_data: dict, risky_argument: str = "",
               debate_history: str = "") -> dict:
        """
        Present conservative, risk-averse arguments.
        
        Args:
            ticker: Stock ticker symbol
            market_data: Technical analysis data
            fundamentals_data: Company financial data
            news_data: Recent news data
            risk_data: Risk analysis data
            risky_argument: Latest argument from risky debator
            debate_history: Previous debate exchanges
            
        Returns:
            Dictionary with conservative perspective and arguments
        """
        self.log(f"Presenting CONSERVATIVE/SAFE perspective for {ticker}...")
        
        market_report = market_data.get("report_section", "")
        fundamentals_report = fundamentals_data.get("report_section", "")
        news_report = news_data.get("report_section", "")
        risk_report = risk_data.get("report_section", "")
        
        system_prompt = """You are a CONSERVATIVE/SAFE Analyst in a risk debate.
Your role is to advocate for cautious, low-risk investment strategies.

Your perspective:
- Capital preservation is the top priority
- "First, do no harm" - avoid losses before seeking gains
- High volatility is dangerous, not opportunity
- Patience and discipline beat speculation

**IMPORTANT:**
- Counter the aggressive viewpoints with risk data
- Emphasize potential downsides and losses
- Focus on protecting capital
- Write in Thai language
- Output conversationally as if speaking, no special formatting"""

        user_prompt = f"""
คุณกำลังอภิปรายเรื่องความเสี่ยงในการลงทุน {ticker}

ข้อมูลที่มี:
- Market Analysis: {market_report[:800]}
- Fundamentals: {fundamentals_report[:800]}
- News: {news_report[:800]}
- Risk Analysis: {risk_report[:800]}

ข้อโต้แย้งจากฝ่ายเสี่ยงสูง:
{risky_argument[:500] if risky_argument else "ยังไม่มี"}

กรุณานำเสนอมุมมอง CONSERVATIVE/SAFE ของคุณ:
1. ความเสี่ยงที่ต้องระวัง
2. ทำไมการเสี่ยงสูงอันตราย
3. ข้อโต้แย้งต่อฝ่ายเสี่ยง
4. ข้อเสนอที่ปลอดภัยกว่า
5. สรุปจุดยืน

พูดแบบกำลังโต้วาทีจริงๆ ไม่ต้องมี format พิเศษ
"""
        
        self.log("Generating conservative argument...")
        response = self.call_llm(system_prompt, user_prompt)
        
        return {
            "stance": "CONSERVATIVE",
            "argument": response,
            "report_section": f"## 🛡️ นักวิเคราะห์ฝ่ายอนุรักษ์นิยม (Conservative Analyst)\n\n{response}"
        }
