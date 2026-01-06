"""
Quantitative Metrics Scorer
Calculates objective confidence scores from real market data
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Tuple


def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    """
    Calculate RSI (Relative Strength Index)
    RSI < 30 = Oversold (Bullish signal)
    RSI > 70 = Overbought (Bearish signal)
    """
    if len(prices) < period + 1:
        return 50.0  # Neutral
    
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0


def calculate_macd(prices: pd.Series) -> Tuple[float, float, str]:
    """
    Calculate MACD (Moving Average Convergence Divergence)
    Returns: (MACD line, Signal line, Signal)
    """
    if len(prices) < 26:
        return 0.0, 0.0, "NEUTRAL"
    
    exp1 = prices.ewm(span=12, adjust=False).mean()
    exp2 = prices.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    
    macd_val = float(macd.iloc[-1])
    signal_val = float(signal.iloc[-1])
    
    if macd_val > signal_val:
        signal_str = "BULLISH"
    elif macd_val < signal_val:
        signal_str = "BEARISH"
    else:
        signal_str = "NEUTRAL"
    
    return macd_val, signal_val, signal_str


def calculate_sma_position(prices: pd.Series, period: int = 50) -> Tuple[float, str]:
    """
    Calculate price position relative to SMA
    Returns: (percentage above/below SMA, Signal)
    """
    if len(prices) < period:
        return 0.0, "NEUTRAL"
    
    sma = prices.rolling(window=period).mean()
    current_price = prices.iloc[-1]
    sma_val = sma.iloc[-1]
    
    pct_diff = ((current_price - sma_val) / sma_val) * 100
    
    if pct_diff > 2:
        signal = "BULLISH"
    elif pct_diff < -2:
        signal = "BEARISH"
    else:
        signal = "NEUTRAL"
    
    return float(pct_diff), signal


def calculate_volume_trend(volume: pd.Series, period: int = 20) -> Tuple[float, str]:
    """
    Calculate volume trend
    Returns: (volume change %, Signal)
    """
    if len(volume) < period:
        return 0.0, "NEUTRAL"
    
    avg_volume = volume.rolling(window=period).mean()
    recent_avg = volume.iloc[-5:].mean()
    historical_avg = avg_volume.iloc[-period]
    
    if historical_avg == 0:
        return 0.0, "NEUTRAL"
    
    pct_change = ((recent_avg - historical_avg) / historical_avg) * 100
    
    if pct_change > 20:
        signal = "INCREASING"
    elif pct_change < -20:
        signal = "DECREASING"
    else:
        signal = "STABLE"
    
    return float(pct_change), signal


def calculate_technical_score(ticker: str) -> Dict:
    """
    Calculate technical analysis score (0-100)
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="3mo")
        
        if hist.empty:
            return {"score": 50, "details": "No data available"}
        
        prices = hist['Close']
        volume = hist['Volume']
        
        # RSI (25% weight)
        rsi = calculate_rsi(prices)
        if rsi < 30:
            rsi_score = 80 + (30 - rsi)  # Oversold = Bullish
        elif rsi > 70:
            rsi_score = 20 - (rsi - 70)  # Overbought = Bearish
        else:
            rsi_score = 50  # Neutral
        rsi_score = max(0, min(100, rsi_score))
        
        # MACD (25% weight)
        macd_val, signal_val, macd_signal = calculate_macd(prices)
        if macd_signal == "BULLISH":
            macd_score = 70 + min(30, abs(macd_val - signal_val) * 10)
        elif macd_signal == "BEARISH":
            macd_score = 30 - min(30, abs(macd_val - signal_val) * 10)
        else:
            macd_score = 50
        macd_score = max(0, min(100, macd_score))
        
        # SMA Position (25% weight)
        sma_pct, sma_signal = calculate_sma_position(prices)
        sma_score = 50 + (sma_pct * 2)  # +/- 2% = +/- 4 points
        sma_score = max(0, min(100, sma_score))
        
        # Volume Trend (25% weight)
        vol_pct, vol_signal = calculate_volume_trend(volume)
        vol_score = 50 + (vol_pct / 4)  # Normalize
        vol_score = max(0, min(100, vol_score))
        
        # Combined Technical Score
        total_score = (rsi_score * 0.25 + macd_score * 0.25 + 
                       sma_score * 0.25 + vol_score * 0.25)
        
        return {
            "score": round(total_score, 1),
            "rsi": {"value": round(rsi, 1), "score": round(rsi_score, 1)},
            "macd": {"signal": macd_signal, "score": round(macd_score, 1)},
            "sma50": {"pct": round(sma_pct, 2), "signal": sma_signal, "score": round(sma_score, 1)},
            "volume": {"pct": round(vol_pct, 1), "signal": vol_signal, "score": round(vol_score, 1)}
        }
    except Exception as e:
        print(f"[MetricsScorer] Technical error: {e}")
        return {"score": 50, "error": str(e)}


