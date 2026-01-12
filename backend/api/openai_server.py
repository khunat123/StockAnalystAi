"""
OpenAI-Compatible API Server for Ai-project
This allows Chat-UI to use our agents via standard OpenAI API format.
Refactored to use LangGraph for orchestration.
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

from src.data.tools import extract_ticker, normalize_ticker, is_crypto
from src.db import get_mongo_client
from src.graph import app as graph_app

# MongoDB
mongo = get_mongo_client()

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


# ============ Endpoints ============

@app.get("/")
async def root():
    return {"message": "AI Stock Analyst API - OpenAI Compatible (LangGraph)"}


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
    """Stream the analysis response using LangGraph"""
    
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
    crypto_flag = is_crypto(ticker)
    
    # Initialize State
    initial_state = {
        "ticker": ticker, 
        "is_crypto": crypto_flag,
        "market_data": {}, "fundamentals_data": {}, "news_data": {}, 
        "social_data": {}, "risk_data": {}, "crypto_data": {},
        "bull_analysis": {}, "bear_analysis": {}, 
        "debate_outcome": {}, "risk_judgment": {}, "final_decision": {},
        "final_report": ""
    }
    
    if crypto_flag:
        yield format_sse_chunk(f"💰 เริ่มวิเคราะห์ Crypto **{ticker}** (LangGraph)...\n\n")
        yield format_sse_chunk("📊 **Phase 1:** กำลังรวบรวมข้อมูล Crypto...\n")
    else:
        yield format_sse_chunk(f"🔍 เริ่มวิเคราะห์หุ้น **{ticker}** (LangGraph)...\n\n")
        yield format_sse_chunk("📊 **Phase 1:** กำลังรวบรวมข้อมูล...\n")

    current_phase = 1

    try:
        # Stream events from LangGraph
        async for event in graph_app.astream(initial_state):
            for node_name, output in event.items():
                
                # STOCK FLOW EVENTS
                if node_name == "run_analysts_parallel":
                    yield format_sse_chunk("✅ รวบรวมข้อมูลเสร็จสิ้น\n\n")
                    yield format_sse_chunk("🐂🐻 **Phase 2:** Bull vs Bear Debate...\n")
                
                elif node_name == "researchers":
                    yield format_sse_chunk("✅ Bull vs Bear เสร็จสิ้น\n\n")
                    yield format_sse_chunk("⚖️ **Phase 3:** Moderating debate...\n")
                
                elif node_name == "debate_moderator":
                    yield format_sse_chunk("✅ Moderation เสร็จสิ้น\n\n")
                    yield format_sse_chunk("⚠️ **Phase 4:** Risk Analysis...\n")
                
                elif node_name == "risk_judge":
                    yield format_sse_chunk("✅ Risk Analysis เสร็จสิ้น\n\n")
                    yield format_sse_chunk("💼 **Phase 5:** Final Decision...\n")
                
                elif node_name == "portfolio_manager":
                    decision = output.get("final_decision", {}).get("decision", "HOLD")
                    yield format_sse_chunk(f"✅ **คำตัดสินสุดท้าย: {decision}**\n\n")
                    yield format_sse_chunk("---\n\n")
                
                elif node_name == "report_builder":
                    report = output.get("final_report", "")
                    
                    # Store context
                    session_context["last_ticker"] = ticker
                    session_context["last_report"] = report
                    # Note: We don't have full state access here easily in astream loop unless we accumulate it,
                    # but for now we trust the report generation. 
                    # If we need 'last_analysis_data' for follow-up, we might need to grab it from the final state if returned,
                    # or just rely on 'report' being sufficient for now to save complexity.
                    
                    # Stream report chunks
                    chunk_size = 500
                    for i in range(0, len(report), chunk_size):
                        yield format_sse_chunk(report[i:i+chunk_size])
                        await asyncio.sleep(0.05)
                        
                    # Save to MongoDB
                    if mongo.is_connected():
                         # We need final decision string
                         # We can parse it or rely on valid state if we had it. 
                         # For now, let's assume report building succeeded.
                         mongo.save_analysis(ticker=ticker, final_decision="N/A", report_content=report)

                # CRYPTO FLOW EVENTS
                elif node_name == "crypto_analyst":
                    yield format_sse_chunk("✅ รวบรวมข้อมูลเสร็จสิ้น\n\n")
                    yield format_sse_chunk("📰 **Phase 2:** วิเคราะห์ข่าวและ Social...\n")
                
                elif node_name == "crypto_enrichment":
                     yield format_sse_chunk("✅ วิเคราะห์ข่าวและ Social เสร็จสิ้น\n\n")
                
                elif node_name == "crypto_report":
                    report = output.get("final_report", "")
                    decision_data = output.get("final_decision", {})
                    decision = decision_data.get("decision", "NEUTRAL")
                    
                    yield format_sse_chunk(f"✅ **สัญญาณ: {decision}**\n\n")
                    yield format_sse_chunk("---\n\n")
                    
                    # Stream report chunks
                    chunk_size = 500
                    for i in range(0, len(report), chunk_size):
                        yield format_sse_chunk(report[i:i+chunk_size])
                        await asyncio.sleep(0.05)
                        
                    if mongo.is_connected():
                        mongo.save_analysis(ticker=ticker, final_decision=decision, report_content=report)

                    session_context["last_ticker"] = ticker
                    session_context["last_report"] = report

    except Exception as e:
        yield format_sse_chunk(f"\n\n❌ เกิดข้อผิดพลาด: {str(e)}")
    
    yield format_sse_done()


async def stream_followup_chat(user_message: str):
    """Stream follow-up chat response based on previous analysis context"""
    
    # Simple fallback using just the report as context since we might not have full state dict easily available
    # after the refactor to simple astream. 
    # To improve: we could store the final state in a global/cache.
    
    ticker = session_context["last_ticker"]
    report = session_context["last_report"]
    
    yield format_sse_chunk(f"💬 **กำลังตอบคำถามเกี่ยวกับ {ticker}...**\n\n")
    
    system_prompt = f"""คุณเป็นผู้ช่วยนักวิเคราะห์หุ้น AI ที่เพิ่งวิเคราะห์หุ้น {ticker} เสร็จ
