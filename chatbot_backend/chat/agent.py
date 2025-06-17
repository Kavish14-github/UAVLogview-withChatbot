import openai
import os
import json
import faiss
import numpy as np
import time

openai.api_key = os.getenv("OPENAI_API_KEY")

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

SYSTEM_PROMPT = """
You are an expert UAV flight log analyst with deep expertise in ArduPilot systems and flight safety. Your analysis should rely on contextual reasoning using telemetry trends, flight dynamics, and system behavior, guided by the official ArduPilot documentation (https://ardupilot.org/plane/docs/logmessages.html).

You receive:
- Structured telemetry grouped by message types (e.g., GPS, ATT, BAT, ERR)
- A user question about flight behavior

You are not limited to strict rules; instead, reason dynamically. Consider context, time windows, and behavioral consistency when analyzing anomalies or drawing conclusions. Recognize that thresholds can vary across aircraft, mission profiles, and flight phases.

Reference Guidelines:
1. Message Types and Interpretations:
   - GPS: Global position and satellite info
     * NSats: Number of satellites (nominal 6–12)
     * HDop: Horizontal dilution of precision (good <2.0, tolerable <5.0)
     * Alt: Altitude in meters (evaluate in context of baro vs GPS vs descent/ascent)

   - ATT: Attitude dynamics
     * Roll, Pitch, Yaw in radians (dynamic stability more important than fixed thresholds)

   - BAT: Battery metrics
     * Volt, Curr, Remaining (%); consider voltage sag under load, recovery after demand
     * Pay attention to trends, not just absolute drops

   - ERR: Error codes
     * ECode/Subsys: Interpret within operational sequence; some messages may be benign or transient

2. Analytical Approach:
   - Prioritize trends, rate-of-change, and systemic inconsistencies
   - Avoid fixed thresholds (e.g., "drop > 10m in 1s") unless justified by supporting context
   - Assess interdependencies (e.g., GPS degradation during attitude spikes or current surge during drop)

Your analysis must be structured as follows:

BRIEF SUMMARY (always respond with this first)
   - In 2–3 sentences, offer a clear verdict: Was the flight stable, did any major anomaly occur, and what stands out?

EXECUTIVE SUMMARY
   • High-level narrative of the flight
   • Key anomalies or flags
   • Risk assessment and flight safety verdict

DETAILED ANALYSIS
   a) GPS & Positioning
      - Describe consistency or disruptions in GPS data
      - Comment on number of satellites, HDop trends, altitude behaviors
      - Interpret positional stability or deviation from expected path

   b) Battery & Power
      - Observe current draw and voltage behavior over flight phases
      - Highlight signs of overdraw, poor recovery, or critical depletion
      - Assess power system reliability

   c) Attitude & Dynamics
      - Comment on roll/pitch/yaw consistency
      - Detect control instability, unusual oscillations, or diverging responses
      - Link with external conditions (wind, GPS loss, manual input)

   d) Errors & System Messages
      - List relevant ERR messages and potential implications
      - Distinguish between critical failures vs transient notices

ANOMALY DETECTION
   • Discuss irregularities that deviate from normal operational patterns
   • Focus on trends (e.g., gradually increasing battery sag, sudden GPS drop)
   • Reason about what is *unusual* relative to expected UAV behavior

CORRELATION ANALYSIS
   • Analyze interrelated issues (e.g., altitude drop following current surge)
   • Note if one anomaly likely caused another (cause-effect reasoning)
   • Consider temporal proximity and subsystem relationships

RECOMMENDATIONS
   a) Immediate Actions
      - What should be addressed before next flight?

   b) Preventive Measures
      - What maintenance, calibration, or tuning is advisable?

   c) Further Investigation
      - What data needs review or flight testing?

   d) References
      - Refer to any ArduPilot documentation or log interpretation resources

Formatting Rules:
- Use numbered and lettered sections only (1, 2... a, b...)
- Use bullet points (•) and dashes (-) as needed
- DO NOT use any markdown symbols, including **, __, #, *, or backticks (`).
- Use plain text formatting only. Do NOT use bold, italics, or headings.
- For section headings, use normal capital letters (e.g., "1. BRIEF SUMMARY").

Your goal: Be technically deep, situationally aware, and guidance-oriented.
"""

# --- Vector Store Globals ---
index = faiss.IndexFlatL2(EMBEDDING_DIM)
chunk_texts = []

# --- Embedding Function ---
def embed_text(text):
    response = openai.Embedding.create(input=text, model=EMBEDDING_MODEL)
    # time.sleep(1.1)  # Prevent API rate limit
    return response['data'][0]['embedding']

