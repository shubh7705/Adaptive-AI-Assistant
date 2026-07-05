# ModelRouter AI (Adaptive AI Assistant)

ModelRouter AI is an intelligent, production-ready Multi-Model AI Router. Instead of sending every request to a single LLM, it acts as an **AI Operating System**, automatically detecting user intent, optimizing prompts, evaluating costs, and routing the request to the best possible model while maximizing quality and minimizing latency.

---

## 🌟 Key Features

- **Intent Detection Agent**: Analyzes prompts to detect the task (math, coding, creative) and complexity.
- **Cost Optimization Agent**: Uses local tokenization (`tiktoken`) to calculate budgets and prevent expensive models from being wasted on simple queries.
- **Model Selection Agent**: Dynamically scores and selects the best model from the active registry based on `Score = Quality + Latency + Cost + Availability`.
- **Live Analytics Dashboard**: Real-time Next.js visualizations (using Recharts) for token usage over time, cache-hit rates, and estimated cost distribution grouped by AI provider.
- **Real-Time Intent Logging**: Automatically logs user queries and detected intent tasks directly to a CSV file (`chat_intents.csv`) for offline dataset generation and training.
- **Exact-Match Redis Caching**: Intercepts identical user queries before they hit external provider APIs, serving them instantly from Redis to guarantee <50ms latency and zero API cost.
- **Prompt Optimization Agent**: Automatically rewrites poor prompts for better generation.
- **Tool Calling Framework**: Equips LLMs with calculators, web search, and Python executors.
- **RAG Pipeline**: Native FAISS integration to chat with your PDFs, Word documents, and Markdown files.
- **Quality Evaluation Gate**: Grades AI responses for accuracy and hallucination before returning them to the user.
- **Fallback Router**: Instantly retries with a secondary model if the primary model fails or hallucinates.

---

## 🏗️ Architecture Stack

- **Orchestration**: LangGraph, LangChain
- **Backend API**: FastAPI (Python 3.12), AsyncIO
- **Database**: PostgreSQL (SQLAlchemy ORM)
- **Short-Term Memory & Cache**: Redis
- **Frontend Dashboard**: Next.js 14, TypeScript, TailwindCSS, shadcn/ui
- **Observability**: Prometheus, Loguru

---

## 🚀 Quickstart (Docker)

The easiest way to run ModelRouter AI is using Docker Compose.

1. **Set your API Keys**
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   DEEPSEEK_API_KEY=your_deepseek_api_key_here
   JWT_SECRET_KEY=generate_a_secure_random_string
   ```

2. **Boot the System**
   ```bash
   docker compose up -d --build
   ```

3. **Access the Services**
   - **Frontend UI**: http://localhost:3000
   - **Backend API Docs**: http://localhost:8000/docs
   - **Prometheus Metrics**: http://localhost:8000/metrics

---

## 💻 Local Development (Without Docker)

### 1. Backend Setup
```bash
# We use `uv` for lightning-fast dependency resolution
pip install uv

# Install dependencies
uv pip install -r pyproject.toml

# Run the API
python scripts/run_backend.py
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 📡 API Reference

You can use ModelRouter AI exactly like the OpenAI API in your own external applications.

### Chat Streaming Endpoint
```bash
curl -X POST "http://localhost:8000/api/v1/chat/stream" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "query": "Write a python script to scrape a website.",
           "session_id": "user_session_123"
         }'
```
*Returns Server-Sent Events (SSE) token-by-token.*

### Register a New Model
```bash
curl -X POST "http://localhost:8000/api/v1/registry/" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "name": "gpt-4o",
           "provider": "openai",
           "cost_per_1k_tokens": 0.01,
           "supports_vision": true,
           "supports_tools": true
         }'
```

---

## 🛡️ License

MIT License
