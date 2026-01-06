"""
Additional Data Providers
Finnhub and Alpha Vantage API integrations
"""

import os
import requests
from typing import Dict, Optional
from datetime import datetime, timedelta


class FinnhubProvider:
    """Finnhub API for real-time stock data and company info"""
    
    BASE_URL = "https://finnhub.io/api/v1"
    
    def __init__(self):
        self.api_key = os.getenv("FINNHUB_API_KEY")
        if not self.api_key:
            print("[Finnhub] API key not found")
    
    def _request(self, endpoint: str, params: dict = None) -> Optional[Dict]:
        """Make API request"""
        if not self.api_key:
            return None
        
        params = params or {}
        params["token"] = self.api_key
        
        try:
            response = requests.get(f"{self.BASE_URL}/{endpoint}", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[Finnhub] Error: {e}")
            return None
    
    def get_quote(self, symbol: str) -> Dict:
        """Get real-time quote"""
        data = self._request("quote", {"symbol": symbol})
        if data:
            return {
                "current_price": data.get("c"),
                "change": data.get("d"),
                "percent_change": data.get("dp"),
                "high": data.get("h"),
                "low": data.get("l"),
                "open": data.get("o"),
                "previous_close": data.get("pc"),
                "timestamp": datetime.fromtimestamp(data.get("t", 0)).isoformat()
            }
        return {}
    
    def get_company_profile(self, symbol: str) -> Dict:
        """Get company profile"""
        data = self._request("stock/profile2", {"symbol": symbol})
        if data:
            return {
                "name": data.get("name"),
                "ticker": data.get("ticker"),
                "exchange": data.get("exchange"),
                "industry": data.get("finnhubIndustry"),
                "market_cap": data.get("marketCapitalization"),
                "shares_outstanding": data.get("shareOutstanding"),
                "logo": data.get("logo"),
                "website": data.get("weburl"),
                "ipo_date": data.get("ipo")
            }
        return {}
    
    def get_recommendation(self, symbol: str) -> Dict:
        """Get analyst recommendations"""
        data = self._request("stock/recommendation", {"symbol": symbol})
        if data and len(data) > 0:
            latest = data[0]
            return {
                "buy": latest.get("buy", 0),
                "hold": latest.get("hold", 0),
                "sell": latest.get("sell", 0),
                "strong_buy": latest.get("strongBuy", 0),
                "strong_sell": latest.get("strongSell", 0),
                "period": latest.get("period")
            }
        return {}
    
    def get_earnings(self, symbol: str) -> Dict:
        """Get earnings surprises"""
        data = self._request("stock/earnings", {"symbol": symbol})
        if data and len(data) > 0:
            latest = data[0]
            return {
                "actual": latest.get("actual"),
                "estimate": latest.get("estimate"),
                "surprise": latest.get("surprise"),
                "surprise_percent": latest.get("surprisePercent"),
                "period": latest.get("period")
            }
        return {}
    
    def get_insider_sentiment(self, symbol: str) -> Dict:
        """Get insider sentiment (MSPR)"""
        today = datetime.now()
        from_date = (today - timedelta(days=90)).strftime("%Y-%m-%d")
        to_date = today.strftime("%Y-%m-%d")
        
        data = self._request("stock/insider-sentiment", {
            "symbol": symbol,
            "from": from_date,
            "to": to_date
        })
        if data and "data" in data and len(data["data"]) > 0:
            latest = data["data"][-1]
            return {
                "mspr": latest.get("mspr"),  # Monthly Share Purchase Ratio
                "change": latest.get("change"),
                "month": latest.get("month"),
                "year": latest.get("year")
            }
        return {}


class AlphaVantageProvider:
    """Alpha Vantage API for technical indicators and fundamentals"""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self):
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            print("[AlphaVantage] API key not found")
    
    def _request(self, params: dict) -> Optional[Dict]:
        """Make API request"""
        if not self.api_key:
            return None
        
        params["apikey"] = self.api_key
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if "Error Message" in data or "Note" in data:
                print(f"[AlphaVantage] API limit or error: {data}")
                return None
            
            return data
        except Exception as e:
            print(f"[AlphaVantage] Error: {e}")
            return None
    
    def get_rsi(self, symbol: str, interval: str = "daily", period: int = 14) -> Dict:
        """Get RSI indicator"""
        data = self._request({
            "function": "RSI",
            "symbol": symbol,
            "interval": interval,
            "time_period": period,
            "series_type": "close"
        })
        if data and "Technical Analysis: RSI" in data:
            rsi_data = data["Technical Analysis: RSI"]
            latest_date = list(rsi_data.keys())[0]
            return {
                "rsi": float(rsi_data[latest_date]["RSI"]),
                "date": latest_date
            }
        return {}
    
    def get_macd(self, symbol: str, interval: str = "daily") -> Dict:
        """Get MACD indicator"""
        data = self._request({
            "function": "MACD",
            "symbol": symbol,
            "interval": interval,
            "series_type": "close"
        })
        if data and "Technical Analysis: MACD" in data:
            macd_data = data["Technical Analysis: MACD"]
            latest_date = list(macd_data.keys())[0]
            latest = macd_data[latest_date]
            return {
                "macd": float(latest["MACD"]),
                "signal": float(latest["MACD_Signal"]),
                "histogram": float(latest["MACD_Hist"]),
                "date": latest_date
            }
        return {}
    
    def get_sma(self, symbol: str, interval: str = "daily", period: int = 50) -> Dict:
        """Get SMA indicator"""
        data = self._request({
            "function": "SMA",
            "symbol": symbol,
            "interval": interval,
            "time_period": period,
            "series_type": "close"
        })
        if data and "Technical Analysis: SMA" in data:
            sma_data = data["Technical Analysis: SMA"]
            latest_date = list(sma_data.keys())[0]
            return {
                "sma": float(sma_data[latest_date]["SMA"]),
                "period": period,
                "date": latest_date
            }
        return {}
    
    def get_overview(self, symbol: str) -> Dict:
        """Get company overview with fundamentals"""
        data = self._request({
            "function": "OVERVIEW",
            "symbol": symbol
        })
        if data and "Symbol" in data:
            return {
                "pe_ratio": float(data.get("PERatio", 0) or 0),
                "peg_ratio": float(data.get("PEGRatio", 0) or 0),
                "book_value": float(data.get("BookValue", 0) or 0),
                "dividend_yield": float(data.get("DividendYield", 0) or 0),
                "eps": float(data.get("EPS", 0) or 0),
                "revenue_per_share": float(data.get("RevenuePerShareTTM", 0) or 0),
                "profit_margin": float(data.get("ProfitMargin", 0) or 0),
                "operating_margin": float(data.get("OperatingMarginTTM", 0) or 0),
                "roe": float(data.get("ReturnOnEquityTTM", 0) or 0),
                "roa": float(data.get("ReturnOnAssetsTTM", 0) or 0),
                "beta": float(data.get("Beta", 0) or 0),
                "52_week_high": float(data.get("52WeekHigh", 0) or 0),
                "52_week_low": float(data.get("52WeekLow", 0) or 0),
                "analyst_target_price": float(data.get("AnalystTargetPrice", 0) or 0)
            }
        return {}


