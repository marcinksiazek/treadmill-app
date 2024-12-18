import asyncio
from bleak import BleakScanner
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Container
from textual.screen import ModalScreen
from textual.widgets import RadioSet, Label, Button, RadioButton


class BluetoothDevicePicker(ModalScreen):
    """A modal screen to pick a Bluetooth device."""
    def __init__(self, uuid_filter: str = None):
        super().__init__()
        self.uuid_filter = uuid_filter

    uuid_filter: str
    selected_device_index: int = None
    scanner: BleakScanner = None
    discovered_devices = []

    def compose(self) -> ComposeResult:
        with Container():
            yield Label("Select a Bluetooth Device")
            yield RadioSet()
            with Horizontal():
                yield Button.success("Yes", id="yes")
                yield Button.error("No", id="no")

    async def on_mount(self) -> None:

        def callback(device, advertising_data):
            if device.address not in [d.address for d in self.discovered_devices]:
                self.discovered_devices.append(device)
                radio_button = RadioButton(device.name)
                self.query_one(RadioSet).mount(radio_button)
                if len(self.discovered_devices) == 1:
                    radio_button.value = True
            pass

        self.scanner = BleakScanner(callback, [self.uuid_filter])
        await self.scanner.start()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        self.selected_device_index = event.radio_set.pressed_index

    @on(Button.Pressed)
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        await self.scanner.stop()
        if event.button.id == "yes" and self.selected_device_index is not None:
            self.dismiss(self.discovered_devices[self.selected_device_index])
        else:
            self.dismiss()