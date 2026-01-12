import asyncio
from typing import TypedDict, Dict, Any, List
from langgraph.graph import StateGraph, END

# Import existing agents
from src.agents.analysts import (
    MarketAnalyst, FundamentalsAnalyst, NewsAnalyst, SocialAnalyst, RiskAnalyst, CryptoAnalyst
)
from src.agents.researchers.bull_researcher import BullResearcher
from src.agents.researchers.bear_researcher import BearResearcher
from src.agents.managers.debate_moderator import DebateModerator
from src.agents.managers.portfolio_manager import PortfolioManager
from src.agents.managers.risk_judge import RiskJudge
from src.agents.debators import RiskyDebator, NeutralDebator, ConservativeDebator
from src.data.tools import is_crypto

# Initialize agents securely
market_analyst = MarketAnalyst()
fundamentals_analyst = FundamentalsAnalyst()
news_analyst = NewsAnalyst()
social_analyst = SocialAnalyst()
risk_analyst = RiskAnalyst()
bull_researcher = BullResearcher()
bear_researcher = BearResearcher()
debate_moderator = DebateModerator()
portfolio_manager = PortfolioManager()
risky_debator = RiskyDebator()
neutral_debator = NeutralDebator()
conservative_debator = ConservativeDebator()
risk_judge = RiskJudge()
crypto_analyst = CryptoAnalyst()

class AgentState(TypedDict):
    ticker: str
    is_crypto: bool
    market_data: Dict[str, Any]
    fundamentals_data: Dict[str, Any]
    news_data: Dict[str, Any]
    social_data: Dict[str, Any]
    risk_data: Dict[str, Any]
    crypto_data: Dict[str, Any]
    bull_analysis: Dict[str, Any]
    bear_analysis: Dict[str, Any]
    debate_outcome: Dict[str, Any]
    risk_judgment: Dict[str, Any]
    final_decision: Dict[str, Any]
    final_report: str

def safe_get(result, key: str, default: str = "") -> str:
    """Safely get a value from result which could be dict or string"""
    if isinstance(result, dict):
        return result.get(key, default)
    elif isinstance(result, str):
        return result
    return default

def ensure_report_dict(result) -> Dict:
    """Ensure result is a dict for DebateModerator"""
    if isinstance(result, dict):
        return result
    return {
        "report_section": str(result),
        "confidence": 0.5
    }

async def analyze_market(state: AgentState):
    return {"market_data": market_analyst.analyze(state["ticker"])}

async def analyze_fundamentals(state: AgentState):
    return {"fundamentals_data": fundamentals_analyst.analyze(state["ticker"])}

async def analyze_news(state: AgentState):
    return {"news_data": news_analyst.analyze(state["ticker"])}

async def analyze_social(state: AgentState):
    return {"social_data": social_analyst.analyze(state["ticker"])}

async def analyze_risk(state: AgentState):
    return {"risk_data": risk_analyst.analyze(state["ticker"])}

async def analyze_crypto(state: AgentState):
    return {"crypto_data": crypto_analyst.analyze(state["ticker"])}

async def conduct_research(state: AgentState):
    """Run Bull and Bear researchers in parallel"""
    bull_task = asyncio.to_thread(
        bull_researcher.analyze, state["ticker"],
        state["market_data"], state["fundamentals_data"], state["news_data"]
    )
    bear_task = asyncio.to_thread(
        bear_researcher.analyze, state["ticker"],
        state["market_data"], state["fundamentals_data"], state["news_data"], state["risk_data"]
    )
    bull, bear = await asyncio.gather(bull_task, bear_task)
    return {"bull_analysis": bull, "bear_analysis": bear}

async def moderate_debate(state: AgentState):
    decision = debate_moderator.moderate(
        state["ticker"],
        ensure_report_dict(state["bull_analysis"]),
        ensure_report_dict(state["bear_analysis"])
    )
    return {"debate_outcome": decision}

async def judge_risk(state: AgentState):
    """Run Risk Debators sequence"""
    # 1. Risky Debator
    risky_result = risky_debator.debate(
        state["ticker"], 
        state["market_data"], state["fundamentals_data"], state["news_data"], 
        ""
    )
    risky_arg = safe_get(risky_result, "argument", "")

    # 2. Conservative Debator
    conservative_result = conservative_debator.debate(
        state["ticker"], 
        state["market_data"], state["fundamentals_data"], state["news_data"], state["risk_data"],
        risky_arg, ""
    )
    safe_arg = safe_get(conservative_result, "argument", "")

    # 3. Neutral Debator
    neutral_result = neutral_debator.debate(
        state["ticker"], 
        state["market_data"], state["fundamentals_data"], state["news_data"],
        risky_arg, safe_arg, ""
    )

    # 4. Risk Judge
    judgment = risk_judge.judge(
        state["ticker"],
        risky_result, conservative_result, neutral_result
    )
    
    return {"risk_judgment": judgment}

