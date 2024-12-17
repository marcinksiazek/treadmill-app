import asyncio
import string
from bleak import BleakScanner, BleakClient
from rich.console import Console
from rich.tree import Tree
from rich import print
from rich.panel import Panel
from rich.live import Live


BATTERY_SERVICE_UUID = "0000180f-0000-1000-8000-00805f9b34fb"
BATTERY_LEVEL_CHARACTERISTIC_UUID = "00002a19-0000-1000-8000-00805f9b34fb"
DEVICE_INFORMATION_SERVICE_UUID = "0000180a-0000-1000-8000-00805f9b34fb"
HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HEART_RATE_MEASUREMENT_CHARACTERISTIC_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_UUIDS = {
    "Manufacturer Name": "00002a29-0000-1000-8000-00805f9b34fb",
    "Model Number": "00002a24-0000-1000-8000-00805f9b34fb",
    "Serial Number": "00002a25-0000-1000-8000-00805f9b34fb",
    "Hardware Revision": "00002a27-0000-1000-8000-00805f9b34fb",
    "Firmware Revision": "00002a26-0000-1000-8000-00805f9b34fb",
    "Software Revision": "00002a28-0000-1000-8000-00805f9b34fb",
    "System ID": "00002a23-0000-1000-8000-00805f9b34fb"
}

console = Console()


async def discover_devices():
    found_device = None
    discovered_devices = []

    async def detection_callback(device, advertisement_data):
        nonlocal found_device
        nonlocal discovered_devices

        if device.address not in [d.address for d in discovered_devices]:
            console.print(f"[{len(discovered_devices)}] [dim]Device:[/] [bold magenta]{device.name}[/] [dim]RSSI:[/] [bold green]{advertisement_data.rssi}[/] [dim]Address:[/] {device.address}")
            discovered_devices.append(device)

        found_device = device
        await scanner.stop()

    scanner = BleakScanner(detection_callback, [HEART_RATE_SERVICE_UUID])

    with console.status("[bold green]Scanning for HR Devices...") as status:
        await scanner.start()
        while not found_device:
            await asyncio.sleep(1)

    async with BleakClient(found_device) as client:

        services = client.services
        services_tree = Tree(f"Sensor: {found_device.name}")
        for service in services:
            if service.uuid in [BATTERY_SERVICE_UUID, DEVICE_INFORMATION_SERVICE_UUID, HEART_RATE_SERVICE_UUID]:
                child_tree = services_tree.add(f"Service: {service.description}")
                for characteristic in service.characteristics:
                    characteristic_node = child_tree.add(f"Characteristic: {characteristic.uuid}")
                    if service.uuid == BATTERY_SERVICE_UUID and characteristic.uuid == BATTERY_LEVEL_CHARACTERISTIC_UUID:
                        battery_level = await client.read_gatt_char(characteristic)
                        characteristic_node.add(f"  Battery Level: {int(battery_level[0])}%")
                    elif service.uuid == DEVICE_INFORMATION_SERVICE_UUID and characteristic.uuid in CHARACTERISTIC_UUIDS.values():
                        value = await client.read_gatt_char(characteristic)
                        for name, uuid in CHARACTERISTIC_UUIDS.items():
                            if characteristic.uuid == uuid and uuid != CHARACTERISTIC_UUIDS["System ID"]:
                                printable_value = ''.join(filter(lambda x: x in string.printable, value.decode('utf-8')))
                                characteristic_node.add(f"  {name}: {printable_value}")
                            elif characteristic.uuid == uuid and uuid == CHARACTERISTIC_UUIDS["System ID"]:
                                characteristic_node.add(f"  {name}: {'-'.join(value.hex()[i:i+2] for i in range(0, len(value.hex()), 2))}")
        print(services_tree)

        panel = Panel(f"\n  [red]---[/] bpm", title=f"{found_device.name}", width=15, height=5)

        def heart_rate_handler(sender, data):
            heart_rate = int(data[1])
            panel.renderable = f"\n  [red]{heart_rate}[/] bpm"

        with Live(panel, refresh_per_second=4):
            await client.start_notify(HEART_RATE_MEASUREMENT_CHARACTERISTIC_UUID, heart_rate_handler)
            await asyncio.sleep(30)  # Keep receiving notifications for 30 seconds
        try:
            await client.stop_notify(characteristic)
        except Exception as e:
            print(f"Error stopping notifications: {e}")


if __name__ == "__main__":
    console.log("HR Monitor Started")
    asyncio.run(discover_devices())