def calculate_fundamental_score(ticker: str) -> Dict:
    """
    Calculate fundamental analysis score (0-100)
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        scores = []
        details = {}
        
        # P/E Ratio (25% weight) - Lower is better (relative to market avg ~20)
        pe = info.get('trailingPE')
        if pe and pe > 0:
            # PE < 15 = 80+, PE = 20 = 50, PE > 40 = 20
            pe_score = max(0, min(100, 100 - (pe - 10) * 2))
            scores.append(('pe', pe_score, 0.25))
            details['pe'] = {"value": round(pe, 1), "score": round(pe_score, 1)}
        
        # ROE (25% weight) - Higher is better
        roe = info.get('returnOnEquity')
        if roe:
            # ROE > 20% = 80+, ROE = 10% = 50
            roe_pct = roe * 100
            roe_score = max(0, min(100, 30 + roe_pct * 2.5))
            scores.append(('roe', roe_score, 0.25))
            details['roe'] = {"value": round(roe_pct, 1), "score": round(roe_score, 1)}
        
        # Profit Margin (25% weight)
        margin = info.get('profitMargins')
        if margin:
            margin_pct = margin * 100
            margin_score = max(0, min(100, 30 + margin_pct * 3))
            scores.append(('margin', margin_score, 0.25))
            details['profit_margin'] = {"value": round(margin_pct, 1), "score": round(margin_score, 1)}
        
        # Debt to Equity (25% weight) - Lower is better
        debt_equity = info.get('debtToEquity')
        if debt_equity:
            # D/E < 50 = 80+, D/E = 100 = 50, D/E > 200 = 20
            de_score = max(0, min(100, 100 - debt_equity * 0.5))
            scores.append(('de', de_score, 0.25))
            details['debt_equity'] = {"value": round(debt_equity, 1), "score": round(de_score, 1)}
        
        # Calculate weighted average
        if scores:
            total_weight = sum(s[2] for s in scores)
            total_score = sum(s[1] * s[2] for s in scores) / total_weight
        else:
            total_score = 50
        
        return {
            "score": round(total_score, 1),
            **details
        }
    except Exception as e:
        print(f"[MetricsScorer] Fundamental error: {e}")
        return {"score": 50, "error": str(e)}


def calculate_sentiment_score(news_data: dict) -> Dict:
    """
    Calculate sentiment score from news analysis
    """
    try:
        report = news_data.get("report_section", "")
        
        # Simple keyword-based sentiment
        bullish_words = ['growth', 'profit', 'beat', 'surge', 'upgrade', 'bullish', 
                         'เติบโต', 'กำไร', 'เพิ่ม', 'บวก', 'ขึ้น']
        bearish_words = ['decline', 'loss', 'miss', 'downgrade', 'bearish', 'risk',
                         'ลด', 'ขาดทุน', 'ลง', 'เสี่ยง', 'ลบ']
        
        report_lower = report.lower()
        bullish_count = sum(1 for word in bullish_words if word in report_lower)
        bearish_count = sum(1 for word in bearish_words if word in report_lower)
        
        total = bullish_count + bearish_count
        if total == 0:
            sentiment_score = 50
            sentiment = "NEUTRAL"
        else:
            sentiment_score = (bullish_count / total) * 100
            if sentiment_score > 60:
                sentiment = "BULLISH"
            elif sentiment_score < 40:
                sentiment = "BEARISH"
            else:
                sentiment = "NEUTRAL"
        
        return {
            "score": round(sentiment_score, 1),
            "sentiment": sentiment,
            "bullish_signals": bullish_count,
            "bearish_signals": bearish_count
        }
    except Exception as e:
        print(f"[MetricsScorer] Sentiment error: {e}")
        return {"score": 50, "error": str(e)}


def get_combined_score(ticker: str, news_data: dict = None) -> Dict:
    """
    Calculate combined confidence score from all metrics
    
    Weights:
    - Technical: 40%
    - Fundamental: 40%
    - Sentiment: 20%
    """
    technical = calculate_technical_score(ticker)
    fundamental = calculate_fundamental_score(ticker)
    sentiment = calculate_sentiment_score(news_data or {})
    
    # Combined score
    combined = (
        technical["score"] * 0.4 +
        fundamental["score"] * 0.4 +
        sentiment["score"] * 0.2
    )
    
    # Determine overall signal
    if combined >= 65:
        signal = "BULLISH"
    elif combined <= 35:
        signal = "BEARISH"
    else:
        signal = "NEUTRAL"
    
    return {
        "combined_score": round(combined, 1),
        "signal": signal,
        "confidence": round(combined / 100, 2),  # 0-1 scale
        "technical": technical,
        "fundamental": fundamental,
        "sentiment": sentiment
    }


def format_metrics_report(scores: Dict) -> str:
    """
    Format metrics scores into a readable report section
    """
    tech = scores.get("technical", {})
    fund = scores.get("fundamental", {})
    sent = scores.get("sentiment", {})
    
    report = f"""## 📊 Quantitative Metrics Score