async def make_final_decision(state: AgentState):
    decision = portfolio_manager.decide(
        state["ticker"],
        state["market_data"], state["fundamentals_data"], state["news_data"], 
        state["social_data"], state["risk_data"],
        state["bull_analysis"], state["bear_analysis"], 
        state["debate_outcome"], state["risk_judgment"]
    )
    return {"final_decision": decision}

def build_report_node(state: AgentState):
    from backend.api.openai_server import build_report # Import helper to reuse logic or we can move it
    # Re-implementing build_report logic briefly here to avoid circular imports if possible, 
    # but reusing is better. For now let's duplicate the simple string formatting or import if we move it to utils.
    # We will assume we move build_report to a shared util or keep it here.
    # Let's import from a new utils file if we refactor, but for now let's just format it here.
    
    # We will modify openai_server to import this graph, so we shouldn't import openai_server here to avoid circular dep.
    # We will return the decision and let the server build the report string, OR build it here.
    # State needs 'final_report'
    
    # Simple reconstruction of build_report logic
    from datetime import datetime
    ticker = state["ticker"]
    final_decision = state["final_decision"].get("decision", "HOLD")
    
    sections = [
        f"# 📊 รายงานการวิเคราะห์หุ้น {ticker}",
        f"\n**วันที่วิเคราะห์:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"\n**คำตัดสินสุดท้าย:** {final_decision}",
        "\n---",
        state["market_data"].get("report_section", ""),
        "\n---",
        state["fundamentals_data"].get("report_section", ""),
        "\n---",
        state["news_data"].get("report_section", ""),
        "\n---",
        state["social_data"].get("report_section", ""),
        "\n---",
        state["risk_data"].get("report_section", ""),
        "\n---",
        state["bull_analysis"].get("report_section", ""),
        "\n---",
        state["bear_analysis"].get("report_section", ""),
        "\n---",
        state["debate_outcome"].get("report_section", ""),
        "\n---",
        state["final_decision"].get("report_section", ""),
        "\n---",
        "\n## ⚠️ Disclaimer",
        "\n**คำเตือน:** รายงานนี้จัดทำโดย AI เพื่อเป็นข้อมูลประกอบการตัดสินใจเท่านั้น",
    ]
    return {"final_report": "\n".join(sections)}

# Define Graph
workflow = StateGraph(AgentState)

# Nodes
workflow.add_node("market_analyst", analyze_market)
workflow.add_node("fundamentals_analyst", analyze_fundamentals)
workflow.add_node("news_analyst", analyze_news)
workflow.add_node("social_analyst", analyze_social)
workflow.add_node("risk_analyst", analyze_risk)
workflow.add_node("crypto_analyst", analyze_crypto)

workflow.add_node("researchers", conduct_research)
workflow.add_node("debate_moderator", moderate_debate)
workflow.add_node("risk_judge", judge_risk)
workflow.add_node("portfolio_manager", make_final_decision)
workflow.add_node("report_builder", build_report_node)

# Edges
def route_start(state):
    if state["is_crypto"]:
        return "crypto_flow"
    return "stock_flow"

workflow.set_conditional_entry_point(
    route_start,
    {
        "crypto_flow": "crypto_analyst",
        "stock_flow": "market_analyst"
    }
)

# Stock Flow - Parallel Analysis
workflow.add_edge("market_analyst", "researchers")
workflow.add_edge("fundamentals_analyst", "researchers")
workflow.add_edge("news_analyst", "researchers")
workflow.add_edge("social_analyst", "portfolio_manager") # Social goes direct to PM in original? No, let's check.
# Original: market, fund, news -> researchers
# Original: market, fund, news, risk -> bear
# Original: social IS used in PM.

# To simplify parallel execution in LangGraph without complex barriers:
# We can have a "gather_data" node that calls them all, OR use LangGraph's parallel support.
# LangGraph runs nodes in parallel if they share same start node.
# Let's make a "start_stock" node that fans out.
# Actually, set_conditional_entry_point can fan out if we mapped to multiple? No, it returns one.
# We will use a dummy start node for stock.

# Revised Edges for Parallelism:
# We need a "router" or just manual edges from start.
# LangGraph doesn't auto-parallelize unless we use a fan-out pattern.
# Simple way: "router" -> [mkt, fund, news, social, risk]
# Then all of them -> "aggregator" (or implementation-wise checking if all done? LangGraph handles this if we join)
# Actually, LangGraph waits for all incoming edges? No.
# We can make a single node "run_analysts" that runs asyncio.gather inside it, which is safer given the existing async code.
# This keeps the graph simpler and avoids race conditions in state updates if not handled carefully.

