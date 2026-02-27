from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Digits, Button
from textual.containers import HorizontalGroup, VerticalScroll

class TimeDisplay(Digits):
    """Widgets to display elpased time."""

class StopWatch(HorizontalGroup):
    """ A stopwatch widget """
    
    def on_button_pressed(self, event: Button.Pressed) -> None: 
        if event.button.id == "start":
            self.add_class("started")
        elif event.button.id == "stop": 
            self.remove_class("started")

    def compose(self): 
        yield Button("Start", id="start", variant="success")
        yield Button("Stop", id="stop", variant="error")
        yield Button("Reset", id="reset")
        yield TimeDisplay("00:00:00:00")

    

class StartwatchApp(App): 
    CSS_PATH = "main.tcss"

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("s", "explode", "DETONATE")
    ]

    def compose(self) -> ComposeResult:
        # Create a child widget for the app
        yield Header()
        yield Footer()
        yield VerticalScroll(StopWatch(), StopWatch(), StopWatch())

    def action_toggle_dark(self) -> None:
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

if __name__ == "__main__": 
    app = StartwatchApp()
    app.run()