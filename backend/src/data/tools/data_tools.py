import yfinance as yf
import pandas as pd
import re


def extract_ticker(message: str) -> str:
    """
    Extracts a stock ticker from a user message.
    Looks for common patterns like "วิเคราะห์ AAPL", "TSLA", "ดูหุ้น NVDA" etc.
    Returns the ticker symbol or None if not found.
    """
    if not message:
        return None
    
    message_upper = message.strip().upper()
    
    # Pattern 1: Direct ticker (2-5 uppercase letters)
    ticker_pattern = r'\b([A-Z]{2,5})\b'
    
    # Comprehensive list of words to exclude
    exclude_words = {
        # Thai keywords
        'วิเคราะห์', 'ดู', 'ขอ', 'หุ้น', 'ราคา', 'ข่าว', 'สรุป', 'อธิบาย', 'บอก', 'ถาม',
        # Trading actions
        'BUY', 'SELL', 'HOLD', 'LONG', 'SHORT', 'STOP', 'LOSS', 'TAKE', 'PROFIT',
        # Common English words that could be mistaken for tickers
        'USER', 'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HAD', 
        'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'HAS', 'HIS', 'HOW', 'ITS', 'LET', 'MAY',
        'NEW', 'NOW', 'OLD', 'SEE', 'WAY', 'WHO', 'BOY', 'DID', 'GET', 'HIM', 'SAY',
        'SHE', 'TOO', 'USE', 'DAY', 'HEY', 'HI', 'OK', 'YES', 'NO',
        # Chat/System terms
        'CHAT', 'BOT', 'AI', 'API', 'URL', 'HTTP', 'HTTPS', 'WWW', 'COM', 'ORG', 'NET',
        'JSON', 'HTML', 'CSS', 'MSG', 'ERR', 'LOG', 'APP', 'DEV', 'SRC', 'ENV',
        # Greetings and common phrases
        'HELLO', 'THANKS', 'THANK', 'PLEASE', 'HELP', 'WHAT', 'WHEN', 'WHERE', 'WHY',
        'WHICH', 'WITH', 'THIS', 'THAT', 'HAVE', 'FROM', 'THEY', 'BEEN', 'WILL',
        'MORE', 'SOME', 'TIME', 'VERY', 'JUST', 'KNOW', 'TAKE', 'COME', 'MAKE',
        'LIKE', 'BACK', 'ONLY', 'OVER', 'SUCH', 'INTO', 'YEAR', 'YOUR', 'GOOD',
        'COULD', 'THEM', 'THAN', 'THEN', 'LOOK', 'ALSO', 'WELL', 'SHOULD', 'WOULD',
        # Analysis terms
        'RISK', 'SAFE', 'HIGH', 'LOW', 'BULL', 'BEAR', 'LONG', 'TERM', 'RETURNS',
        'PRICE', 'VALUE', 'STOCK', 'MARKET', 'TRADE', 'INVEST', 'MONEY', 'FUND',
        # Summary/Report terms  
        'NOTE', 'INFO', 'DATA', 'SHOW', 'LIST', 'VIEW', 'FIND', 'TELL', 'WANT',
    }
    
    # Find all potential tickers
    matches = re.findall(ticker_pattern, message_upper)
    
    for match in matches:
        # Skip excluded words
        if match in exclude_words:
            continue
        # Skip if less than 2 characters (shouldn't happen with pattern, but safety check)
        if len(match) < 2:
            continue
        # Avoid words that are too common in English (basic heuristic)
        if len(match) == 2 and match not in {'GE', 'GM', 'HP', 'AT', 'LG', 'BK'}:  # Known 2-letter tickers
            # Skip most 2-letter combos unless they're known tickers
            continue
        # Likely a valid ticker
        return match
    
    # Pattern 2: Check for company names
    company_names = {
        'MICROSOFT': 'MSFT',
        'APPLE': 'AAPL', 
        'GOOGLE': 'GOOGL',
        'AMAZON': 'AMZN',
        'NVIDIA': 'NVDA',
        'TESLA': 'TSLA',
        'META': 'META',
        'FACEBOOK': 'META',
    }
    
    for name, ticker in company_names.items():
        if name in message_upper:
            return ticker
    
    # Pattern 3: Check for crypto names
    crypto_names = {
        'BITCOIN': 'BTC',
        'ETHEREUM': 'ETH',
        'BINANCE': 'BNB',
        'RIPPLE': 'XRP',
        'CARDANO': 'ADA',
        'DOGECOIN': 'DOGE',
        'SOLANA': 'SOL',
        'POLYGON': 'MATIC',
        'POLKADOT': 'DOT',
        'AVALANCHE': 'AVAX',
        'CHAINLINK': 'LINK',
        'LITECOIN': 'LTC',
        'UNISWAP': 'UNI',
        'SHIBA': 'SHIB',
    }
    
    for name, ticker in crypto_names.items():
        if name in message_upper:
            return ticker
    
    return None