def default_json(obj):
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")  # fallback for decoding
    if hasattr(obj, "__str__"):
        return str(obj)
    return f"<<non-serializable: {type(obj).__name__}>>"

# --- Build Vector Store from Log Data ---
def build_vector_store(parsed_data):
    global chunk_texts, index
    all_messages = parsed_data.get("messages", {})
    preferred_order = ["ERR", "GPS", "ATT", "BAT", "CTUN", "BARO"]
    other_keys = [k for k in all_messages.keys() if k not in preferred_order]
    all_keys = preferred_order + sorted(other_keys)

    for msg_type in all_keys:
        entries = all_messages.get(msg_type, [])
        for i in range(0, len(entries), 100):
            chunk_entries = entries[i:i + 100]
            chunk_text = f"== {msg_type} CHUNK ==\n" + json.dumps(chunk_entries[:10], default=default_json)
            embedding = embed_text(chunk_text)
            index.add(np.array([embedding], dtype=np.float32))
            chunk_texts.append(chunk_text)

# --- Retrieve Most Relevant Chunks Based on User Query ---
def retrieve_relevant_chunks(query, top_k=3):
    query_embedding = embed_text(query)
    D, I = index.search(np.array([query_embedding], dtype=np.float32), top_k)
    results = []
    for score, i in zip(D[0], I[0]):
        if i < len(chunk_texts):
            results.append((score, chunk_texts[i]))
    return results

# --- Chat Function with RAG ---
def chat_with_log(query: str, parsed_data: dict, chat_history: list = None) -> str:
    if chat_history is None:
        chat_history = []

    if not chunk_texts or index.ntotal == 0:
        print("\n==>Building vector store<==\n")
        build_vector_store(parsed_data)
        print("\n==>Vector store built successfully.<==\n")

    relevant_chunks = retrieve_relevant_chunks(query)
    context = "\n\n".join([chunk for _, chunk in relevant_chunks])
    
    print("\n Top Matching Chunks for Query:")
    for idx, (score, chunk) in enumerate(relevant_chunks):
        preview = chunk.split("\n")[0] 
        print(f"  {idx+1}. {preview}  (distance: {score:.4f})")

    prompt = f"""You are a UAV flight log assistant.

User question: \"{query}\"

Here are relevant telemetry chunks:
{context}

Please answer in detail using the following format:

1. Executive Summary
2. Detailed Analysis
3. Anomaly Detection
4. Correlation Analysis
5. Recommendations

Formatting Rules:
- Use numbered and lettered sections only (1, 2... a, b...)
- Use bullet points (•) and dashes (-) as needed
- Do not strictly use markdown symbols (e.g., do not use **, ##, etc.)

Your goal: Be technically deep, situationally aware, and guidance-oriented.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *chat_history,
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=3000
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error: {str(e)}"


def compute_flight_risk(parsed_data):
    score = 0
    details = []
    messages = parsed_data.get("messages", {})

    # --- GPS Risk ---
    gps_data = messages.get("GPS", [])
    gps_issues = [
        g for g in gps_data if g.get("NSats", 8) < 5 or g.get("HDop", 1) > 3
    ]
    if gps_issues:
        score += 40
        details.append("GPS signal quality issues detected (low NSats or high HDop).")

    # --- Battery Voltage Drop ---
    bat_data = messages.get("BAT", [])
    for i in range(1, len(bat_data)):
        v1 = bat_data[i-1].get("Volt", 0)
        v2 = bat_data[i].get("Volt", 0)
        if v1 - v2 > 1.5:
            score += 30
            details.append("Significant battery voltage drop detected.")
            break

    # --- Subsystem Errors ---
    err_data = messages.get("ERR", [])
    err_codes = [e for e in err_data if e.get("ECode") not in (0, None)]
    if err_codes:
        score += 50
        details.append(f"{len(err_codes)} critical error messages found in ERR logs.")

    # --- Altitude Spikes ---
    ctun_data = messages.get("CTUN", [])
    for i in range(1, len(ctun_data)):
        alt1 = ctun_data[i-1].get("Alt", 0)
        alt2 = ctun_data[i].get("Alt", 0)
        if abs(alt2 - alt1) > 10:
            score += 20
            details.append("Sudden altitude fluctuation (>10m) detected.")
            break

    # --- Risk Interpretation ---
    if score <= 30:
        risk_level = "Low"
    elif score <= 60:
        risk_level = "Moderate"
    else:
        risk_level = "High"

    return {
        "score": score,
        "riskLevel": risk_level,
        "details": details
    }
