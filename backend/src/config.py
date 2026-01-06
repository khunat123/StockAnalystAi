"""
Configuration module for AI Stock Analyst
Loads environment variables and provides config access
"""

import os
from dotenv import load_dotenv

# Load environment variables from project root
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_project_root, '.env'))

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

# Database
MONGODB_URL = os.getenv("MONGODB_URL")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "trading-bot")

# LLM Provider (gemini or openai)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

# Validate required keys
def validate_config():
    """Check if required configuration is present"""
    errors = []
    
    if LLM_PROVIDER == "gemini" and not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY is required when using Gemini")
    elif LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is required when using OpenAI")
    
    if errors:
        for error in errors:
            print(f"[Config Error] {error}")
        return False
    
    return True


def get_config_summary():
    """Get a summary of current configuration"""
    return {
        "llm_provider": LLM_PROVIDER,
        "gemini_configured": bool(GEMINI_API_KEY),
        "openai_configured": bool(OPENAI_API_KEY),
        "tavily_configured": bool(TAVILY_API_KEY),
        "finnhub_configured": bool(FINNHUB_API_KEY),
        "alpha_vantage_configured": bool(ALPHA_VANTAGE_API_KEY),
        "mongodb_configured": bool(MONGODB_URL),
    }
