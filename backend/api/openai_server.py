"""
OpenAI-Compatible API Server for Ai-project
This allows Chat-UI to use our agents via standard OpenAI API format.
"""

import sys
import os
import json
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Import agents
from src.agents.analysts import (
    MarketAnalyst, FundamentalsAnalyst, NewsAnalyst, SocialAnalyst, RiskAnalyst, CryptoAnalyst
)
from src.agents.researchers.bull_researcher import BullResearcher
from src.agents.researchers.bear_researcher import BearResearcher
from src.agents.managers.debate_moderator import DebateModerator
from src.agents.managers.portfolio_manager import PortfolioManager
from src.agents.managers.risk_judge import RiskJudge
from src.agents.debators import RiskyDebator, NeutralDebator, ConservativeDebator
from src.data.tools import extract_ticker, normalize_ticker, is_crypto
from src.db import get_mongo_client

# Initialize agents
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

# MongoDB
mongo = get_mongo_client()

# Thread pool
executor = ThreadPoolExecutor(max_workers=10)

# Session context storage (for follow-up questions)
# In production, use Redis or database for multi-user support
session_context = {
    "last_ticker": None,
    "last_report": None,
    "last_analysis_data": {}  # Stores all analysis results for context
}

# FastAPI app
app = FastAPI(title="AI Stock Analyst API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Pydantic Models (OpenAI format) ============

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "stock-analyst"
    messages: List[Message]
    stream: bool = False
    temperature: float = 0.7
    max_tokens: Optional[int] = None

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int = 1700000000
    owned_by: str = "ai-project"


# ============ Helper Functions ============

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


# ============ Endpoints ============

@app.get("/")
async def root():
    return {"message": "AI Stock Analyst API - OpenAI Compatible"}


@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI format)"""
    return {
        "object": "list",
        "data": [
            {
                "id": "stock-analyst",
                "object": "model",
                "created": 1700000000,
                "owned_by": "ai-project"
            },
            {
                "id": "stock-analyst-fast",
                "object": "model", 
                "created": 1700000000,
                "owned_by": "ai-project"
            }
        ]
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """Chat completions endpoint (OpenAI format)"""
    
    # Get last user message
    user_message = ""
    for msg in reversed(request.messages):
        if msg.role == "user":
            user_message = msg.content
            break
    
    if not user_message:
        raise HTTPException(status_code=400, detail="No user message found")
    
    # Extract ticker from message
    ticker = extract_ticker(user_message)
    
    if request.stream:
        return StreamingResponse(
            stream_analysis(ticker, user_message, request.model),
            media_type="text/event-stream"
        )
    else:
        # Non-streaming response
        response_text = await run_analysis(ticker, user_message, request.model)
        return {
            "id": f"chatcmpl-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": len(user_message.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(user_message.split()) + len(response_text.split())
            }
        }


async def stream_analysis(ticker: str, user_message: str, model: str):
    """Stream the analysis response"""
    
    if not ticker:
        # No ticker found - check if we have context for follow-up questions
        if session_context["last_ticker"] and session_context["last_report"]:
            # Use LLM to answer follow-up questions based on context
            async for chunk in stream_followup_chat(user_message):
                yield chunk
            return
        else:
            yield format_sse_chunk("ไม่พบ ticker ในข้อความ กรุณาระบุหุ้นที่ต้องการวิเคราะห์ เช่น 'วิเคราะห์ AAPL'")
            yield format_sse_done()
            return
    
    ticker = normalize_ticker(ticker)
    
    # Check if this is a cryptocurrency
    if is_crypto(ticker):
        # Use crypto-specific analysis flow
        async for chunk in stream_crypto_analysis(ticker, user_message):
            yield chunk
        return
    
    # Stream progress updates (for stocks)
    yield format_sse_chunk(f"🔍 เริ่มวิเคราะห์หุ้น **{ticker}**...\n\n")
    
    loop = asyncio.get_event_loop()
    
    # Phase 1: Data Collection
    yield format_sse_chunk("📊 **Phase 1:** กำลังรวบรวมข้อมูล...\n")
    
    try:
        # Run analysts in parallel
        market_task = loop.run_in_executor(executor, market_analyst.analyze, ticker)
        fundamentals_task = loop.run_in_executor(executor, fundamentals_analyst.analyze, ticker)
        news_task = loop.run_in_executor(executor, news_analyst.analyze, ticker)
        social_task = loop.run_in_executor(executor, social_analyst.analyze, ticker)
        risk_task = loop.run_in_executor(executor, risk_analyst.analyze, ticker)
        
        market_result, fundamentals_result, news_result, social_result, risk_result = await asyncio.gather(
            market_task, fundamentals_task, news_task, social_task, risk_task
        )
        
        yield format_sse_chunk("✅ รวบรวมข้อมูลเสร็จสิ้น\n\n")
        
        # Phase 2: Bull vs Bear
        yield format_sse_chunk("🐂🐻 **Phase 2:** Bull vs Bear Debate...\n")
        
        bull_result = await loop.run_in_executor(
            executor, bull_researcher.analyze, ticker, 
            market_result, fundamentals_result, news_result
        )
        bear_result = await loop.run_in_executor(
            executor, bear_researcher.analyze, ticker,
            market_result, fundamentals_result, news_result, risk_result
        )
        
        yield format_sse_chunk("✅ Bull vs Bear เสร็จสิ้น\n\n")
        
        # Phase 3: Moderation
        yield format_sse_chunk("⚖️ **Phase 3:** Moderating debate...\n")
        
        decision = await loop.run_in_executor(
            executor, debate_moderator.moderate, ticker,
            ensure_report_dict(bull_result), ensure_report_dict(bear_result)
        )
        
        yield format_sse_chunk("✅ Moderation เสร็จสิ้น\n\n")
        
        # Phase 4: Risk Debate
        yield format_sse_chunk("⚠️ **Phase 4:** Risk Analysis...\n")
        
        risky_result = await loop.run_in_executor(
            executor, risky_debator.debate, ticker, 
            market_result, fundamentals_result, news_result, 
            "" # debate_history
        )
        # Extract risky argument for conservative
        risky_arg = safe_get(risky_result, "argument", "")
        
        conservative_result = await loop.run_in_executor(
            executor, conservative_debator.debate, ticker, 
            market_result, fundamentals_result, news_result, risk_result,
            risky_arg, "" # debate_history
        )
        # Extract safe argument for neutral
        safe_arg = safe_get(conservative_result, "argument", "")
        
        neutral_result = await loop.run_in_executor(
            executor, neutral_debator.debate, ticker, 
            market_result, fundamentals_result, news_result,
            risky_arg, safe_arg, "" # debate_history
        )
        
        risk_judgment = await loop.run_in_executor(
            executor, risk_judge.judge, ticker,
            risky_result, conservative_result, neutral_result
        )
        
        yield format_sse_chunk("✅ Risk Analysis เสร็จสิ้น\n\n")
        
        # Phase 5: Final Decision
        yield format_sse_chunk("💼 **Phase 5:** Final Decision...\n")
        
        pm_decision = await loop.run_in_executor(
            executor, portfolio_manager.decide, ticker,
            market_result, fundamentals_result, news_result, social_result, risk_result,
            bull_result, bear_result, decision, risk_judgment
        )
        
        final_decision = pm_decision.get("decision", "HOLD")
        
        yield format_sse_chunk(f"✅ **คำตัดสินสุดท้าย: {final_decision}**\n\n")
        yield format_sse_chunk("---\n\n")
        
        # Build final report
        report = build_report(
            ticker, final_decision,
            market_result, fundamentals_result, news_result, social_result, risk_result,
            bull_result, bear_result, decision, pm_decision
        )
        
        # Stream report in chunks
        chunk_size = 500
        for i in range(0, len(report), chunk_size):
            yield format_sse_chunk(report[i:i+chunk_size])
            await asyncio.sleep(0.05)  # Small delay for streaming effect
        
        # Save to MongoDB
        if mongo.is_connected():
            mongo.save_analysis(ticker=ticker, final_decision=final_decision, report_content=report)
        
        # Save context for follow-up questions
        session_context["last_ticker"] = ticker
        session_context["last_report"] = report
        session_context["last_analysis_data"] = {
            "ticker": ticker,
            "decision": final_decision,
            "market": safe_get(market_result, "report_section", ""),
            "fundamentals": safe_get(fundamentals_result, "report_section", ""),
            "news": safe_get(news_result, "report_section", ""),
            "social": safe_get(social_result, "report_section", ""),
            "risk": safe_get(risk_result, "report_section", ""),
            "bull": safe_get(bull_result, "report_section", ""),
            "bear": safe_get(bear_result, "report_section", ""),
            "debate": safe_get(decision, "report_section", ""),
            "pm_decision": safe_get(pm_decision, "report_section", "")
        }
        
    except Exception as e:
        yield format_sse_chunk(f"\n\n❌ เกิดข้อผิดพลาด: {str(e)}")
    
    yield format_sse_done()


async def stream_crypto_analysis(ticker: str, user_message: str):
    """Stream cryptocurrency analysis response"""
    
    yield format_sse_chunk(f"💰 เริ่มวิเคราะห์ Crypto **{ticker}**...\n\n")
    
    loop = asyncio.get_event_loop()
    
    try:
        # Phase 1: Crypto Data Collection
        yield format_sse_chunk("📊 **Phase 1:** กำลังรวบรวมข้อมูล Crypto...\n")
        
        crypto_result = await loop.run_in_executor(executor, crypto_analyst.analyze, ticker)
        
        yield format_sse_chunk("✅ รวบรวมข้อมูลเสร็จสิ้น\n\n")
        
        # Phase 2: News Analysis
        yield format_sse_chunk("📰 **Phase 2:** วิเคราะห์ข่าวสาร...\n")
        
        news_result = await loop.run_in_executor(executor, news_analyst.analyze, ticker)
        
        yield format_sse_chunk("✅ วิเคราะห์ข่าวเสร็จสิ้น\n\n")
        
        # Phase 3: Social Sentiment
        yield format_sse_chunk("💬 **Phase 3:** วิเคราะห์ Social Sentiment...\n")
        
        social_result = await loop.run_in_executor(executor, social_analyst.analyze, ticker)
        
        yield format_sse_chunk("✅ Social Sentiment เสร็จสิ้น\n\n")
        
        # Build crypto report
        sentiment = crypto_result.get("sentiment", "NEUTRAL")
        
        yield format_sse_chunk(f"✅ **สัญญาณ: {sentiment}**\n\n")
        yield format_sse_chunk("---\n\n")
        
        report = build_crypto_report(ticker, crypto_result, news_result, social_result)
        
        # Stream report in chunks
        chunk_size = 500
        for i in range(0, len(report), chunk_size):
            yield format_sse_chunk(report[i:i+chunk_size])
            await asyncio.sleep(0.05)
        
        # Save to MongoDB
        if mongo.is_connected():
            mongo.save_analysis(ticker=ticker, final_decision=sentiment, report_content=report)
        
        # Save context for follow-up questions
        session_context["last_ticker"] = ticker
        session_context["last_report"] = report
        session_context["last_analysis_data"] = {
            "ticker": ticker,
            "decision": sentiment,
            "asset_type": "crypto",
            "market": safe_get(crypto_result, "report_section", ""),
            "news": safe_get(news_result, "report_section", ""),
            "social": safe_get(social_result, "report_section", ""),
        }
        
    except Exception as e:
        yield format_sse_chunk(f"\n\n❌ เกิดข้อผิดพลาด: {str(e)}")
    
    yield format_sse_done()


def build_crypto_report(ticker: str, crypto_result: dict, news_result: dict, social_result: dict) -> str:
    """Build cryptocurrency analysis report"""
    
    sections = [
        f"# 💰 รายงานการวิเคราะห์ Cryptocurrency {ticker}",
        f"\n**วันที่วิเคราะห์:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"\n**สัญญาณ:** {crypto_result.get('sentiment', 'NEUTRAL')}",
        "\n---",
        crypto_result.get("report_section", ""),
        "\n---",
        news_result.get("report_section", ""),
        "\n---",
        social_result.get("report_section", ""),
        "\n---",
        "\n## ⚠️ Disclaimer",
        "\n**คำเตือน:** Cryptocurrency มีความผันผวนสูงมาก การลงทุนมีความเสี่ยง ควรศึกษาข้อมูลให้ดีก่อนตัดสินใจ",
        "\n**หมายเหตุ:** รายงานนี้จัดทำโดย AI เพื่อเป็นข้อมูลประกอบการตัดสินใจเท่านั้น",
    ]
    
    return "\n".join(sections)


async def stream_followup_chat(user_message: str):
    """Stream follow-up chat response based on previous analysis context"""
    
    ctx = session_context["last_analysis_data"]
    ticker = ctx.get("ticker", "")
    
    yield format_sse_chunk(f"💬 **กำลังตอบคำถามเกี่ยวกับ {ticker}...**\n\n")
    
    # Build context summary for LLM
    context_summary = f"""
