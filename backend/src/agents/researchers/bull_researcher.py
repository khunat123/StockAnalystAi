"""
Bull Researcher Agent - Optimistic viewpoint analyst.
Focuses on growth opportunities and bullish catalysts.
"""
from src.agents.base_agent import BaseAgent


class BullResearcher(BaseAgent):
    """
    Agent that focuses on finding positive aspects and growth opportunities.
    Argues the bullish case for a stock.
    """
    
    def __init__(self):
        super().__init__("BullResearcher")
    
    def analyze(self, ticker: str, market_data: dict, fundamentals_data: dict, 
                news_data: dict) -> dict:
        """
        Analyze data with a bullish perspective.
        """
        self.log(f"Analyzing bullish case for {ticker}...")
        
        # Extract relevant sections
        market_report = market_data.get("report_section", "No market data available")
        fundamentals_report = fundamentals_data.get("report_section", "No fundamentals data available")
        news_report = news_data.get("report_section", "No news data available")
        
        system_prompt = """You are a Bull Analyst advocating for investing in this stock.
Your task is to build a strong, evidence-based bullish case.

**Style Guidelines:**
- Write in a conversational, persuasive tone
- Focus on storytelling with data support
- Don't just list points - explain WHY they matter
- Be confident but not arrogant
- Write entirely in Thai
- Keep it concise but impactful"""
        
        user_prompt = f"""
Build the STRONGEST BULLISH CASE for {ticker}:

=== AVAILABLE DATA ===
Market Analysis:
{market_report}

Fundamentals:
{fundamentals_report}

News:
{news_report}

=== YOUR BULLISH ARGUMENT ===
Write a compelling bullish thesis covering:

1. **ข้อมูลสนับสนุนขาขึ้น (Bullish Arguments)**
   Highlight growth potential, competitive advantages, and positive indicators.
   Cite specific data from the reports.

2. **ตัวเร่งการเติบโต (Growth Catalysts)**
   What upcoming events or trends could drive the stock up?

3. **การประเมินมูลค่า (Valuation Assessment)**
   Why might the stock be undervalued or fairly valued for its growth?

4. **สรุปและคำแนะนำ (Summary)**
   Wrap up your bullish thesis in 2-3 persuasive sentences.

5. **ความเชื่อมั่น (Confidence Score)**
   End with: "Confidence: X.XX" (0.0 to 1.0)

Format as Markdown starting with '## 🐂 BULL RESEARCHER REPORT'
"""
        
        self.log(f"Generating bullish thesis for {ticker}...")
        report = self.call_llm(system_prompt, user_prompt)
        
        # Extract confidence score
        confidence = self._extract_confidence(report)
        
        return {
            "stance": "BULLISH",
            "confidence": confidence,
            "report_section": report
        }
    
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
        
        return 0.7  # Default bullish confidence
