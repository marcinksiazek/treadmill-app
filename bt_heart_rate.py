from bleak.uuids import normalize_uuid_str

SERVICE_UUID = "180d"
MEASUREMENT_CHARACTERISTIC_UUID = "2a37"


def service_uuid():
    return normalize_uuid_str(SERVICE_UUID)


def measurement_uuid():
    return normalize_uuid_str(MEASUREMENT_CHARACTERISTIC_UUID)


def parse_hr_data(data):
    return int(data[1])