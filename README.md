# UAVLogview-withChatbot

This is an enhanced fork of the original [UAV Log Viewer](https://plot.ardupilot.org/) that integrates an **AI-powered chatbot assistant** capable of understanding and reasoning about parsed MAVLink `.BIN` flight logs.

---

## 🔧 Project Structure

UAVLogview-withChatbot/
├── UAVLogViewer/ # Vue-based log visualization tool
├── chatbot_backend/ # FastAPI server handling chatbot and log parsing

---

## ✨ Features

- Upload and analyze `.BIN` UAV flight logs.
- Beautiful log visualization using Plotly & Cesium.
- Chatbot with LLM (OpenAI or compatible) support.
- Agentic anomaly detection and reasoning on flight data.
- Interactive Q&A:
  - "What was the max altitude?"
  - "When was the first GPS loss?"
  - "Were there critical mid-flight errors?"
  - "How long did the flight last?"
  - "Did RC signal drop at any point?"

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
Access the frontend at: http://localhost:8080

##  🧠 Backend Setup (FastAPI + Python)

Prerequisites:
Python 3.9+
pip

Install & Run:

```bash
cd chatbot_backend
python -m venv venv
```

# Activate the virtual environment:

# On Windows:
```bash
venv\Scripts\activate
python -m uvicorn main:app --reload
```
# On Mac/Linux:
```bash
source venv/bin/activate

pip install -r requirements.txt

uvicorn main:app --reload
```
The backend API runs on: http://localhost:8000

📤 Upload + Chatbot Flow
Launch both the UAVLogViewer and chatbot_backend.

In the UI, locate the Chatbot (bottom-right).

First, upload a .BIN flight log.

Then, ask questions about the flight.

🧠 API Endpoints
Method	Endpoint	Description
POST	/upload	Uploads the .BIN log file
POST	/chat	Sends queries to the chatbot (LLM)

🧪 Example Chatbot Queries
"What was the highest altitude reached?"

"Were there any GPS signal losses?"

"How long did the flight last?"

"What battery voltage drops were recorded?"

"List all critical subsystem errors mid-flight."

"Spot any unusual flight behavior?"

🤖 AI Integration Notes
Uses OpenAI/GPT or compatible LLM API.

Dynamically interprets MAVLink data and infers anomalies.

Encourages reasoning (not hard-coded rules).

Prompts hint at patterns, inconsistencies, thresholds, etc.

🧰 Technologies Used
Frontend: Vue.js, Webpack, Cesium, Plotly

Backend: FastAPI, Pydantic

LLM API: OpenAI (or equivalent)

ESLint, Babel, Axios

📁 Forked From
https://github.com/ArduPilot/UAVLogViewer

👤 Author
Kavish14
GitHub: @Kavish14-github
