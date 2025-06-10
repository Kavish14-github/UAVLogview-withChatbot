from pymavlink import mavutil
from collections import defaultdict


def parse_log_file(file_path: str, max_samples: int = 100):
    """
    Parse a .bin log file and extract structured telemetry data.

    Args:
        file_path (str): Path to the .bin file
        max_samples (int): Max number of entries per message type to extract

    Returns:
        dict: Parsed and structured flight data
    """
    # mav = mavutil.mavlink_connection(file_path)
    # data = defaultdict(list)
    # counts = defaultdict(int)

    # important_msgs = {
    #     "GPS": ["TimeUS", "Lat", "Lng", "Alt", "Spd", "NSats", "HDop", "Yaw"],
    #     "ATT": ["TimeUS", "Roll", "Pitch", "Yaw", "ErrRP", "ErrYaw", "AEKF"],
    #     "BAT": ["TimeUS", "Volt", "Curr", "CurrTot", "VoltR", "Temp"],
    #     "MODE": ["TimeUS", "Mode", "ModeNum"],
    #     "ERR": ["TimeUS", "Subsys", "ECode"],
    #     "MSG": ["TimeUS", "Message"],
    #     "CTUN": ["TimeUS", "ThO", "Alt", "BAlt", "DesAlt", "TAlt", "DAlt"],
    #     "NTUN": ["TimeUS", "NavRoll", "NavPitch", "NavYaw", "DesSpeed"],
    #     "XKF1": ["TimeUS", "PN", "PE", "PD", "VX", "VY", "VZ", "Yaw"],
    # }

    # while True:
    #     msg = mav.recv_match(blocking=False)
    #     if msg is None:
    #         break

    #     msg_type = msg.get_type()
    #     if msg_type in important_msgs and counts[msg_type] < max_samples:
    #         entry = msg.to_dict()
    #         filtered = {
    #             k: entry[k]
    #             for k in important_msgs[msg_type]
    #             if k in entry
    #         }
    #         data[msg_type].append(filtered)
    #         counts[msg_type] += 1

    # return {
    #     "messages": dict(data),
    #     "summary": {k: len(v) for k, v in data.items()}
    # }

    mav = mavutil.mavlink_connection(file_path)
    data = defaultdict(list)
    counts = defaultdict(int)

    while True:
        msg = mav.recv_match(blocking=False)
        if msg is None:
            break

        msg_type = msg.get_type()
        if msg_type == 'BAD_DATA':
            continue  # Skip unparseable or corrupted data

        if counts[msg_type] < max_samples:
            try:
                entry = msg.to_dict()
                data[msg_type].append(entry)
                counts[msg_type] += 1
            except Exception as e:
                # Gracefully skip broken messages
                continue

    return {
        "messages": dict(data),
        "summary": {k: len(v) for k, v in data.items()}
    }