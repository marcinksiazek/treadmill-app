from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, HorizontalGroup, VerticalScroll, HorizontalScroll, Container
from textual.widgets import Button, Footer, Log, RadioSet, RadioButton
from textual.widgets import Digits, Header, Label
from textual.reactive import reactive
from bleak import BleakScanner, BleakClient, BLEDevice
import asyncio
from textual import work
from textual.worker import Worker
from bluetooth_device_picker import BluetoothDevicePicker

HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HEART_RATE_MEASUREMENT_CHARACTERISTIC_UUID = "00002a37-0000-1000-8000-00805f9b34fb"


class HeartRateTile(HorizontalGroup):
    """A HR tile widget."""

    hr: reactive[int] = reactive(0)

    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""
        yield Digits("123")
        yield Label("bpm")

    def watch_hr(self, hr: int) -> None:
        """Called when the hr attribute changes."""
        self.query_one(Digits).update(f"{hr}" if hr > 0 else "---")


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
    def connect_hr_pressed(self, event: Button.Pressed) -> None:
        self.append_log("Discovering HR devices...")
        self.push_screen(BluetoothDevicePicker(HEART_RATE_SERVICE_UUID), self.hr_device_selected)

    @on(Button.Pressed, "#disconnect-hr")
    def disconnect_hr_pressed(self, event: Button.Pressed) -> None:
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
            self.hr = int(data[1])

        async with BleakClient(device) as client:
            await client.start_notify("00002a37-0000-1000-8000-00805f9b34fb", heart_rate_handler)
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