ข้อมูลในรายงานล่าสุด:
{report}

หน้าที่ของคุณ:
- ตอบคำถามโดยอ้างอิงจากข้อมูลการวิเคราะห์ที่มี
- สรุปหรืออธิบายเพิ่มเติมตามที่ผู้ใช้ต้องการ
- ตอบเป็นภาษาไทย กระชับ ได้ใจความ
"""
    
    loop = asyncio.get_event_loop()
    try:
        # Use base_agent's LLM call
        from src.agents.base_agent import BaseAgent
        # Initializing a temporary agent for chat
        chat_agent = BaseAgent("ChatAssistant")
        
        # Run in executor to avoid blocking
        response = await loop.run_in_executor(
            None, chat_agent.call_llm, system_prompt, user_message
        )
        
        # Stream response
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
    crypto_flag = is_crypto(ticker)
    
    initial_state = {
        "ticker": ticker, 
        "is_crypto": crypto_flag,
        "market_data": {}, "fundamentals_data": {}, "news_data": {}, 
        "social_data": {}, "risk_data": {}, "crypto_data": {},
        "bull_analysis": {}, "bear_analysis": {}, 
        "debate_outcome": {}, "risk_judgment": {}, "final_decision": {},
        "final_report": ""
    }
    
    try:
        # Use ainvoke to get final state
        final_state = await graph_app.ainvoke(initial_state)
        report = final_state.get("final_report", "No report generated.")
        
        decision = final_state.get("final_decision", {}).get("decision", "N/A")
        
        if mongo.is_connected():
            mongo.save_analysis(ticker=ticker, final_decision=decision, report_content=report)
            
        return report
        
    except Exception as e:
        return f"❌ เกิดข้อผิดพลาด: {str(e)}"


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
    return f"data: {json.dumps(finish_data, ensure_ascii=False)}\n\ndata: [DONE]\n\n"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
