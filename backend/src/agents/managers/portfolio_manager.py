from src.agents.base_agent import BaseAgent

class PortfolioManager(BaseAgent):
    def __init__(self):
        super().__init__("PortfolioManager")

    def decide(self, ticker: str, market_data: dict, fundamentals_data: dict, 
               news_data: dict, social_data: dict, risk_data: dict,
               bull_data: dict, bear_data: dict, debate_data: dict, 
               risk_judgment_data: dict) -> dict:
        """
        Make the final portfolio decision based on all analysis and debate results.
        """
        self.log(f"Reviewing all reports and debate results for {ticker}...")
        
        # Extract report sections safely
        market_report = market_data.get("report_section", "")
        fundamentals_report = fundamentals_data.get("report_section", "")
        news_report = news_data.get("report_section", "")
        social_report = social_data.get("report_section", "")
        risk_report = risk_data.get("report_section", "")
        
        bull_report = bull_data.get("report_section", "")
        bear_report = bear_data.get("report_section", "")
        debate_report = debate_data.get("report_section", "")
        risk_judgment_report = risk_judgment_data.get("report_section", "")
        
        system_prompt = """You are a Portfolio Manager with final decision-making authority.
Your goal is to synthesize ALL analysis, debates, and risk assessments to make a profitable yet prudent investment decision.

Your Inputs:
1. Technical & Fundamental Analysis
2. Sentiment Analysis (News & Social)
3. Bull vs Bear Debate (The arguments)
4. Debate Verdict (Who won?)
5. Risk Debate Judgment (Is the risk acceptable?)

Your Task:
- Weigh the evidence holistically.
- If the debate was heated but one side won clearly, respect that validict.
- If the risk judgment suggests "TOO RISKY", be very cautious about buying.
- Write entirely in Thai.
- Conclude with a clear ACTION: BUY, SELL, or HOLD."""
        
        user_prompt = f"""
Make your Final Decision for {ticker} based on this dossier:

=== 1. CORE ANALYSIS ===
Market: {market_report[:500]}...
Fundamentals: {fundamentals_report[:500]}...
News/Social: {news_report[:300]}... {social_report[:300]}...

=== 2. BULL VS BEAR DEBATE ===
Bull Case: {bull_report[:500]}...
Bear Case: {bear_report[:500]}...
Moderator Verdict: {debate_report}

=== 3. RISK ASSESSMENT ===
Risk Report: {risk_report[:500]}...
Risk Debate Judgment: {risk_judgment_report}

=== YOUR DECISION ===
Please provide:
1. **บทสรุปผู้บริหาร (Executive Summary)**: synthesis of the strongest points from all sides.
2. **การประเมินความเสี่ยง (Risk Evaluation)**: strictly based on the Risk Judgment.
3. **กลยุทธ์แนะนำ (Recommended Strategy)**: Action (BUY/SELL/HOLD), Entry Price, Target Price, Stop Loss (if applicable).
4. **เหตุผลประกอบ (Rationale)**: Why this decision?

Format the output as a clean Markdown section starting with '## 💼 PORTFOLIO MANAGER DECISION'.
"""
        
        self.log(f"Asking LLM to make final decision for {ticker}...")
        report = self.call_llm(system_prompt, user_prompt)
        
        # Extract decision
        decision = "HOLD"
        report_upper = report.upper()
        if "ACTION: BUY" in report_upper or "**BUY**" in report_upper or "RECOMMENDATION: BUY" in report_upper:
            decision = "BUY"
        elif "ACTION: SELL" in report_upper or "**SELL**" in report_upper or "RECOMMENDATION: SELL" in report_upper:
            decision = "SELL"
            
        return {
            "decision": decision,
            "report_section": report
        }
