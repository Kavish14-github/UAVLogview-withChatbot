import openai
import os
import json

openai.api_key = os.getenv("OPENAI_API_KEY")

SYSTEM_PROMPT = """
You are an expert UAV flight log analyst working with telemetry data extracted from ArduPilot .bin logs.

You receive:
- Structured telemetry grouped by message types (e.g., GPS, ATT, BAT, ERR)
- A user question about flight behavior

Your task:
- Answer clearly and concisely using actual telemetry
- Detect anomalies or explain uncertainties
- Use judgment (not hard rules) to spot issues like:
  • Sudden drops in altitude
  • Irregular battery usage
  • Missing GPS fixes
  • Errors or subsystem faults

If needed, mention:
- When data is incomplete or inconclusive
- Any patterns that suggest risks or unsafe behavior

Be technical, factual, and helpful — like reporting to a flight safety officer.
"""

def extract_samples(messages_dict, max_per_type=10):
    samples = {}
    for msg_type, entries in messages_dict.items():
        samples[msg_type] = entries[:max_per_type]
    return samples


# ========== ANOMALY CHECKERS ==========

def detect_altitude_spikes(alt_data):
    anomalies = []
    for i in range(1, len(alt_data)):
        t1, alt1 = alt_data[i-1]["TimeUS"], alt_data[i-1].get("Alt", 0)
        t2, alt2 = alt_data[i]["TimeUS"], alt_data[i].get("Alt", 0)
        dt = (t2 - t1) / 1e6
        dalt = alt2 - alt1
        if abs(dalt) > 10 and dt < 2:
            anomalies.append({
                "from_time": t1,
                "to_time": t2,
                "altitude_change": dalt,
                "duration_sec": dt
            })
    return anomalies


def detect_voltage_drops(bat_data):
    anomalies = []
    for i in range(1, len(bat_data)):
        v1 = bat_data[i-1].get("Volt", 0)
        v2 = bat_data[i].get("Volt", 0)
        drop = v1 - v2
        if drop > 1.5:
            anomalies.append({
                "from_volt": v1,
                "to_volt": v2,
                "drop": round(drop, 2),
                "time": bat_data[i].get("TimeUS")
            })
    return anomalies


def detect_gps_loss(gps_data):
    losses = []
    for g in gps_data:
        if g.get("NSats", 8) < 5 or g.get("HDop", 1) > 3:
            losses.append(g)
    return losses


def detect_errors(err_data):
    return [e for e in err_data if e.get("ECode") not in (0, None)]


# ========== MAIN CHAT FUNCTION ==========
def safe_json(obj):
    def default(o):
        if hasattr(o, 'tolist'): 
            return o.tolist()
        if hasattr(o, '__str__'):
            return str(o)
        return o
    return json.dumps(obj, indent=2, default=default)

def chat_with_log(query: str, parsed_data: dict) -> str:
    all_messages = parsed_data.get("messages", {})
    if not all_messages:
        return "No telemetry data found in uploaded log."

    query_lower = query.lower()
    hint_blocks = []
    relevant_types = set()

    # === Smart Anomaly Hints ===
    if "altitude" in query_lower and "CTUN" in all_messages:
        relevant_types.add("CTUN")
        spikes = detect_altitude_spikes(all_messages["CTUN"])
        if spikes:
            hint_blocks.append(f"⚠️ **Altitude Anomalies:**\n{safe_json(spikes[:3])}")

    if "voltage" in query_lower and "BAT" in all_messages:
        relevant_types.add("BAT")
        drops = detect_voltage_drops(all_messages["BAT"])
        if drops:
            hint_blocks.append(f"⚠️ **Voltage Drops:**\n{safe_json(drops[:3])}")

    if "gps" in query_lower and "GPS" in all_messages:
        relevant_types.add("GPS")
        losses = detect_gps_loss(all_messages["GPS"])
        if losses:
            hint_blocks.append(f"⚠️ **GPS Signal Issues:**\n{safe_json(losses[:3])}")

    if "error" in query_lower and "ERR" in all_messages:
        relevant_types.add("ERR")
        errors = detect_errors(all_messages["ERR"])
        if errors:
            hint_blocks.append(f"⚠️ **Subsystem Errors:**\n{safe_json(errors[:5])}")

    # Fallback: if no relevant types found, show just 2-3 core types
    if not relevant_types:
        core = ["GPS", "BAT", "ATT"]
        relevant_types.update([t for t in core if t in all_messages])

    # === Compact Sample Section ===
    telemetry_preview = ""
    for msg_type in relevant_types:
        entries = all_messages.get(msg_type, [])[:3]
        if entries:
            telemetry_preview += f"\n\n📘 **{msg_type} Sample:**\n{safe_json(entries)}"

    # === Prompt Assembly ===
    prompt = f"""You are a flight log analysis assistant.

User query: {query}

Available message types: {list(all_messages.keys())}
{"".join(["\n\n" + h for h in hint_blocks])}

=== Telemetry Samples ===
{telemetry_preview}
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error: {str(e)}"
