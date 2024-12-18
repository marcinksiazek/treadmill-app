SERVICE_UUID = "1814"
FEATURE_CHARACTERISTIC_UUID = "2a54"
MEASUREMENT_CHARACTERISTIC_UUID = "2a53"


def parse_rsc_measurement(data):
    """
    Parse the RSC (Running Speed and Cadence) measurement data.

    Args:
        data (bytes): Byte array containing the RSC measurement data.

    Returns:
        dict: Parsed RSC measurement fields.
    """
    # Ensure data is at least 4 bytes (minimum RSC packet length)
    if len(data) < 4:
        raise ValueError("Invalid RSC Measurement data length.")

    # Parse the Flags byte
    flags = data[0]
    stride_length_present = (flags & 0x01) != 0
    total_distance_present = (flags & 0x02) != 0
    running_status = (flags & 0x04) != 0

    # Parse mandatory fields
    speed_m_per_s = int.from_bytes(data[1:3], byteorder='little') / 256  # Convert to m/s
    cadence_steps_per_min = data[3]  # Steps per minute

    # Calculate derived fields
    speed_kmh = speed_m_per_s * 3.6  # Convert m/s to km/h
    pace_min_per_km = 1 / (speed_m_per_s * 3.6 / 60) if speed_m_per_s > 0 else 50  # Convert to min/km

    # Initialize result dictionary
    result = {
        "speed_m_per_s": speed_m_per_s,
        "speed_kmh": speed_kmh,
        "pace": pace_min_per_km,
        "cadence": cadence_steps_per_min,
        "running_status": "running" if running_status else "walking",
    }

    # Offset for optional fields
    offset = 4

    # Parse optional stride length
    if stride_length_present:
        if len(data) >= offset + 2:
            stride_length_m = int.from_bytes(data[offset:offset + 2], byteorder='little') * 0.01  # Convert to meters
            result["stride_length_m"] = stride_length_m
            offset += 2
        else:
            raise ValueError("Stride length flag is set, but data is incomplete.")

    # Parse optional total distance
    if total_distance_present:
        if len(data) >= offset + 4:
            total_distance_m = int.from_bytes(data[offset:offset + 4], byteorder='little') * 0.01  # Convert to meters
            total_distance_km = total_distance_m / 1000  # Convert to kilometers
            result["total_distance_m"] = total_distance_m
            result["total_distance_km"] = total_distance_km
        else:
            raise ValueError("Total distance flag is set, but data is incomplete.")

    return result
