# Stock Analyst AI 📊

ระบบ AI วิเคราะห์หุ้นและ Crypto ด้วย Multi-Agent System

## โครงสร้างโปรเจค

```
StockAnalystAI/
├── backend/          # API Server (FastAPI)
│   ├── api/          # OpenAI-compatible API
│   ├── src/          # Agent logic
│   ├── .env          # API keys
│   └── requirements.txt
└── chat-ui/          # Frontend (HuggingFace Chat-UI)
```

## การติดตั้ง

### 1. Backend (API Server)

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Frontend (Chat-UI)

```bash
cd chat-ui
npm install
```

### 3. ตั้งค่า Environment Variables

**backend/.env:**
```
GOOGLE_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=trading-bot
```

**chat-ui/.env.local:**
```
MONGODB_URL=mongodb://localhost:27017/chat-ui
OPENID_CONFIG=""
OPENAI_API_KEY=local-dev-key
OPENAI_BASE_URL=http://localhost:8090/v1
OPENAI_CHAT_MODEL=stock-analyst
```

## การใช้งาน

### เริ่มต้น Backend

```bash
cd backend
python api/openai_server.py
```

Server จะรันที่ http://localhost:8090

### เริ่มต้น Frontend

```bash
cd chat-ui
npm run dev
```

เปิด http://localhost:5173 ในเบราว์เซอร์

## ฟีเจอร์

- ✅ วิเคราะห์หุ้น US (AAPL, NVDA, TSLA, etc.)
- ✅ วิเคราะห์ Crypto (BTC, ETH, SOL, DOGE, etc.)
- ✅ Multi-Agent System (Market, Fundamentals, News, Social, Risk)
- ✅ Bull vs Bear Debate
- ✅ Risk Judge
- ✅ Follow-up Questions (ถามต่อได้หลังวิเคราะห์)
- ✅ Streaming Responses
- ✅ MongoDB Storage

## ตัวอย่างการใช้งาน

```
วิเคราะห์ NVDA
ดู Bitcoin
วิเคราะห์ SOL
สรุปสั้นๆ
ความเสี่ยงหลักๆ คืออะไร
```

## License

MIT
