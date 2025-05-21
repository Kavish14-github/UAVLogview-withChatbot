from dotenv import load_dotenv
import os

load_dotenv()
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from chat.agent import chat_with_log
from parser.mavlog_parser import parse_log_file
import uuid

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
    return {"session_id": session_id, "message": "Log parsed successfully."}

@app.post("/chat")
def chat(session_id: str = Form(...), query: str = Form(...)):
    try:
        parsed = session_logs.get(session_id)
        if not parsed:
            return {"error": "Invalid session ID"}

        response = chat_with_log(query, parsed)
        return {"response": response}

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {"error": f"Exception occurred: {str(e)}"}


