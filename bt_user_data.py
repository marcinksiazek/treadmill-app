from bleak.uuids import normalize_uuid_str

SERVICE_UUID = "181c"
AGE_CHARACTERISTIC_UUID = "2a80"
GENDER_CHARACTERISTIC_UUID = "2a8c"
WEIGHT_CHARACTERISTIC_UUID = "2a98"


def service_uuid():
    return normalize_uuid_str(SERVICE_UUID)


def age_uuid():
    return normalize_uuid_str(AGE_CHARACTERISTIC_UUID)


def gender_uuid():
    return normalize_uuid_str(GENDER_CHARACTERISTIC_UUID)


def weight_uuid():
    return normalize_uuid_str(WEIGHT_CHARACTERISTIC_UUID)


def parse_age_data(data):
    return int.from_bytes(data, byteorder='little')


def parse_gender(data):
    return "Male" if data == b'\x00' else "Female"


def parse_weight(data):
    return int.from_bytes(data, byteorder='little') / 2 / 100