**Overall Score: {scores['combined_score']}/100 ({scores['signal']})**
**Confidence: {scores['confidence']:.0%}**

### 📈 Technical Analysis (40%)
- **RSI (14):** {tech.get('rsi', {}).get('value', 'N/A')} → Score: {tech.get('rsi', {}).get('score', 'N/A')}
- **MACD:** {tech.get('macd', {}).get('signal', 'N/A')} → Score: {tech.get('macd', {}).get('score', 'N/A')}
- **Price vs SMA50:** {tech.get('sma50', {}).get('pct', 'N/A')}% ({tech.get('sma50', {}).get('signal', 'N/A')})
- **Volume Trend:** {tech.get('volume', {}).get('signal', 'N/A')} ({tech.get('volume', {}).get('pct', 'N/A')}%)
- **Technical Score:** {tech.get('score', 'N/A')}/100

### 💰 Fundamental Analysis (40%)
- **P/E Ratio:** {fund.get('pe', {}).get('value', 'N/A')} → Score: {fund.get('pe', {}).get('score', 'N/A')}
- **ROE:** {fund.get('roe', {}).get('value', 'N/A')}% → Score: {fund.get('roe', {}).get('score', 'N/A')}
- **Profit Margin:** {fund.get('profit_margin', {}).get('value', 'N/A')}%
- **Debt/Equity:** {fund.get('debt_equity', {}).get('value', 'N/A')}
- **Fundamental Score:** {fund.get('score', 'N/A')}/100

### 💬 Sentiment Analysis (20%)
- **Bullish Signals:** {sent.get('bullish_signals', 'N/A')}
- **Bearish Signals:** {sent.get('bearish_signals', 'N/A')}
- **Sentiment:** {sent.get('sentiment', 'N/A')}
- **Sentiment Score:** {sent.get('score', 'N/A')}/100
"""
    return report
