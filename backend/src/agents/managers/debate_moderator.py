"""
Debate Moderator Agent - Synthesizes Bull vs Bear arguments.
Weighs competing viewpoints and produces balanced summary.
"""
from src.agents.base_agent import BaseAgent


class DebateModerator(BaseAgent):
    """
    Agent that moderates the debate between Bull and Bear researchers.
    Produces a balanced synthesis of competing viewpoints.
    """
    
    def __init__(self):
        super().__init__("DebateModerator")
    
    def moderate(self, ticker: str, bull_report: dict, bear_report: dict) -> dict:
        """
        Moderate the debate between bull and bear researchers.
        """
        self.log(f"Moderating Bull vs Bear debate for {ticker}...")
        
        bull_content = bull_report.get("report_section", "")
        bear_content = bear_report.get("report_section", "")
        bull_confidence = bull_report.get("confidence", 0.5)
        bear_confidence = bear_report.get("confidence", 0.5)
        
        system_prompt = """You are a Debate Moderator - an impartial financial analyst.
Your role is to fairly evaluate both bullish and bearish arguments
and determine which side makes the stronger case.

**Style Guidelines:**
- Be objective and balanced
- Focus on the quality of arguments, not just confidence
- Acknowledge valid points from both sides
- Write entirely in Thai
- Keep it concise"""
        
        user_prompt = f"""
Review the Bull vs Bear debate for {ticker}:

=== 🐂 BULL RESEARCHER (Confidence: {bull_confidence:.2f}) ===
{bull_content}

---

=== 🐻 BEAR RESEARCHER (Confidence: {bear_confidence:.2f}) ===
{bear_content}

---

Provide a balanced moderation:

1. **สรุปข้อโต้แย้งฝั่ง Bull (Bull Summary)**
   Key points the bull side made well

2. **สรุปข้อโต้แย้งฝั่ง Bear (Bear Summary)**
   Key points the bear side made well

3. **การประเมินข้อโต้แย้ง (Argument Assessment)**
   - Which side presents stronger evidence?
   - What are the key uncertainties?

4. **จุดที่ทั้งสองฝ่ายเห็นตรงกัน (Points of Agreement)**
   Any areas where both sides agree

5. **ผลการอภิปราย (Debate Verdict)**
   State clearly: BULL_WINS, BEAR_WINS, or DRAW
   Brief explanation why

6. **ความเชื่อมั่นในผล (Confidence in Verdict)**
   End with: "Confidence: X.XX" (0.0 to 1.0)

Format as Markdown starting with '## ⚖️ DEBATE MODERATOR REPORT'
"""
        
        self.log(f"Synthesizing debate for {ticker}...")
        report = self.call_llm(system_prompt, user_prompt)
        
        # Determine winner
        verdict = self._determine_verdict(report, bull_confidence, bear_confidence)
        confidence = self._extract_confidence(report)
        
        return {
            "verdict": verdict,
            "bull_confidence": bull_confidence,
            "bear_confidence": bear_confidence,
            "debate_confidence": confidence,
            "report_section": report
        }
    
    def _determine_verdict(self, report: str, bull_conf: float, bear_conf: float) -> str:
        """Determine debate winner from report."""
        report_upper = report.upper()
        
        if "BULL_WINS" in report_upper or "BULL WINS" in report_upper:
            return "BULL_WINS"
        elif "BEAR_WINS" in report_upper or "BEAR WINS" in report_upper:
            return "BEAR_WINS"
        elif "DRAW" in report_upper:
            return "DRAW"
        
        # Fall back to confidence comparison
        diff = bull_conf - bear_conf
        if diff > 0.15:
            return "BULL_WINS"
        elif diff < -0.15:
            return "BEAR_WINS"
        else:
            return "DRAW"
    
    def _extract_confidence(self, report: str) -> float:
        """Extract confidence score from report."""
        import re
        
        patterns = [
            r'[Cc]onfidence[:\s]+([0-9]*\.?[0-9]+)',
            r'ความเชื่อมั่น[:\s]+([0-9]*\.?[0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, report)
            if match:
                try:
                    score = float(match.group(1))
                    if score > 1.0:
                        score = score / 100.0
                    return min(max(score, 0.0), 1.0)
                except ValueError:
                    pass
        
        return 0.5