=== ข้อมูลการวิเคราะห์ {ticker} ===
คำตัดสิน: {ctx.get("decision", "N/A")}

สรุปตลาด:
{ctx.get("market", "")[:800]}

ปัจจัยพื้นฐาน:
{ctx.get("fundamentals", "")[:800]}

ข่าวสาร:
{ctx.get("news", "")[:500]}

ความเสี่ยง:
{ctx.get("risk", "")[:500]}

มุมมอง Bull:
{ctx.get("bull", "")[:500]}

มุมมอง Bear:
{ctx.get("bear", "")[:500]}

คำตัดสินผู้จัดการพอร์ต:
{ctx.get("pm_decision", "")[:800]}
"""
    
    system_prompt = f"""คุณเป็นผู้ช่วยนักวิเคราะห์หุ้น AI ที่เพิ่งวิเคราะห์หุ้น {ticker} เสร็จ
ตอนนี้ผู้ใช้กำลังถามคำถามเพิ่มเติมเกี่ยวกับการวิเคราะห์นี้

หน้าที่ของคุณ:
- ตอบคำถามโดยอ้างอิงจากข้อมูลการวิเคราะห์ที่มี
- สรุปหรืออธิบายเพิ่มเติมตามที่ผู้ใช้ต้องการ
- ตอบเป็นภาษาไทย กระชับ ได้ใจความ
- ถ้าผู้ใช้ขอสรุป ให้สรุปประเด็นหลักๆ
- ถ้าผู้ใช้ถามเรื่องความเสี่ยง ให้เน้นข้อมูลจากส่วน Risk
- ถ้าผู้ใช้ถามราคา ให้อ้างอิงจากข้อมูลที่มี