# Crypto symbols list for detection
CRYPTO_SYMBOLS = {
    'BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'DOGE', 'SOL', 'MATIC', 'DOT', 'AVAX',
    'LINK', 'LTC', 'UNI', 'SHIB', 'ATOM', 'XLM', 'ALGO', 'VET', 'FTM', 'NEAR',
    'BTC-USD', 'ETH-USD', 'BNB-USD', 'XRP-USD', 'ADA-USD', 'DOGE-USD', 'SOL-USD',
    'MATIC-USD', 'DOT-USD', 'AVAX-USD', 'LINK-USD', 'LTC-USD', 'UNI-USD', 'SHIB-USD'
}


def is_crypto(ticker: str) -> bool:
    """Check if a ticker is a cryptocurrency"""
    if not ticker:
        return False
    ticker_upper = ticker.strip().upper()
    # Check direct match or -USD suffix
    return ticker_upper in CRYPTO_SYMBOLS or ticker_upper.endswith('-USD')

def get_stock_data(ticker):
    """
    Fetches 1-month historical price data for the given ticker.
    Returns a DataFrame with OHLCV data.
    """
    try:
        stock = yf.Ticker(ticker)
        # Fetch 1 month of data
        hist = stock.history(period="1mo")
        return hist
    except Exception as e:
        print(f"Error fetching stock data for {ticker}: {e}")
        return pd.DataFrame()

def get_financials(ticker):
    """
    Fetches key financial metrics for the given ticker.
    Returns a dictionary of metrics.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        metrics = {
            "Market Cap": info.get("marketCap", "N/A"),
            "Revenue (TTM)": info.get("totalRevenue", "N/A"),
            "PE Ratio": info.get("trailingPE", "N/A"),
            "Forward PE": info.get("forwardPE", "N/A"),
            "EPS (TTM)": info.get("trailingEps", "N/A"),
            "Profit Margin": info.get("profitMargins", "N/A"),
            "Operating Margin": info.get("operatingMargins", "N/A"),
            "Return on Equity": info.get("returnOnEquity", "N/A"),
            "Current Price": info.get("currentPrice", "N/A"),
            "Target Mean Price": info.get("targetMeanPrice", "N/A"),
            "Recommendation": info.get("recommendationKey", "N/A")
        }
        
        # Format large numbers
        for key, value in metrics.items():
            if isinstance(value, (int, float)) and value > 1e9:
                metrics[key] = f"${value/1e9:.2f} B"
            elif isinstance(value, (int, float)) and value > 1e6:
                metrics[key] = f"${value/1e6:.2f} M"
                
        return metrics
    except Exception as e:
        print(f"Error fetching financials for {ticker}: {e}")
        return {}

def get_news(ticker):
    """
    Fetches recent news for the given ticker using yfinance.
    Returns a list of news dictionaries.
    """
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        
        formatted_news = []
        for item in news:
            formatted_news.append({
                "title": item.get("title"),
                "publisher": item.get("publisher"),
                "link": item.get("link"),
                "published": item.get("providerPublishTime")
            })
        return formatted_news
    except Exception as e:
        print(f"Error fetching news for {ticker}: {e}")
        return []

def get_detailed_financials(ticker):
    """
    Fetches detailed financial statements (Income, Balance Sheet, Cash Flow).
    Returns a dictionary of DataFrames (as strings).
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Get last 2 years/quarters to keep it concise for LLM
        income = stock.income_stmt.iloc[:, :2] if not stock.income_stmt.empty else pd.DataFrame()
        balance = stock.balance_sheet.iloc[:, :2] if not stock.balance_sheet.empty else pd.DataFrame()
        cashflow = stock.cashflow.iloc[:, :2] if not stock.cashflow.empty else pd.DataFrame()
        
        return {
            "income_statement": income.to_string(),
            "balance_sheet": balance.to_string(),
            "cash_flow": cashflow.to_string()
        }
    except Exception as e:
        print(f"Error fetching detailed financials for {ticker}: {e}")
        return {}

