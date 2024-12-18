import asyncio
from bleak import BleakClient, BLEDevice
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import HorizontalScroll
from textual.reactive import reactive
from textual.widgets import Button, Header, Footer, Log
from textual.worker import Worker
import bt_heart_rate
from bluetooth_device_picker import BluetoothDevicePicker
from heart_rate_tile import HeartRateTile


class FitnessApp(App):
    hr_worker: Worker = None
    hr: reactive[int] = reactive(0)
    CSS_PATH = "fitness-app.tcss"
    BINDINGS = [
        ("h", "connect_hr('red')", "Connect HR")
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield HorizontalScroll(HeartRateTile().data_bind(FitnessApp.hr),
                               Button("Connect HR", id="connect-hr", variant="success"),
                               Button("Disconnect HR", id="disconnect-hr", variant="error"))
        yield Log()

    @on(Button.Pressed, "#connect-hr")
    def connect_hr_pressed(self) -> None:
        self.append_log("Discovering HR devices...")
        self.push_screen(BluetoothDevicePicker(bt_heart_rate.service_uuid()), self.hr_device_selected)

    @on(Button.Pressed, "#disconnect-hr")
    def disconnect_hr_pressed(self) -> None:
        self.append_log("Cancelling HR worker...")
        if self.hr_worker and self.hr_worker.is_running:
            self.hr_worker.cancel()
        self.hr = 0

    async def hr_device_selected(self, device: BLEDevice) -> None:
        if device is not None:
            self.append_log(f"Connecting to {device.name}...")
            self.hr_worker = self.connect_hr(device)
        else:
            self.append_log("No device selected.")

    def append_log(self, message: str) -> None:
        self.query_one(Log).write_line(message)

    def on_mount(self) -> None:
        self.append_log("Welcome to the Fitness App!")

    def on_unmount(self) -> None:
        pass

    @work(thread=False)
    async def connect_hr(self, device) -> None:
        self.append_log("Subscribing for HR notifications...")

        def heart_rate_handler(sender, data):
            self.hr = bt_heart_rate.parse_hr_data(data)

        async with BleakClient(device) as client:
            await client.start_notify(bt_heart_rate.measurement_uuid(), heart_rate_handler)
            while True:
                await asyncio.sleep(1)
                # TODO: Handle disconnection
        self.append_log("Worker exit...")

    async def action_connect_hr(self) -> None:
        """ Connect to HR Monitor """
        self.append_log("Connecting to HR Monitor")
        self.hr_worker = self.connect_hr()


if __name__ == "__main__":
    app = FitnessApp()
    app.run()
