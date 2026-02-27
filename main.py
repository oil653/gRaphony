from time import monotonic

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Digits, Button
from textual.containers import HorizontalGroup, VerticalScroll
from textual.reactive import reactive

class TimeDisplay(Digits):
    """Widgets to display elpased time."""
    
    start_time = reactive(monotonic)
    time = reactive(0.0)
    total = reactive(0.0)
    
    def on_mount(self) -> None: 
        """ Event handler called when the thing displays """
        self.update_timer = self.set_interval(1 / 60, self.update_time, pause=True)
        
    def update_time(self) -> None: 
        self.time = self.total + (monotonic() - self.start_time)
        
    def watch_time(self, time: float) -> None:
        """Called when the time attribute changes."""
        minutes, seconds = divmod(time, 60)
        hours, minutes = divmod(minutes, 60)
        self.update(f"{hours:02,.0f}:{minutes:02.0f}:{seconds:05.2f}")
        
    def start(self) -> None:
        self.start_time = monotonic()
        self.update_timer.resume()
        
    def pause(self) -> None:
        self.update_timer.pause()
        self.total += monotonic() - self.start_time
        self.time = self.total
        
    def reset(self) -> None:
        self.pause()
        self.time = 0.0
        self.total = 0.0
        
        
        

class StopWatch(HorizontalGroup):
    """ A stopwatch widget """
    
    def on_button_pressed(self, event: Button.Pressed) -> None: 
        button_id = event.button.id
        time_display = self.query_one(TimeDisplay)
        
        if button_id == "start":
            time_display.start()
            self.add_class("started")
        elif button_id == "stop": 
            time_display.pause()
            self.remove_class("started")
        elif button_id == "reset":
            time_display.reset()

    def compose(self): 
        yield Button("Start", id="start", variant="success")
        yield Button("Stop", id="stop", variant="error")
        yield Button("Reset", id="reset")
        yield TimeDisplay()


    

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