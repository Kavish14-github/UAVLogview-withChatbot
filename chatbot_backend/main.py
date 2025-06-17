from dotenv import load_dotenv
import os

load_dotenv()
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from chat.agent import chat_with_log, compute_flight_risk
from telemetry_parser.mavlog_parser import parse_log_file
import uuid
from collections import defaultdict

print("Loaded API key:", os.getenv("OPENAI_API_KEY"))

app = FastAPI()
session_cache = {} 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# session_id => list of messages
chat_histories = {}  


session_logs = {}

@app.post("/upload")
async def upload_log(file: UploadFile = File(...)):
    contents = await file.read()
    session_id = str(uuid.uuid4())
    filepath = f"tmp/{session_id}.bin"
    os.makedirs("tmp", exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(contents)
    parsed_data = parse_log_file(filepath)
    session_logs[session_id] = parsed_data
    chat_histories[session_id] = []

    return {"sessionNum": session_id, "message": "Log parsed successfully."}


@app.post("/chat")
async def chat(sessionNum: str = Form(...), query: str = Form(...)):
    parsed = session_logs.get(sessionNum)
    if not parsed:
        raise HTTPException(status_code=400, detail="Invalid or expired session ID")

    history = chat_histories.setdefault(sessionNum, [])

    trimmed_history = history[-2:]
    
    # print(f"Session: {sessionNum}")
    # print(f"Chat history so far: {trimmed_history}")

    messages = trimmed_history  + [{"role": "user", "content": query}]

    response_text = chat_with_log(query, parsed, messages)
    history.append({"role": "user", "content": query})
    history.append({"role": "assistant", "content": response_text})

    return {
        "response": response_text,
        "sessionNum": sessionNum
    }


@app.post("/risk_score")
async def risk_score(sessionNum: str = Form(...)):
    parsed = session_logs.get(sessionNum)
    if not parsed:
        return {"error": "Invalid session number"}
    risk = compute_flight_risk(parsed)
    return risk


