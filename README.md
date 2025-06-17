# UAVLogview-withChatbot

This is an enhanced fork of the original [UAV Log Viewer](https://plot.ardupilot.org/) that integrates an **AI-powered chatbot assistant** capable of understanding and reasoning about parsed MAVLink `.BIN` flight logs using Retrieval-Augmented Generation (RAG).

---

## 🔧 Project Structure

```
UAVLogview-withChatbot/
├── UAVLogViewer/       # Vue-based log visualization tool
├── chatbot_backend/    # FastAPI + RAG backend for chat and analysis
```

---

## ✨ Key Features

- 📤 Upload and analyze `.BIN` UAV flight logs
- 📊 Interactive 3D visualization (Cesium, Plotly)
- 🤖 LLM-powered chatbot that:
  - Understands ArduPilot log structures
  - Performs anomaly detection (GPS loss, battery sag, altitude spikes)
  - Provides system-level diagnostics and explanations
  - Leverages OpenAI embeddings and FAISS for RAG-based retrieval
- 🔍 Sample Queries:
  - "What was the max altitude?"
  - "When was the first GPS loss?"
  - "Any critical mid-flight errors?"
  - "How long did the flight last?"
  - "Did RC signal drop?"

---

## 🖥️ Frontend Setup (Vue.js)

### Prerequisites
- Node.js v14 or later
- npm

### Install & Run
```bash
cd UAVLogViewer
npm install
npm run dev
```
Access the frontend at: [http://localhost:8080](http://localhost:8080)

---

## 🧠 Backend Setup (FastAPI + RAG + OpenAI)

### Prerequisites
- Python 3.9+
- pip

### Install & Run
```bash
cd chatbot_backend
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload
```
Backend runs at: [http://localhost:8000](http://localhost:8000)

---

## 🤖 AI Flow (RAG Architecture)

- Parsed `.BIN` logs are chunked into 100-line telemetry segments
- Chunks are embedded using OpenAI `text-embedding-3-small`
- FAISS stores embeddings locally in-memory for fast similarity search
- User query is embedded and matched to top-K relevant chunks
- Contextual chunks + query are sent to GPT-4 for final reasoning

---

## 🚀 API Endpoints

| Method | Endpoint  | Description                     |
|--------|-----------|---------------------------------|
| POST   | /upload   | Uploads the `.BIN` log file     |
| POST   | /chat     | Sends a query to the chatbot    |

---

## 🧪 Example Questions
- "What altitude spikes occurred?"
- "Any GPS signal anomalies?"
- "Show subsystem errors mid-flight"
- "Highlight unusual battery behavior"
- "Was the flight stable?"

---

## 🧰 Tech Stack
- **Frontend**: Vue.js, Cesium, Plotly, Webpack
- **Backend**: FastAPI, FAISS, OpenAI, Pydantic
- **LLM Integration**: GPT-4 Turbo via OpenAI API
- **Vector Search**: FAISS + embeddings (1536-dim)
- **Others**: ESLint, Babel, Axios, CORS

---

## 📁 Forked From
[https://github.com/ArduPilot/UAVLogViewer](https://github.com/ArduPilot/UAVLogViewer)

## 👤 Author
**Kavish14**
GitHub: [@Kavish14-github](https://github.com/Kavish14-github)
