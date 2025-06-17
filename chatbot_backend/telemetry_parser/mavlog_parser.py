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
    mav = mavutil.mavlink_connection(file_path)
    data = defaultdict(list)
    counts = defaultdict(int)

    while True:
        msg = mav.recv_match(blocking=False)
        if msg is None:
            break

        msg_type = msg.get_type()
        if msg_type == 'BAD_DATA':
            continue

        if counts[msg_type] < max_samples:
            try:
                entry = msg.to_dict()
                data[msg_type].append(entry)
                counts[msg_type] += 1
            except Exception as e:
                continue
    # print(data)
    return {
        "messages": dict(data),
        "summary": {k: len(v) for k, v in data.items()}
    }