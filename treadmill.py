import asyncio
from bleak import BleakScanner, BleakClient
from bleak.uuids import normalize_uuid_str
from rich.console import Console
from rich.tree import Tree
from rich import print
from rich.panel import Panel
from rich.live import Live
import bt_running_speed_cadence
import bt_user_data

FITNESS_MACHINE_SERVICE_UUID = "1826"
FITNESS_MACHINE_FEATURE_CHARACTERISTIC_UUID = "2acc"
FITNESS_MACHINE_TREADMILL_DATA_CHARACTERISTIC_UUID = "2acd"
FITNESS_MACHINE_CONTROL_POINT_CHARACTERISTIC_UUID = "2ad9"
FITNESS_MACHINE_STATUS_CHARACTERISTIC_UUID = "2ada"
FITNESS_MACHINE_TRAINING_STATUS_CHARACTERISTIC_UUID = "2ad3"
FITNESS_MACHINE_SUPPORTED_SPEED_RANGE_CHARACTERISTIC_UUID = "2ad4"
FITNESS_MACHINE_SUPPORTED_INCLINATION_RANGE_CHARACTERISTIC_UUID = "2ad5"


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

    with console.status("[bold green]Scanning for Treadmill...") as status:
        await scanner.start()
        while not found_device:
            await asyncio.sleep(1)

    async with BleakClient(found_device) as client:

        services = client.services
        services_tree = Tree(f"Sensor: {found_device.name}")
        for service in services:
            if service.uuid == bt_user_data.service_uuid():
                child_tree = services_tree.add(f"Service: {service.description}")
                for characteristic in service.characteristics:
                    value = await client.read_gatt_char(characteristic.uuid)
                    display_value = ""
                    if characteristic.uuid == bt_user_data.weight_uuid():
                        display_value = f"{bt_user_data.parse_weight(value)} kg"
                    elif characteristic.uuid == bt_user_data.age_uuid():
                        display_value = bt_user_data.parse_age_data(value)
                    elif characteristic.uuid == bt_user_data.gender_uuid():
                        display_value = bt_user_data.parse_gender(value)
                    child_tree.add(f"{characteristic.description}: {display_value}")

        print(services_tree)

        panel = Panel(f"\n  [cyan]---", title=f"Speed & Cadence", width=30, height=10)

        def running_speed_and_cadence_handler(sender, data):
            result = bt_running_speed_cadence.parse_rsc_measurement(data)

            text = f"\n  Speed:    [cyan]{result['speed_kmh']:.2f}[/] km/h" + \
                   f"\n  Pace:     [cyan]{result['pace']:.2f}[/] min/km" + \
                   f"\n  Distance: [cyan]{result.get('total_distance_km', 0):.2f}[/] km"

            panel.renderable = text

        with Live(panel, refresh_per_second=4):
            await client.start_notify(bt_running_speed_cadence.MEASUREMENT_CHARACTERISTIC_UUID,
                                      running_speed_and_cadence_handler)
            await asyncio.sleep(300)  # Keep receiving notifications for 30 seconds


if __name__ == "__main__":
    console.log("Treadmill Controller Started")
    asyncio.run(discover_devices())
