# Stock Analyst AI 📊

ระบบ AI วิเคราะห์หุ้นและ Cryptocurrency อัจฉริยะ ด้วย **Multi-Agent System** ที่ทำงานร่วมกันเหมือนทีมวิเคราะห์มืออาชีพ ขับเคลื่อนด้วย **LangGraph**

## 🌟 ฟีเจอร์เด่น

- **Multi-Agent Architecture**: ใช้ AI Analyst 5 ด้าน (Technical, Fundamental, News, Social, Risk) ทำงานร่วมกัน
- **LangGraph Orchestration**: ควบคุม Flow การทำงานด้วย Graph Workflow ที่ซับซ้อนและแม่นยำ
- **Bull vs Bear Debate**: จำลองการโต้เถียงระหว่างมุมมอง "เชียร์ซื้อ" และ "เชียร์ขาย"
- **Risk Judgment**: มีระบบไต่สวนความเสี่ยง (Risk Judge) เพื่อประเมินความปลอดภัยก่อนลงทุน
- **Interactive UI**: หน้าเว็บ Chat ที่ใช้งานง่าย รองรับ Streaming Response และ Follow-up questions
- **Crypto Support**: รองรับทั้งหุ้น US และ Cryptocurrency

## 🏗️ โครงสร้างระบบ

ระบบประกอบด้วย 2 ส่วนหลัก:

1.  **Backend (`/backend`)**:
    - Build with **Python** & **FastAPI**
    - Orchestrated by **LangGraph**
    - Uses **Gemini 2.0 Flash** / **GPT-4o** as LLM
2.  **Frontend (`/chat-ui`)**:
    - Build with **SvelteKit**
    - Chat Interface similar to ChatGPT

```
StockAnalystAI/
├── backend/
│   ├── api/openai_server.py  # API Entry Point
│   ├── src/
│   │   ├── graph.py         # LangGraph Workflow Definition
│   │   ├── agents/          # AI Agents logic
│   └── requirements.txt
└── chat-ui/                  # Frontend Application
```

## 🚀 การติดตั้งและใช้งาน

### 1. Backend Setup

```bash
cd backend

# 1. สร้าง Virtual Environment
python -m venv venv
source venv/bin/activate  # Mac/Linux
# หรือ venv\Scripts\activate  # Windows

# 2. ติดตั้ง Dependencies
pip install -r requirements.txt

# 3. ตั้งค่า API Keys
# สร้างไฟล์ .env ในโฟลเดอร์ backend และใส่ค่าตามนี้:
# GEMINI_API_KEY=your_key_here
# TAVILY_API_KEY=your_key_here
```

### 2. Frontend Setup

```bash
cd chat-ui

# ติดตั้ง Node modules
npm install
```

### 3. Start System

**Step 1: รัน Backend**
```bash
# ใน Terminal ที่ 1 (folder backend)
python api/openai_server.py
```
*รอจนขึ้น: `Uvicorn running on http://0.0.0.0:8090`*

**Step 2: รัน Frontend**
```bash
# ใน Terminal ที่ 2 (folder chat-ui)
npm run dev
```
*รอจนขึ้น: `Local: http://localhost:5173`*

**Step 3: ใช้งาน**
- เปิด Browser ไปที่ **http://localhost:5173**
- เริ่มคุยกับ AI ได้เลย!

## 💡 ตัวอย่างคำสั่ง

- "วิเคราะห์หุ้น NVDA"
- "ดูแนวโน้ม Bitcoin"
- "ขอวิเคราะห์ความเสี่ยง TSLA"
- "สรุปงบการเงิน APPLE ให้หน่อย"

## 🛠️ Tech Stack

- **LangGraph** & **LangChain**: Agent Orchestration
- **FastAPI**: Backend API
- **Google Gemini / OpenAI**: LLM Models
- **Tavily**: Search Tool
- **SvelteKit**: Frontend Framework
- **MongoDB**: (Optional) Data Persistence

## License

MIT
