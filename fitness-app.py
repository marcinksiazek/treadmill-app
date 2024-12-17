from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, HorizontalGroup, VerticalScroll
from textual.widgets import Button, Footer, Log
from textual.widgets import Digits, Header, Label
from textual.reactive import reactive
from bleak import BleakScanner, BleakClient
import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor

current_hr = 5

HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HEART_RATE_MEASUREMENT_CHARACTERISTIC_UUID = "00002a37-0000-1000-8000-00805f9b34fb"


def discover_devices(app: "FitnessApp") -> None:
    found_device = None
    global current_hr
    current_hr = 22

    async def detection_callback(device, advertisement_data):
        nonlocal found_device
        global current_hr
        found_device = device
        current_hr = 666

    app.append_log("Discovering devices...")
    scanner = BleakScanner(detection_callback)
    app.append_log("Acanner initiated...")

    time.sleep(10)


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


class UpdateThread(threading.Thread):
    def __init__(self, app: "FitnessApp") -> None:
        self._app = app
        self._canceled = threading.Event()
        super().__init__()

    def run(self) -> None:
        self._app.append_log("Starting update thread...")
        discover_devices(self._app)
        self._app.append_log("After...")
        while True:
            if self._canceled.is_set():
                return

            # Sleep for 1 second
            asyncio.sleep(100)

    def cancel(self) -> None:
        self._canceled.set()


class FitnessApp(App):

    hr: reactive[int] = reactive(0)

    def __init__(self):
        super().__init__()
        self._update_thread = UpdateThread(self)

    CSS_PATH = "fitness-app.tcss"

    BINDINGS = [
        ("h", "connect_hr('red')", "Connect HR")
    ]

    def compose(self) -> ComposeResult:
        yield Header("Fitness App")
        yield Footer()
        yield VerticalScroll(HeartRateTile().data_bind(FitnessApp.hr),
                             Button("Connect HR", name="connect_hr", variant="primary"))
        yield Log()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        global current_hr
        self.query_one(Log).write_line("Button pressed!")
        current_hr += 1

    def append_log(self, message: str) -> None:
        self.query_one(Log).write_line(message)

    def update_hr(self) -> None:
        self.hr = current_hr

    def on_mount(self) -> None:
        self.update_hr()
        self.set_interval(1, self.update_hr)
        self.query_one(Log).write_line("Welcome to the Fitness App!")
        self._update_thread.start()

    def on_unmount(self) -> None:
        self._update_thread.cancel()
        if self._update_thread.is_alive():
            self._update_thread.join()

    def action_connect_hr(self) -> None:
        """ Connect to HR Monitor """
        print("Connecting to HR Monitor")


if __name__ == "__main__":
    app = FitnessApp()
    app.run()