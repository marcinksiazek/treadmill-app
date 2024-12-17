import asyncio
from bleak import BleakScanner, BleakClient
import string

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


async def discover_devices():
    found_device = None

    async def detection_callback(device, advertisement_data):
        nonlocal found_device
        if device.name and device.name.startswith("Polar H10"):
            print("Found Polar H10")
            print(f"Device: {device.name}, Address: {device.address}")
            print(f"Details: {device.details}")
            print(f"Advertisement Data: {advertisement_data}")
            found_device = device
            await scanner.stop()

    scanner = BleakScanner(detection_callback)
    await scanner.start()
    while not found_device:
        await asyncio.sleep(1)

    async with BleakClient(found_device) as client:
        services = client.services
        for service in services:
            if service.uuid in [BATTERY_SERVICE_UUID, DEVICE_INFORMATION_SERVICE_UUID, HEART_RATE_SERVICE_UUID]:
                print(f"Service: {service.uuid}")
                print(f"Description: {service.description}")
                for characteristic in service.characteristics:
                    print(f"  Characteristic: {characteristic.uuid}")
                    if service.uuid == BATTERY_SERVICE_UUID and characteristic.uuid == BATTERY_LEVEL_CHARACTERISTIC_UUID:
                        battery_level = await client.read_gatt_char(characteristic)
                        print(f"  Battery Level: {int(battery_level[0])}%")
                    elif service.uuid == DEVICE_INFORMATION_SERVICE_UUID and characteristic.uuid in CHARACTERISTIC_UUIDS.values():
                        value = await client.read_gatt_char(characteristic)
                        for name, uuid in CHARACTERISTIC_UUIDS.items():
                            if characteristic.uuid == uuid and uuid != CHARACTERISTIC_UUIDS["System ID"]:
                                printable_value = ''.join(filter(lambda x: x in string.printable, value.decode('utf-8')))
                                print(f"  {name}: {printable_value}")
                            elif characteristic.uuid == uuid and uuid == CHARACTERISTIC_UUIDS["System ID"]:
                                print(f"  {name}: {'-'.join(value.hex()[i:i+2] for i in range(0, len(value.hex()), 2))}")

        def heart_rate_handler(sender, data):
            heart_rate = int(data[1])
            print(f"Heart Rate: {heart_rate} bpm")
        await client.start_notify(HEART_RATE_MEASUREMENT_CHARACTERISTIC_UUID, heart_rate_handler)
        await asyncio.sleep(30)  # Keep receiving notifications for 30 seconds
        try:
            await client.stop_notify(characteristic)
        except Exception as e:
            print(f"Error stopping notifications: {e}")


if __name__ == "__main__":
    print("Scanning for devices...")
    asyncio.run(discover_devices())