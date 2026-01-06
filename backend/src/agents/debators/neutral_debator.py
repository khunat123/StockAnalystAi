"""
Neutral Debator Agent - Advocates for balanced, moderate strategies.
Part of the 3-way Risk Debate system.
"""
from src.agents.base_agent import BaseAgent


class NeutralDebator(BaseAgent):
    """
    Agent that advocates for balanced, moderate risk strategies.
    Seeks the middle ground between aggressive and conservative.
    """
    
    def __init__(self):
        super().__init__("NeutralDebator")
    
    def debate(self, ticker: str, market_data: dict, fundamentals_data: dict,
               news_data: dict, risky_argument: str = "", safe_argument: str = "",
               debate_history: str = "") -> dict:
        """
        Present balanced, moderate arguments.
        
        Args:
            ticker: Stock ticker symbol
            market_data: Technical analysis data
            fundamentals_data: Company financial data
            news_data: Recent news data
            risky_argument: Latest argument from risky debator
            safe_argument: Latest argument from safe debator
            debate_history: Previous debate exchanges
            
        Returns:
            Dictionary with neutral perspective and arguments
        """
        self.log(f"Presenting NEUTRAL perspective for {ticker}...")
        
        market_report = market_data.get("report_section", "")
        fundamentals_report = fundamentals_data.get("report_section", "")
        news_report = news_data.get("report_section", "")
        
        system_prompt = """You are a NEUTRAL/BALANCED Analyst in a risk debate.
Your role is to advocate for moderate, balanced investment strategies.

Your perspective:
- Balance is key - neither too risky nor too conservative
- Diversification and position sizing matter
- Both upside potential and downside protection are important
- Data-driven decisions beat emotional extremes

**IMPORTANT:**
- Engage with both risky and safe arguments
- Point out weaknesses in both extreme positions
- Advocate for the middle ground with specific reasoning
- Write in Thai language
- Output conversationally as if speaking, no special formatting"""

        user_prompt = f"""
คุณกำลังอภิปรายเรื่องความเสี่ยงในการลงทุน {ticker}

ข้อมูลที่มี:
- Market Analysis: {market_report[:800]}
- Fundamentals: {fundamentals_report[:800]}
- News: {news_report[:800]}

ข้อโต้แย้งจากฝ่ายเสี่ยงสูง:
{risky_argument[:500] if risky_argument else "ยังไม่มี"}

ข้อโต้แย้งจากฝ่ายอนุรักษ์นิยม:
{safe_argument[:500] if safe_argument else "ยังไม่มี"}

กรุณานำเสนอมุมมอง NEUTRAL/BALANCED ของคุณ:
1. จุดแข็งและจุดอ่อนของทั้งสองฝ่าย
2. ทำไมแนวทางสายกลางดีกว่า
3. ข้อเสนอที่สมดุล - ทั้งโอกาสและความเสี่ยง
4. สรุปจุดยืน

พูดแบบกำลังโต้วาทีจริงๆ ไม่ต้องมี format พิเศษ
"""
        
        self.log("Generating neutral argument...")
        response = self.call_llm(system_prompt, user_prompt)
        
        return {
            "stance": "NEUTRAL",
            "argument": response,
            "report_section": f"## ⚖️ นักวิเคราะห์สายกลาง (Neutral Analyst)\n\n{response}"
        }