def normalize_ticker(ticker):
    """
    Corrects common ticker typos and normalizes input.
    Also converts company names to ticker symbols.
    """
    ticker = ticker.strip().upper()
    
    # Company Names to Ticker Symbols
    company_names = {
        # Tech Giants
        "MICROSOFT": "MSFT",
        "APPLE": "AAPL",
        "GOOGLE": "GOOGL",
        "ALPHABET": "GOOGL",
        "AMAZON": "AMZN",
        "META": "META",
        "FACEBOOK": "META",
        "NVIDIA": "NVDA",
        "TESLA": "TSLA",
        "NETFLIX": "NFLX",
        "AMD": "AMD",
        "INTEL": "INTC",
        "ORACLE": "ORCL",
        "SALESFORCE": "CRM",
        "ADOBE": "ADBE",
        "PAYPAL": "PYPL",
        "UBER": "UBER",
        "AIRBNB": "ABNB",
        "SPOTIFY": "SPOT",
        "ZOOM": "ZM",
        "SHOPIFY": "SHOP",
        "SQUARE": "SQ",
        "BLOCK": "SQ",
        "TWITTER": "TWTR",
        "SNAP": "SNAP",
        "SNAPCHAT": "SNAP",
        "PINTEREST": "PINS",
        "COINBASE": "COIN",
        "ROBINHOOD": "HOOD",
        "PALANTIR": "PLTR",
        
        # Finance
        "JPMORGAN": "JPM",
        "GOLDMAN": "GS",
        "VISA": "V",
        "MASTERCARD": "MA",
        "BERKSHIRE": "BRK-B",
        "BANK OF AMERICA": "BAC",
        "WELLS FARGO": "WFC",
        "MORGAN STANLEY": "MS",
        "CITIGROUP": "C",
        "BLACKROCK": "BLK",
        
        # Consumer
        "WALMART": "WMT",
        "COSTCO": "COST",
        "TARGET": "TGT",
        "NIKE": "NKE",
        "STARBUCKS": "SBUX",
        "MCDONALDS": "MCD",
        "COCA-COLA": "KO",
        "PEPSI": "PEP",
        "DISNEY": "DIS",
        
        # Healthcare
        "JOHNSON": "JNJ",
        "PFIZER": "PFE",
        "MODERNA": "MRNA",
        "UNITEDHEALTH": "UNH",
        
        # Others
        "BOEING": "BA",
        "EXXON": "XOM",
        "CHEVRON": "CVX",
    }
    
    # Check company names first
    if ticker in company_names:
        corrected = company_names[ticker]
        print(f"Company Name Correction: '{ticker}' -> '{corrected}'")
        return corrected
    
    # Common Typos / Mappings
    corrections = {
        # Stock Typos
        "APPL": "AAPL",  # Apple
        "TSMC": "TSM",   # Taiwan Semiconductor (NYSE)
        "GOOG": "GOOGL", # Alphabet Class A (often preferred)
        "FB": "META",    # Meta Platforms
        "TWTR": "TWTR",  # Twitter (Delisted, but good to keep for legacy)
        
        # Crypto Symbols (auto-append -USD)
        "BTC": "BTC-USD",   # Bitcoin
        "ETH": "ETH-USD",   # Ethereum
        "BNB": "BNB-USD",   # Binance Coin
        "XRP": "XRP-USD",   # Ripple
        "ADA": "ADA-USD",   # Cardano
        "DOGE": "DOGE-USD", # Dogecoin
        "SOL": "SOL-USD",   # Solana
        "MATIC": "MATIC-USD", # Polygon
        "DOT": "DOT-USD",   # Polkadot
        "AVAX": "AVAX-USD", # Avalanche
    }
    
    if ticker in corrections:
        corrected = corrections[ticker]
        print(f"Smart Correction: '{ticker}' -> '{corrected}'")
        return corrected
        
    return ticker