{context_summary}
"""
    
    loop = asyncio.get_event_loop()
    try:
        # Use base_agent's LLM call
        from src.agents.base_agent import BaseAgent
        chat_agent = BaseAgent("ChatAssistant")
        
        response = await loop.run_in_executor(
            executor, chat_agent.call_llm, system_prompt, user_message
        )
        
        # Stream response in chunks
        chunk_size = 200
        for i in range(0, len(response), chunk_size):
            yield format_sse_chunk(response[i:i+chunk_size])
            await asyncio.sleep(0.03)
            
    except Exception as e:
        yield format_sse_chunk(f"\n\n❌ เกิดข้อผิดพลาด: {str(e)}")
    
    yield format_sse_done()


async def run_analysis(ticker: str, user_message: str, model: str) -> str:
    """Run full analysis (non-streaming)"""
    
    if not ticker:
        return "ไม่พบ ticker ในข้อความ กรุณาระบุหุ้นที่ต้องการวิเคราะห์ เช่น 'วิเคราะห์ AAPL'"
    
    ticker = normalize_ticker(ticker)
    loop = asyncio.get_event_loop()
    
    try:
        # Run all analyses
        market_result = await loop.run_in_executor(executor, market_analyst.analyze, ticker)
        fundamentals_result = await loop.run_in_executor(executor, fundamentals_analyst.analyze, ticker)
        news_result = await loop.run_in_executor(executor, news_analyst.analyze, ticker)
        social_result = await loop.run_in_executor(executor, social_analyst.analyze, ticker)
        risk_result = await loop.run_in_executor(executor, risk_analyst.analyze, ticker)
        
        bull_result = await loop.run_in_executor(
            executor, bull_researcher.analyze, ticker,
            market_result, fundamentals_result, news_result
        )
        bear_result = await loop.run_in_executor(
            executor, bear_researcher.analyze, ticker,
            market_result, fundamentals_result, news_result, risk_result
        )
        
        decision = await loop.run_in_executor(
            executor, debate_moderator.moderate, ticker,
            ensure_report_dict(bull_result), ensure_report_dict(bear_result)
        )
        
        risky_result = await loop.run_in_executor(
            executor, risky_debator.debate, ticker, 
            market_result, fundamentals_result, news_result, 
            "" # debate_history
        )
        # Extract risky argument for conservative
        risky_arg = safe_get(risky_result, "argument", "")
        
        conservative_result = await loop.run_in_executor(
            executor, conservative_debator.debate, ticker, 
            market_result, fundamentals_result, news_result, risk_result,
            risky_arg, "" # debate_history
        )
        # Extract safe argument for neutral
        safe_arg = safe_get(conservative_result, "argument", "")
        
        neutral_result = await loop.run_in_executor(
            executor, neutral_debator.debate, ticker, 
            market_result, fundamentals_result, news_result,
            risky_arg, safe_arg, "" # debate_history
        )
        
        risk_judgment = await loop.run_in_executor(
            executor, risk_judge.judge, ticker,
            risky_result, conservative_result, neutral_result
        )
        
        pm_decision = await loop.run_in_executor(
            executor, portfolio_manager.decide, ticker,
            market_result, fundamentals_result, news_result, social_result, risk_result,
            bull_result, bear_result, decision, risk_judgment
        )
        
        final_decision = pm_decision.get("decision", "HOLD")
        
        report = build_report(
            ticker, final_decision,
            market_result, fundamentals_result, news_result, social_result, risk_result,
            bull_result, bear_result, decision, pm_decision
        )
        
        # Save to MongoDB
        if mongo.is_connected():
            mongo.save_analysis(ticker=ticker, final_decision=final_decision, report_content=report)
        
        return report
        
    except Exception as e:
        return f"❌ เกิดข้อผิดพลาด: {str(e)}"


def build_report(ticker, final_decision, market_result, fundamentals_result, 
                 news_result, social_result, risk_result, bull_result, 
                 bear_result, decision, pm_decision) -> str:
    """Build the final report"""
    
    sections = [
        f"# 📊 รายงานการวิเคราะห์หุ้น {ticker}",
        f"\n**วันที่วิเคราะห์:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"\n**คำตัดสินสุดท้าย:** {final_decision}",
        "\n---",
        market_result.get("report_section", ""),
        "\n---",
        fundamentals_result.get("report_section", ""),
        "\n---",
        news_result.get("report_section", ""),
        "\n---",
        social_result.get("report_section", ""),
        "\n---",
        risk_result.get("report_section", ""),
        "\n---",
        bull_result.get("report_section", ""),
        "\n---",
        bear_result.get("report_section", ""),
        "\n---",
        decision.get("report_section", ""),
        "\n---",
        pm_decision.get("report_section", ""),
        "\n---",
        "\n## ⚠️ Disclaimer",
        "\n**คำเตือน:** รายงานนี้จัดทำโดย AI เพื่อเป็นข้อมูลประกอบการตัดสินใจเท่านั้น",
    ]
    
    return "\n".join(sections)


def format_sse_chunk(content: str) -> str:
    """Format content as SSE data chunk"""
    data = {
        "id": f"chatcmpl-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "object": "chat.completion.chunk",
        "created": int(datetime.now().timestamp()),
        "model": "stock-analyst",
        "choices": [
            {
                "index": 0,
                "delta": {"content": content},
                "finish_reason": None
            }
        ]
    }
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def format_sse_done() -> str:
    """Format SSE done message with proper finish_reason"""
    # First send a chunk with finish_reason: stop
    finish_data = {
        "id": f"chatcmpl-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "object": "chat.completion.chunk",
        "created": int(datetime.now().timestamp()),
        "model": "stock-analyst",
        "choices": [
            {
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }
        ]
    }
    # Return finish chunk followed by [DONE]
    return f"data: {json.dumps(finish_data, ensure_ascii=False)}\n\ndata: [DONE]\n\n"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
