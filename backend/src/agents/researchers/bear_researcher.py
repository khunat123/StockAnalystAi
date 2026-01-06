"""
Bear Researcher Agent - Pessimistic viewpoint analyst.
Focuses on risks, downsides, and bearish signals.
"""
from src.agents.base_agent import BaseAgent


class BearResearcher(BaseAgent):
    """
    Agent that focuses on finding risks and negative aspects.
    Argues the bearish case for a stock.
    """
    
    def __init__(self):
        super().__init__("BearResearcher")
    
    def analyze(self, ticker: str, market_data: dict, fundamentals_data: dict, 
                news_data: dict, risk_data: dict) -> dict:
        """
        Analyze data with a bearish perspective.
        """
        self.log(f"Analyzing bearish case for {ticker}...")
        
        # Extract relevant sections
        market_report = market_data.get("report_section", "No market data available")
        fundamentals_report = fundamentals_data.get("report_section", "No fundamentals data available")
        news_report = news_data.get("report_section", "No news data available")
        risk_report = risk_data.get("report_section", "No risk data available")
        
        system_prompt = """You are a Bear Analyst making the case AGAINST investing in this stock.
Your task is to present well-reasoned bearish arguments.

**Style Guidelines:**
- Write in a critical but fair tone
- Focus on real risks, not fear-mongering
- Explain WHY certain factors are concerning
- Be specific with data citations
- Write entirely in Thai
- Be concise but thorough"""
        
        user_prompt = f"""
Build the STRONGEST BEARISH CASE for {ticker}:

=== AVAILABLE DATA ===
Market Analysis:
{market_report}

Fundamentals:
{fundamentals_report}

News:
{news_report}

Risk Analysis:
{risk_report}

=== YOUR BEARISH ARGUMENT ===
Write a critical bearish thesis covering:

1. **ข้อมูลสนับสนุนขาลง (Bearish Arguments)**
   Highlight risks, challenges, and negative indicators.
   Cite specific data from the reports.

2. **ความเสี่ยงที่สำคัญ (Key Risks)**
   What major factors could hurt this stock?

3. **การประเมินมูลค่า (Valuation Concerns)**
   Why might the stock be overvalued?

4. **Red Flags และสัญญาณเตือน (Warning Signs)**
   Point out any concerning patterns or risks.

5. **สรุปและคำแนะนำ (Summary)**
   Wrap up your bearish thesis in 2-3 sentences.

6. **ความเชื่อมั่น (Confidence Score)**
   End with: "Confidence: X.XX" (0.0 to 1.0)

Format as Markdown starting with '## 🐻 BEAR RESEARCHER REPORT'
"""
        
        self.log(f"Generating bearish thesis for {ticker}...")
        report = self.call_llm(system_prompt, user_prompt)
        
        # Extract confidence score
        confidence = self._extract_confidence(report)
        
        return {
            "stance": "BEARISH",
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
        
        return 0.6  # Default bearish confidence
