import openai
import os
import json

openai.api_key = os.getenv("OPENAI_API_KEY")

SYSTEM_PROMPT = """
You are an expert UAV flight log analyst working with telemetry data extracted from ArduPilot .bin logs.

The data includes messages like GPS, ATT (attitude), BATTERY_STATUS, ERR, RCIN, etc. Refer to the official ArduPilot message documentation to understand the meaning of each field:
→ https://ardupilot.org/plane/docs/logmessages.html

Your job is to analyze flight behavior and answer user questions using available telemetry data.

Rather than using rigid rules, apply expert judgment to identify:
- Sudden changes in altitude or pitch/yaw/roll (e.g., a drop of 50m in 3 seconds)
- Irregular battery usage patterns or voltage drops
- Inconsistent or lost GPS signal
- Warnings or error flags (e.g., subsystem errors, arming failures)
- Patterns that suggest pilot control loss or autopilot anomalies

If a value appears questionable or suggests something wrong, mention it and suggest possible causes.

You may:
- Compare trends and time sequences
- Identify gaps or missing signals
- Flag anomalies
- Estimate safe vs risky behavior ranges
- Interpret changes (e.g., “voltage dropped ~1.2V in 5s, which is unusual”)

If data is insufficient to conclude, say so clearly. Avoid assumptions or hallucinations.

Respond clearly, as if briefing a mission commander or flight safety officer.
"""


def extract_messages_by_type(messages_dict, msg_type, max_count=20):
    return messages_dict.get(msg_type, [])[:max_count]

def detect_altitude_spikes(alt_data):
    anomalies = []
    for i in range(1, len(alt_data)):
        t1, alt1 = alt_data[i-1]["TimeUS"], alt_data[i-1].get("Alt", 0)
        t2, alt2 = alt_data[i]["TimeUS"], alt_data[i].get("Alt", 0)
        delta_t = (t2 - t1) / 1e6
        delta_alt = alt2 - alt1
        if abs(delta_alt) > 10 and delta_t < 2:
            anomalies.append({
                "from_time": t1, "to_time": t2,
                "altitude_change": delta_alt,
                "duration_sec": delta_t
            })
    return anomalies

def chat_with_log(query: str, parsed_data: dict) -> str:
    all_messages = parsed_data.get("messages", {})

    gps_data = extract_messages_by_type(all_messages, "GPS")
    bat_data = extract_messages_by_type(all_messages, "BAT")
    att_data = extract_messages_by_type(all_messages, "ATT")
    alt_data = extract_messages_by_type(all_messages, "ALT")
    rcin_data = extract_messages_by_type(all_messages, "RCIN")
    err_data = extract_messages_by_type(all_messages, "ERR")

    hint = ""
    if "altitude" in query.lower():
        spikes = detect_altitude_spikes(alt_data)
        if spikes:
            hint += f"\nPotential altitude anomalies: {json.dumps(spikes[:5], indent=2)}"

    user_prompt = f"""
    User question: {query}

    Available message types: {list(all_messages.keys())}

    {hint}

    GPS sample:
    {json.dumps(gps_data[:5], indent=2)}

    ALT sample:
    {json.dumps(alt_data[:5], indent=2)}

    ATT sample:
    {json.dumps(att_data[:5], indent=2)}

    BATTERY sample:
    {json.dumps(bat_data[:5], indent=2)}

    RCIN sample:
    {json.dumps(rcin_data[:5], indent=2)}

    ERR sample:
    {json.dumps(err_data[:5], indent=2)}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error: {str(e)}"
