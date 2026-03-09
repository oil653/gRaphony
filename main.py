from sys import stderr

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Digits, Button, Label
from textual.containers import HorizontalGroup, VerticalGroup, VerticalScroll, HorizontalScroll, Container
from textual.reactive import reactive
from textual.css.query import NoMatches 

from textual_image.widget import Image

from tinytag import TinyTag

from just_playback import Playback
from crossfiledialog import open_file, open_multiple

class TimeRemaining(Digits):
    """ Digits that update when called """

    media_length = reactive(0.0)
    media_position = reactive(0.0)
    
    def watch_media_length(self, length: float) -> None:
        len_minutes, len_seconds = divmod(length, 60)
        len_hours, len_minutes = divmod(len_minutes, 60)
        
        pos_minutes, pos_seconds = divmod(self.media_position, 60)
        pos_hours, pos_minutes = divmod(pos_minutes, 60)
        self.update(f"{pos_hours:02,.0f}:{pos_minutes:02.0f}:{pos_seconds:05.2f} / {len_hours:02,.0f}:{len_minutes:02.0f}:{len_seconds:05.2f}")
        
        
    def watch_media_position(self, pos: float) -> None:
        len_minutes, len_seconds = divmod(self.media_length, 60)
        len_hours, len_minutes = divmod(len_minutes, 60)
        
        pos_minutes, pos_seconds = divmod(pos, 60)
        pos_hours, pos_minutes = divmod(pos_minutes, 60)
        self.update(f"{pos_hours:02,.0f}:{pos_minutes:02.0f}:{pos_seconds:05.2f} / {len_hours:02,.0f}:{len_minutes:02.0f}:{len_seconds:05.2f}")

class MediaControls(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield Button("|<", id="previous")
        yield Button("|>", id="play", variant="primary")
        yield Button(">|", id="next")

class MainApp(App[None]):    
    CSS_PATH = "main.tcss"
    
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("o", "open_file", "Open a media file")
    ]

        
    def __init__(self) -> None:
        super().__init__()
        self.player = Playback()
    
    # Something that plays media
    player: Playback
    current_title = reactive("NOTHING", init=True)
    
    def compose(self) -> ComposeResult:
        yield Header(id="header")

        with VerticalGroup(id="top_bar"):
            # Top thingy with basic controls
            with HorizontalGroup(id="playbar"):
                yield MediaControls(id="media_controls")
                yield TimeRemaining(id="time_remaining")

            # The name of the media
            with HorizontalGroup(id="media_label_container"):
                yield Label(f"Playing: {self.current_title}", id="current_title")

        
        yield Footer()


    def watch_current_title(self, old: str, new: str) -> None:
        try: 
            self.query_one("#current_title").label = f"Playing: {new}"
        except NoMatches:
            pass
    
    def on_mount(self) -> None: 
        self.title = "gRaphony"
        self.sub_title = "Music player"

        # Tick every 1 sec
        self.timer = self.set_interval(1 / 60, self.tick, pause=True)
        self.timer.pause() # The player will not play anything by default
        
    def tick(self) -> None:
        widget = self.query_one(TimeRemaining)
        widget.media_position = self.player.curr_pos
        
        
    def action_toggle_dark(self) -> None:
        """ Toggles between dark and light mode """
        self.theme = ("textual-dark" if self.theme == "textual-light" else "textual-light")
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        idb = event.button.id
        
        if idb == "play" and self.player.playing:
            self.pause()
        elif idb == "play" and not self.player.playing:
            self.play()
         
    def action_open_file(self) -> None:
        path = open_file("Chose a file to add to the queue", filter="*.mp3")
        try:
            self.player.load_file(path)
            widget = self.query_one(TimeRemaining)
            widget.media_length = self.player.duration

            meta =  TinyTag.get(path)
            self.current_title = meta.title
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