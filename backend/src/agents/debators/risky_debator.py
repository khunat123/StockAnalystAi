"""
Risky Debator Agent - Advocates for aggressive, high-risk strategies.
Part of the 3-way Risk Debate system.
"""
from src.agents.base_agent import BaseAgent


class RiskyDebator(BaseAgent):
    """
    Agent that advocates for aggressive, high-risk investment strategies.
    Focuses on maximum potential gains even with higher volatility.
    """
    
    def __init__(self):
        super().__init__("RiskyDebator")
    
    def debate(self, ticker: str, market_data: dict, fundamentals_data: dict,
               news_data: dict, debate_history: str = "") -> dict:
        """
        Present aggressive risk-taking arguments.
        
        Args:
            ticker: Stock ticker symbol
            market_data: Technical analysis data
            fundamentals_data: Company financial data
            news_data: Recent news data
            debate_history: Previous debate exchanges
            
        Returns:
            Dictionary with risky perspective and arguments
        """
        self.log(f"Presenting RISKY perspective for {ticker}...")
        
        market_report = market_data.get("report_section", "")
        fundamentals_report = fundamentals_data.get("report_section", "")
        news_report = news_data.get("report_section", "")
        
        system_prompt = """You are a RISKY/AGGRESSIVE Analyst in a risk debate.
Your role is to advocate for high-risk, high-reward investment strategies.

Your perspective:
- Fortune favors the bold - big risks lead to big rewards
- Market timing and momentum are key opportunities
- Conservative approaches miss the best gains
- Volatility creates opportunity, not just risk

**IMPORTANT:**
- Be persuasive and engaging, like a real debate
- Counter the conservative viewpoints with specific data
- Focus on potential upside and growth opportunities
- Write in Thai language
- Output conversationally as if speaking, no special formatting"""

        user_prompt = f"""
คุณกำลังอภิปรายเรื่องความเสี่ยงในการลงทุน {ticker}

ข้อมูลที่มี:
- Market Analysis: {market_report[:1000]}
- Fundamentals: {fundamentals_report[:1000]}
- News: {news_report[:1000]}

ประวัติการอภิปราย:
{debate_history if debate_history else "ยังไม่มีการอภิปราย - คุณพูดก่อน"}

กรุณานำเสนอมุมมอง RISKY/AGGRESSIVE ของคุณ:
1. ทำไมควรเสี่ยง - โอกาสทำกำไรสูง
2. ข้อโต้แย้งต่อฝ่ายอนุรักษ์นิยม
3. ตัวอย่างจากข้อมูลที่สนับสนุนการเสี่ยง
4. สรุปจุดยืน

พูดแบบกำลังโต้วาทีจริงๆ ไม่ต้องมี format พิเศษ
"""
        
        self.log("Generating risky argument...")
        response = self.call_llm(system_prompt, user_prompt)
        
        return {
            "stance": "RISKY",
            "argument": response,
            "report_section": f"## 🔥 นักวิเคราะห์ฝ่ายเสี่ยงสูง (Risky Analyst)\n\n{response}"
        }