async def run_analysts_parallel(state: AgentState):
    results = await asyncio.gather(
        analyze_market(state),
        analyze_fundamentals(state),
        analyze_news(state),
        analyze_social(state),
        analyze_risk(state)
    )
    # Merge results
    new_state = {}
    for r in results:
        new_state.update(r)
    return new_state

workflow.add_node("run_analysts_parallel", run_analysts_parallel)

# Re-route start
def route_start_v2(state):
    if state["is_crypto"]:
        return "crypto_analyst"
    return "run_analysts_parallel"

workflow.set_conditional_entry_point(
    route_start_v2,
    {
        "crypto_analyst": "crypto_analyst",
        "run_analysts_parallel": "run_analysts_parallel"
    }
)

# Stock flow continuation
workflow.add_edge("run_analysts_parallel", "researchers")
workflow.add_edge("run_analysts_parallel", "risk_judge") # Risk debate needs data

# Researchers -> Debate
workflow.add_edge("researchers", "debate_moderator")

# Debate & Risk Judge -> PM
# We need to join them.
# Create a join node? Or just chain them?
# Researchers/Debate and RiskJudge are independent after Analysis.
# Let's serialize them to ensure state is fully populated for PM.
# Analysts -> Researchers -> Debate -> Risk Judge -> PM
# (Original: Risk debate also runs in parallel with others? No, original had Phase 1 (Data), Phase 2 (Bull/Bear), Phase 3 (Mod), Phase 4 (Risk), Phase 5 (PM))
# Original Phase 4 (Risk) comes AFTER Moderation?
# Let's check original code.
# Phase 1: Gather Data
# Phase 2: Bull/Bear (needs data)
# Phase 3: Debate Mod (needs Bull/Bear)
# Phase 4: Risk Debate (needs Data, independent of Bull/Bear)
# Phase 5: PM (needs Everything)

# So we can run Debate Branch and Risk Branch in parallel?
# Yes.
# Analysts -> [Debate Branch, Risk Branch] -> PM
# Debate Branch: Researchers -> Moderator
# Risk Branch: RiskJudge (which runs 3 debators inside)

# LangGraph join:
# PM needs input from Moderator and RiskJudge.
# If we add edges: Moderator -> PM, RiskJudge -> PM.
# PM will run when BOTH are done? LangGraph behavior: It might run twice if not configured to wait.
# We can use a "joiner" or make it sequential for safety and simplicity (as in original code it was sequential phases).
# Original code: await Phase 2, await Phase 3, await Phase 4.
# So it WAS sequential.
# Let's keep it sequential to match original exactly and avoid complexity.
# Data -> Researchers -> Moderator -> Risk Judge -> PM

workflow.add_edge("debate_moderator", "risk_judge")
workflow.add_edge("risk_judge", "portfolio_manager")
workflow.add_edge("portfolio_manager", "report_builder")
workflow.add_edge("report_builder", END)

# Crypto Flow
# Crypto Analyst -> News -> Social -> Report
# Original Crypto: Crypto -> News -> Social -> Report
async def run_crypto_rest(state: AgentState):
    # original: crypto done, then news, then social
    n = news_analyst.analyze(state["ticker"])
    s = social_analyst.analyze(state["ticker"])
    return {"news_data": n, "social_data": s}

workflow.add_node("crypto_enrichment", run_crypto_rest)
workflow.add_edge("crypto_analyst", "crypto_enrichment")

def build_crypto_report_node(state: AgentState):
    from datetime import datetime
    ticker = state["ticker"]
    sentiment = state["crypto_data"].get("sentiment", "NEUTRAL")
    
    sections = [
        f"# 💰 รายงานการวิเคราะห์ Cryptocurrency {ticker}",
        f"\n**วันที่วิเคราะห์:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"\n**สัญญาณ:** {sentiment}",
        "\n---",
        state["crypto_data"].get("report_section", ""),
        "\n---",
        state["news_data"].get("report_section", ""),
        "\n---",
        state["social_data"].get("report_section", ""),
        "\n---",
        "\n## ⚠️ Disclaimer",
        "\n**คำเตือน:** Cryptocurrency มีความผันผวนสูงมาก การลงทุนมีความเสี่ยง ควรศึกษาข้อมูลให้ดีก่อนตัดสินใจ",
        "\n**หมายเหตุ:** รายงานนี้จัดทำโดย AI เพื่อเป็นข้อมูลประกอบการตัดสินใจเท่านั้น",
    ]
    return {"final_report": "\n".join(sections), "final_decision": {"decision": sentiment}}

workflow.add_node("crypto_report", build_crypto_report_node)
workflow.add_edge("crypto_enrichment", "crypto_report")
workflow.add_edge("crypto_report", END)

app = workflow.compile()
