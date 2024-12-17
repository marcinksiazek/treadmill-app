import asyncio
import string
from bleak import BleakScanner, BleakClient
from bleak.uuids import normalize_uuid_str
from rich.console import Console
from rich.tree import Tree
from rich import print
from rich.panel import Panel
from rich.live import Live

FITNESS_MACHINE_SERVICE_UUID = "1826"
FITNESS_MACHINE_FEATURE_CHARACTERISTIC_UUID = "2acc"
FITNESS_MACHINE_TREADMILL_DATA_CHARACTERISTIC_UUID = "2acd"
FITNESS_MACHINE_CONTROL_POINT_CHARACTERISTIC_UUID = "2ad9"
FITNESS_MACHINE_STATUS_CHARACTERISTIC_UUID = "2ada"
FITNESS_MACHINE_TRAINING_STATUS_CHARACTERISTIC_UUID = "2ad3"
FITNESS_MACHINE_SUPPORTED_SPEED_RANGE_CHARACTERISTIC_UUID = "2ad4"
FITNESS_MACHINE_SUPPORTED_INCLINATION_RANGE_CHARACTERISTIC_UUID = "2ad5"

USER_DATA_SERVICE_UUID = "181c"
USER_DATA_AGE_CHARACTERISTIC_UUID = "2a80"
USER_DATA_GENDER_CHARACTERISTIC_UUID = "2a8c"
USER_DATA_WEIGHT_CHARACTERISTIC_UUID = "2a98"

RUNNING_SPEED_AND_CADENCE_SERVICE_UUID = "1814"
RUNNING_SPEED_AND_CADENCE_FEATURE_CHARACTERISTIC_UUID = "2a54"
RUNNING_SPEED_AND_CADENCE_MEASUREMENT_CHARACTERISTIC_UUID = "2a53"

DEVICE_INFORMATION_SERVICE_UUID = "180a"
DEVICE_INFORMATION_CHARACTERISTIC_UUIDS = {
    "Manufacturer Name": "2a29",
    "Serial Number": "2a25",
    "Hardware Revision": "2a27",
    "Software Revision": "2a28",
}

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


console = Console()


async def discover_devices():
    found_device = None
    discovered_devices = []

    async def detection_callback(device, advertisement_data):
        nonlocal found_device
        nonlocal discovered_devices

        if device.address not in [d.address for d in discovered_devices]:
            console.print(
                f"[{len(discovered_devices)}] [dim]Device:[/] [bold magenta]{device.name}[/] [dim]RSSI:[/] [bold green]{advertisement_data.rssi}[/] [dim]Address:[/] {device.address}")
            discovered_devices.append(device)

        found_device = device
        await scanner.stop()

    scanner = BleakScanner(detection_callback, [normalize_uuid_str(FITNESS_MACHINE_SERVICE_UUID)])

    with console.status("[bold green]Scanning for HR Devices...") as status:
        await scanner.start()
        while not found_device:
            await asyncio.sleep(1)

    async with BleakClient(found_device) as client:

        services = client.services
        services_tree = Tree(f"Sensor: {found_device.name}")
        for service in services:
            if service.uuid == normalize_uuid_str(USER_DATA_SERVICE_UUID):
                child_tree = services_tree.add(f"Service: {service.description}")
                for characteristic in service.characteristics:
                    value = await client.read_gatt_char(characteristic.uuid)
                    display_value = ""
                    if characteristic.uuid == normalize_uuid_str(USER_DATA_WEIGHT_CHARACTERISTIC_UUID):
                        display_value = f"{int.from_bytes(value, byteorder='little') / 2 / 100} kg"
                    elif characteristic.uuid == normalize_uuid_str(USER_DATA_AGE_CHARACTERISTIC_UUID):
                        display_value = int.from_bytes(value, byteorder='little')
                    elif characteristic.uuid == normalize_uuid_str(USER_DATA_GENDER_CHARACTERISTIC_UUID):
                        display_value = "Male" if value == b'\x00' else "Female"
                    child_tree.add(f"{characteristic.description}: {display_value}")

        print(services_tree)

        panel = Panel(f"\n  [cyan]---", title=f"Speed & Cadence", width=30, height=10)

        def running_speed_and_cadence_handler(sender, data):
            result = parse_rsc_measurement(data)
            #print(result)

            text = f"\n  Speed:    [cyan]{result['speed_kmh']:.2f}[/] km/h" + \
                   f"\n  Pace:     [cyan]{result['pace']:.2f}[/] min/km" + \
                   f"\n  Distance: [cyan]{result.get('total_distance_km', 0):.2f}[/] km"

            panel.renderable = text

        with Live(panel, refresh_per_second=4):
            await client.start_notify(RUNNING_SPEED_AND_CADENCE_MEASUREMENT_CHARACTERISTIC_UUID, running_speed_and_cadence_handler)
            await asyncio.sleep(300)  # Keep receiving notifications for 30 seconds


if __name__ == "__main__":
    console.log("Treadmill Manager Started")
    asyncio.run(discover_devices())
