from sys import stderr

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Digits, Button
from textual.containers import HorizontalGroup, VerticalGroup, VerticalScroll, HorizontalScroll
from textual.reactive import reactive

from textual_image.widget import Image

from just_playback import Playback
from crossfiledialog import open_file, open_multiple

class CustomDigits(Digits):
    """ Digits that update when called """

    media_length = reactive(0.0)
    media_position = reactive(0.0)
    
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

class MainApp(App[None]):
    CSS_PATH = "main.tcss"
    
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("o", "open_file", "Open a media file")
    ]
    
    # Something that plays media
    player: Playback
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with HorizontalGroup(id="playbar"):
            yield Button("|<", id="previous")
            yield Button("|>", id="play", variant="primary")
            yield Button(">|", id="next")
            
            yield Digits(f"{self.media_position} / {self.media_length}")
            
        
        
        yield Footer()
    
    
    def __init__(self) -> None:
        self.player = Playback()
        super().__init__()

    
    def on_mount(self) -> None: 
        """ Sets the timer tickrate to 1 tick / sec """
        self.timer = self.set_interval(1 / 60, self.tick, pause=True)
        self.timer.pause() # The player will not play anything by default
        
    def tick(self) -> None:
        self.media_position = self.player.curr_pos
        
        
    def action_toggle_dark(self) -> None:
        """ Toggles between dark and light mode """
        self.theme = ("textual-dark" if self.theme == "textual-light" else "textual-light")
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """ Handles button events """
        idb: str = event.button.id
        
        if idb == "play" and self.player.playing:
            self.pause()
        elif idb == "play" and not self.player.playing:
            self.play()
         
    def action_open_file(self) -> None:
        path = open_file("Chose a file to add to the queue", filter="*.mp3")
        try:
            self.player.load_file(path)
            self.media_length = self.player.duration
            self.media_position = self.player.curr_pos
        except Exception as e:
            print(f"Failed to open file at path \"{path}\": {e}", file=stderr)
        
    def play(self) -> None:
        self.timer.resume()
        
        if self.player.active:
            self.player.resume()
        else:
            self.player.play()
        
        btn = self.query_one("#play")
        btn.label = "||"
        
    def pause(self) -> None: 
        self.timer.pause()
        self.player.pause()
        
        btn = self.query_one("#play")
        btn.label = "|>"
    
        
    

if __name__ == "__main__": 
    app = MainApp()
    app.run()