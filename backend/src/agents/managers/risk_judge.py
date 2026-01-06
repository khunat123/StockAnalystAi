"""
Risk Judge Agent - Evaluates the 3-way risk debate and makes final decision.
Part of the Risk Debate system.
"""
from src.agents.base_agent import BaseAgent


class RiskJudge(BaseAgent):
    """
    Agent that judges the risk debate between Risky, Neutral, and Conservative analysts.
    Makes the final trading decision based on all arguments.
    """
    
    def __init__(self):
        super().__init__("RiskJudge")
    
    def judge(self, ticker: str, risky_result: dict, neutral_result: dict,
              conservative_result: dict, trader_plan: str = "") -> dict:
        """
        Judge the risk debate and make final decision.
        
        Args:
            ticker: Stock ticker symbol
            risky_result: Arguments from risky debator
            neutral_result: Arguments from neutral debator
            conservative_result: Arguments from conservative debator
            trader_plan: Original trading plan from portfolio manager
            
        Returns:
            Dictionary with final verdict and reasoning
        """
        self.log(f"Judging risk debate for {ticker}...")
        
        risky_argument = risky_result.get("argument", "")
        neutral_argument = neutral_result.get("argument", "")
        conservative_argument = conservative_result.get("argument", "")
        
        system_prompt = """You are the Risk Management Judge.
Your role is to evaluate the debate between three risk analysts and make a CLEAR decision.

Rules:
1. You MUST give a clear verdict: BUY, SELL, or HOLD
2. Do NOT choose HOLD just because all sides seem valid - be decisive
3. Summarize the strongest points from each analyst
4. Explain your reasoning clearly
5. Provide an adjusted trading recommendation

**IMPORTANT:**
- Be decisive - traders need clear direction
- Base your decision on the strength of arguments
- Write in Thai language"""

        user_prompt = f"""
คุณเป็นผู้พิพากษาการอภิปรายเรื่องความเสี่ยงสำหรับ {ticker}

=== 🔥 ฝ่ายเสี่ยงสูง (Risky) ===
{risky_argument}

=== ⚖️ ฝ่ายสายกลาง (Neutral) ===
{neutral_argument}

=== 🛡️ ฝ่ายอนุรักษ์นิยม (Conservative) ===
{conservative_argument}

แผนเดิมจาก Trader: {trader_plan if trader_plan else "ยังไม่มี"}

---

กรุณาตัดสิน:

1. **สรุปประเด็นสำคัญจากแต่ละฝ่าย**
   - ฝ่ายเสี่ยง: [จุดแข็งที่สุด]
   - ฝ่ายกลาง: [จุดแข็งที่สุด]
   - ฝ่ายอนุรักษ์: [จุดแข็งที่สุด]

2. **ฝ่ายที่มีเหตุผลแข็งแกร่งที่สุด**: [ระบุ]

3. **คำตัดสิน**: [BUY / SELL / HOLD]

4. **เหตุผลโดยละเอียด**:
   - ทำไมถึงเลือกคำตัดสินนี้

5. **คำแนะนำเพิ่มเติม**:
   - ควรทำอย่างไร, position size แนะนำ, stop loss ฯลฯ

จงตัดสินใจอย่างชัดเจน!
"""
        
        self.log("Making final judgment...")
        
        # Try to get LLM response with fallback
        try:
            response = self.call_llm(system_prompt, user_prompt)
            # Check if response is empty or None (can happen with safety filters)
            if not response or len(response.strip()) < 50:
                raise ValueError("Empty or too short response from LLM")
        except Exception as e:
            self.log(f"LLM call failed, using fallback: {e}")
            response = f"""## ⚡ การตัดสินอัตโนมัติ (Fallback)

เนื่องจากระบบไม่สามารถวิเคราะห์ได้อย่างสมบูรณ์ ขอแนะนำ:

**คำตัดสิน: HOLD**

**เหตุผล:**
- ควรรอข้อมูลเพิ่มเติมก่อนตัดสินใจ
- พิจารณาปัจจัยพื้นฐานและเทคนิคัลร่วมกัน
- ปรึกษานักวิเคราะห์เพิ่มเติมก่อนลงทุน

**ฝ่ายที่มีเหตุผลแข็งแกร่งที่สุด:** NEUTRAL (สายกลาง)

**คำแนะนำ:**
- หากต้องการลงทุน ควรเริ่มด้วย position size เล็กๆ
- ตั้ง stop loss เสมอ
- ติดตามข่าวสารอย่างใกล้ชิด
"""
        
        # Extract decision
        decision = "HOLD"
        response_upper = response.upper()
        if "BUY" in response_upper and "SELL" not in response_upper:
            decision = "BUY"
        elif "SELL" in response_upper and "BUY" not in response_upper:
            decision = "SELL"
        
        # Determine which side won
        winning_side = "NEUTRAL"
        if "เสี่ยง" in response and "แข็งแกร่ง" in response:
            winning_side = "RISKY"
        elif "อนุรักษ์" in response and "แข็งแกร่ง" in response:
            winning_side = "CONSERVATIVE"
        
        return {
            "decision": decision,
            "winning_side": winning_side,
            "verdict": response,
            "report_section": f"## ⚖️ คำตัดสินของผู้พิพากษา (Risk Judge)\n\n{response}"
        }
