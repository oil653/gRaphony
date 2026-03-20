from sys import stderr

from crossfiledialog import open_file
from just_playback import Playback
from metaspector import MediaInspector
from textual.app import App, ComposeResult
from textual.containers import (
    HorizontalGroup,
    VerticalGroup,
)
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import Button, Digits, Footer, Header, Label
from textual_image.widget import Image
from tinytag import TinyTag


class TimeRemaining(Digits):
    """Digits that update when called"""

    media_length = reactive(0.0)
    media_position = reactive(0.0)

    def watch_media_length(self, length: float) -> None:
        len_minutes, len_seconds = divmod(length, 60)
        len_hours, len_minutes = divmod(len_minutes, 60)

        pos_minutes, pos_seconds = divmod(self.media_position, 60)
        pos_hours, pos_minutes = divmod(pos_minutes, 60)
        self.update(
            f"{pos_hours:02,.0f}:{pos_minutes:02.0f}:{pos_seconds:05.2f} / {len_hours:02,.0f}:{len_minutes:02.0f}:{len_seconds:05.2f}"
        )

    def watch_media_position(self, pos: float) -> None:
        len_minutes, len_seconds = divmod(self.media_length, 60)
        len_hours, len_minutes = divmod(len_minutes, 60)

        pos_minutes, pos_seconds = divmod(pos, 60)
        pos_hours, pos_minutes = divmod(pos_minutes, 60)
        self.update(
            f"{pos_hours:02,.0f}:{pos_minutes:02.0f}:{pos_seconds:05.2f} / {len_hours:02,.0f}:{len_minutes:02.0f}:{len_seconds:05.2f}"
        )


class MediaControls(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield Button("|<", id="previous")
        yield Button("|>", id="play", variant="primary")
        yield Button(">|", id="next")


class Metadata:
    title: str
    album: str
    artist: str
    filename: str
    album_art_path: str

    def __init__(
        self,
        title: str | None = "??",
        album: str | None = "??",
        artist: str | None = "??",
        filename: str | None = "??",
        album_art_path: str | None = "./assets/question_mark.png",
    ) -> None:
        if title is None:
            title = "??"

        if album is None:
            album = "??"

        if artist is None:
            artist = "??"

        if filename is None:
            filename = "??"

        if album_art_path is None:
            album_art_path = "./assets/question_mark.png"

        self.title = title
        self.album = album
        self.artist = artist
        self.filename = filename
        self.album_art_path = album_art_path


class MainApp(App[None]):
    CSS_PATH = "main.tcss"

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("o", "open_file", "Open a media file"),
        ("space", "play", "Toggle playback"),
        ("left", "back", "Previous"),
        ("right", "next", "Next"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.player = Playback()

    # Something that plays media
    player: Playback
    media_loaded: bool = False
    meta = reactive(Metadata, init=True)

    def compose(self) -> ComposeResult:
        yield Header(id="header")

        with VerticalGroup(id="top_bar"):
            yield MediaControls(id="media_controls")
            yield TimeRemaining(id="time")

            # Labels
            with VerticalGroup(id="media_label_container"):
                yield Label(f"File: {self.meta.filename}", id="current_filename")
                yield Label(f"Playing: {self.meta.title}", id="current_title")
                yield Label(f"Album: {self.meta.album}", id="current_album")
                yield Label(f"Artist: {self.meta.artist}", id="current_artist")

            yield Image(image="assets/question_mark.png", id="media_image")

        yield Footer()

    def watch_meta(self, _old: Metadata, new: Metadata) -> None:
        try:
            self.query_one("#current_filename", Label).update(f"File: {new.filename}")
            self.query_one("#current_title", Label).update(f"Playing: {new.title}")
            self.query_one("#current_album", Label).update(f"Album: {new.album}")
            self.query_one("#current_artist", Label).update(f"Artist: {new.artist}")

            self.query_one("#media_image", Image).image = new.album_art_path
        except NoMatches:
            pass

    def on_mount(self) -> None:
        self.title = "gRaphony"
        self.sub_title = "Music player"

        # Tick every 1 sec
        self.timer = self.set_interval(1 / 60, self.tick, pause=True)
        self.timer.pause()  # The player will not play anything by default

    def tick(self) -> None:
        widget = self.query_one(TimeRemaining)
        widget.media_position = self.player.curr_pos

    def action_toggle_dark(self) -> None:
        """Toggles between dark and light mode"""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        idb = event.button.id

        if idb == "play":
            self.toggle_play()

    def action_open_file(self) -> None:
        path = open_file("Chose a file to add to the queue", filter="*.mp3")
        try:
            self.player.load_file(path)
            widget = self.query_one(TimeRemaining)
            widget.media_length = self.player.duration

            inspector = MediaInspector(path)
            cover_art_bytes = inspector.get_cover_art()
            cover_path: str | None = None
            if cover_art_bytes:
                cover_path = "./assets/cover.png"
                with open("./assets/cover.png", "wb") as f:
                    f.write(cover_art_bytes)

            meta = TinyTag.get(path)
            self.meta = Metadata(
                title=meta.title,
                artist=meta.artist,
                album=meta.album,
                filename=meta.filename,
                album_art_path=cover_path,
            )
            self.media_loaded = True
        except Exception as e:
            print(f'Failed to open file at path "{path}": {e}', file=stderr)

    def action_play(self) -> None:
        self.toggle_play()

    def action_next(self) -> None:
        exit("To be implemented")

    def action_back(self) -> None:
        exit("To be implemented")

    def toggle_play(self) -> None:
        if not self.media_loaded:
            pass
        elif self.player.playing:
            self.pause()
        elif not self.player.playing:
            self.play()

    def play(self) -> None:
        self.timer.resume()

        if self.player.active:
            self.player.resume()
        else:
            self.player.play()

        self.query_one("#play", Button).label = "||"

    def pause(self) -> None:
        self.timer.pause()
        self.player.pause()

        self.query_one("#play", Button).label = "|>"


if __name__ == "__main__":
    app = MainApp()
    app.run()