def get_enhanced_data(ticker: str) -> Dict:
    """Get enhanced data from all providers"""
    finnhub = FinnhubProvider()
    alpha = AlphaVantageProvider()
    
    result = {
        "finnhub": {},
        "alpha_vantage": {}
    }
    
    # Finnhub data
    if finnhub.api_key:
        result["finnhub"] = {
            "quote": finnhub.get_quote(ticker),
            "profile": finnhub.get_company_profile(ticker),
            "recommendation": finnhub.get_recommendation(ticker),
            "earnings": finnhub.get_earnings(ticker),
            "insider_sentiment": finnhub.get_insider_sentiment(ticker)
        }
        print(f"[Finnhub] Fetched data for {ticker}")
    
    # Alpha Vantage data
    if alpha.api_key:
        result["alpha_vantage"] = {
            "rsi": alpha.get_rsi(ticker),
            "macd": alpha.get_macd(ticker),
            "sma50": alpha.get_sma(ticker, period=50),
            "overview": alpha.get_overview(ticker)
        }
        print(f"[AlphaVantage] Fetched data for {ticker}")
    
    return result


def format_enhanced_report(data: Dict) -> str:
    """Format enhanced data into a report section"""
    report = "\n## 📡 Enhanced Data (Finnhub + Alpha Vantage)\n"
    
    # Finnhub section
    fh = data.get("finnhub", {})
    if fh.get("quote"):
        q = fh["quote"]
        report += f"""
### 📈 Real-time Quote (Finnhub)
- **Price:** ${q.get('current_price', 'N/A')}
- **Change:** ${q.get('change', 'N/A')} ({q.get('percent_change', 'N/A')}%)
- **Day Range:** ${q.get('low', 'N/A')} - ${q.get('high', 'N/A')}
"""
    
    if fh.get("recommendation"):
        r = fh["recommendation"]
        total = r.get('strong_buy', 0) + r.get('buy', 0) + r.get('hold', 0) + r.get('sell', 0) + r.get('strong_sell', 0)
        report += f"""
### 📊 Analyst Recommendations
- **Strong Buy:** {r.get('strong_buy', 0)}
- **Buy:** {r.get('buy', 0)}
- **Hold:** {r.get('hold', 0)}
- **Sell:** {r.get('sell', 0)}
- **Strong Sell:** {r.get('strong_sell', 0)}
"""
    
    if fh.get("earnings"):
        e = fh["earnings"]
        report += f"""
### 💰 Latest Earnings
- **Actual:** ${e.get('actual', 'N/A')}
- **Estimate:** ${e.get('estimate', 'N/A')}
- **Surprise:** {e.get('surprise_percent', 'N/A')}%
"""
    
    # Alpha Vantage section
    av = data.get("alpha_vantage", {})
    if av.get("rsi") or av.get("macd"):
        report += "\n### 📐 Technical Indicators (Alpha Vantage)\n"
        if av.get("rsi"):
            rsi_val = av["rsi"].get("rsi", 50)
            rsi_signal = "Oversold 🟢" if rsi_val < 30 else "Overbought 🔴" if rsi_val > 70 else "Neutral ⚪"
            report += f"- **RSI (14):** {rsi_val:.1f} ({rsi_signal})\n"
        
        if av.get("macd"):
            m = av["macd"]
            macd_signal = "Bullish 🟢" if m.get("histogram", 0) > 0 else "Bearish 🔴"
            report += f"- **MACD:** {m.get('macd', 0):.2f} | Signal: {m.get('signal', 0):.2f} ({macd_signal})\n"
        
        if av.get("sma50"):
            report += f"- **SMA 50:** ${av['sma50'].get('sma', 0):.2f}\n"
    
    if av.get("overview"):
        o = av["overview"]
        report += f"""
### 💼 Fundamentals (Alpha Vantage)
- **P/E Ratio:** {o.get('pe_ratio', 'N/A')}
- **PEG Ratio:** {o.get('peg_ratio', 'N/A')}
- **EPS:** ${o.get('eps', 'N/A')}
- **ROE:** {o.get('roe', 0) * 100:.1f}%
- **Profit Margin:** {o.get('profit_margin', 0) * 100:.1f}%
- **Beta:** {o.get('beta', 'N/A')}
- **Analyst Target:** ${o.get('analyst_target_price', 'N/A')}
"""
    
    return report
