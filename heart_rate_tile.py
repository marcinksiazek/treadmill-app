from textual.app import ComposeResult
from textual.containers import HorizontalGroup
from textual.reactive import reactive
from textual.widgets import Digits, Label


class HeartRateTile(HorizontalGroup):
    """A HR tile widget."""
    hr: reactive[int] = reactive(0)

    def compose(self) -> ComposeResult:
        yield Digits("---")
        yield Label("bpm")

    def watch_hr(self, hr: int) -> None:
        """Called when the hr attribute changes."""
        self.query_one(Digits).update(f"{hr}" if hr > 0 else "---")