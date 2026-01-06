"""
Crypto Analyst Agent - Analyzes cryptocurrency assets.
Focuses on price action, volume, market cap, and sentiment.
"""
import yfinance as yf
from src.agents.base_agent import BaseAgent


class CryptoAnalyst(BaseAgent):
    """
    Agent specialized in cryptocurrency analysis.
    Does NOT use traditional stock metrics like P/E, EPS, Revenue.
    Instead focuses on crypto-specific factors.
    """
    
    def __init__(self):
        super().__init__("CryptoAnalyst")
    
    def analyze(self, ticker: str) -> dict:
        """
        Analyze a cryptocurrency.
        
        Args:
            ticker: Crypto ticker (e.g., BTC-USD, ETH-USD)
            
        Returns:
            Dictionary with analysis and report section
        """
        self.log(f"Analyzing cryptocurrency {ticker}...")
        
        # Ensure ticker has -USD suffix
        if not ticker.endswith('-USD'):
            ticker = f"{ticker}-USD"
        
        # Fetch crypto data
        try:
            crypto = yf.Ticker(ticker)
            info = crypto.info
            hist = crypto.history(period="1mo")
            
            # Extract crypto-specific data
            data = {
                "name": info.get("shortName", ticker),
                "symbol": ticker,
                "current_price": info.get("regularMarketPrice", info.get("previousClose", "N/A")),
                "market_cap": info.get("marketCap", "N/A"),
                "volume_24h": info.get("volume24Hr", info.get("volume", "N/A")),
                "circulating_supply": info.get("circulatingSupply", "N/A"),
                "total_supply": info.get("totalSupply", "N/A"),
                "day_high": info.get("dayHigh", "N/A"),
                "day_low": info.get("dayLow", "N/A"),
                "week_52_high": info.get("fiftyTwoWeekHigh", "N/A"),
                "week_52_low": info.get("fiftyTwoWeekLow", "N/A"),
                "price_change_24h": info.get("regularMarketChangePercent", "N/A"),
            }
            
            # Format large numbers
            if isinstance(data["market_cap"], (int, float)) and data["market_cap"] > 1e9:
                data["market_cap_formatted"] = f"${data['market_cap']/1e9:.2f}B"
            elif isinstance(data["market_cap"], (int, float)) and data["market_cap"] > 1e6:
                data["market_cap_formatted"] = f"${data['market_cap']/1e6:.2f}M"
            else:
                data["market_cap_formatted"] = str(data["market_cap"])
            
            # Get recent price history
            if not hist.empty:
                recent_prices = hist.tail(5)[['Open', 'Close', 'Volume']].to_string()
            else:
                recent_prices = "No price data available"
                
        except Exception as e:
            self.log(f"Error fetching crypto data: {e}")
            data = {"error": str(e)}
            recent_prices = "Error fetching data"
        
        # Build prompt for LLM analysis
        system_prompt = """You are a Cryptocurrency Analyst specializing in digital assets.
Your analysis focuses on:
1. Price action and volatility
2. Market cap and trading volume
3. Market sentiment and trends
4. Technical patterns
5. Risk assessment for crypto assets

**IMPORTANT:**
- Crypto is highly volatile - always mention risks
- DO NOT use stock metrics like P/E, EPS, Revenue
- Write entirely in Thai language
- Be balanced - mention both opportunities and risks"""

        user_prompt = f"""
Analyze this cryptocurrency: {ticker}

=== ข้อมูลตลาด ===
ชื่อ: {data.get('name', ticker)}
ราคาปัจจุบัน: ${data.get('current_price', 'N/A')}
Market Cap: {data.get('market_cap_formatted', 'N/A')}
Volume 24h: {data.get('volume_24h', 'N/A')}
52-Week High: ${data.get('week_52_high', 'N/A')}
52-Week Low: ${data.get('week_52_low', 'N/A')}
Circulating Supply: {data.get('circulating_supply', 'N/A')}

=== ราคา 5 วันล่าสุด ===
{recent_prices}

กรุณาวิเคราะห์โดยครอบคลุม:
1. **สถานะตลาดปัจจุบัน**: ราคาอยู่ในช่วงไหน (ใกล้ ATH? ใกล้ bottom?)
2. **Volume และ Liquidity**: การซื้อขายคล่องแค่ไหน
3. **แนวโน้มระยะสั้น**: กราฟบอกอะไร
4. **ความเสี่ยงสำคัญ**: ความผันผวน, regulatory risks, etc.
5. **สัญญาณ**: BULLISH / BEARISH / NEUTRAL

Format เป็น Markdown section เริ่มด้วย '## 1. รายงานวิเคราะห์ Cryptocurrency'
"""

        self.log(f"Asking LLM to analyze {ticker}...")
        report = self.call_llm(system_prompt, user_prompt)
        
        # Determine sentiment from report
        sentiment = "NEUTRAL"
        report_upper = report.upper()
        if "BULLISH" in report_upper:
            sentiment = "BULLISH"
        elif "BEARISH" in report_upper:
            sentiment = "BEARISH"
        
        return {
            "ticker": ticker,
            "data": data,
            "sentiment": sentiment,
            "report_section": report,
            "asset_type": "crypto"
        }
