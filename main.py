import hashlib
import os
from pathlib import Path
from sys import stderr

from crossfiledialog import open_file
from just_playback import Playback
from metaspector import MediaInspector
from textual.app import App, ComposeResult
from textual.containers import (
    Horizontal,
    HorizontalGroup,
    Vertical,
    VerticalGroup,
    VerticalScroll,
)
from textual.css.query import NoMatches
from textual.reactive import Reactive, reactive
from textual.widgets import Button, Digits, Footer, Header, Label
from textual_image.widget import Image
from tinytag import TinyTag

BASE_DIR: Path = Path(__file__).resolve().parent


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
    path: str | None
    duration_secons: float

    def is_some(self) -> bool:
        return self.path is not None

    def __init__(
        self,
        path: str | None = None,
        title: str | None = "??",
        album: str | None = "??",
        artist: str | None = "??",
        filename: str | None = "??",
        album_art_path: str | None = f"{BASE_DIR}/unknown.png",
        duration_seconds: float | None = 0,
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
            album_art_path = f"{BASE_DIR}/unknown.png"

        if duration_seconds is None:
            duration_seconds = 0

        self.title = title
        self.album = album
        self.artist = artist
        self.filename = filename
        self.album_art_path = album_art_path
        self.path = path
        self.duration_secons = duration_seconds


class MetaCard(HorizontalGroup):
    meta: Metadata

    def __init__(self, meta: Metadata) -> None:
        super().__init__()
        self.meta = meta

    def compose(self) -> ComposeResult:
        with HorizontalGroup(classes="meta_card"):
            with VerticalGroup():
                yield Label(f"File: {self.meta.filename}", id="current_filename")
                yield Label(f"Playing: {self.meta.title}", id="current_title")
                yield Label(f"Album: {self.meta.album}", id="current_album")
                yield Label(f"Artist: {self.meta.artist}", id="current_artist")

                len_minutes, len_seconds = divmod(self.meta.duration_secons, 60)
                len_hours, len_minutes = divmod(len_minutes, 60)
                yield Label(
                    f"Duration: {len_hours:02,.0f}:{len_minutes:02.0f}:{len_seconds:05.2f}",
                    id="duration",
                )

            yield Image(image=self.meta.album_art_path, classes="meta_card_image")


class MainApp(App[None]):
    CSS_PATH = "main.tcss"

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("o", "open_file", "Open a file"),
        ("c", "clear", "Clear queue"),
        ("space", "play", "Play/Pause"),
        ("left", "previous", "Previous"),
        ("right", "next", "Next"),
    ]

    def __init__(self) -> None:
        super().__init__()

        os.makedirs(self.cache_dir, exist_ok=True)

        # Build existing cache
        for file in self.cache_dir.iterdir():
            if file.is_file():
                self.img_cache[file.stem] = file

    cache_dir: Path = BASE_DIR / Path("cache")

    player: Playback = Playback()
    media_loaded: bool = False
    meta = reactive(Metadata, init=True)
    queue: Reactive[list[Metadata]] = reactive([])
    played: Reactive[list[Metadata]] = reactive([])

    # A cache of the thumbnail images.
    # "hash": "cache/{HASH}.png"
    img_cache: dict = {}

    # ===== UI =====
    def compose(self) -> ComposeResult:
        yield Header(id="header")

        # Top, currently playing bar
        with Vertical(id="top_bar"):
            yield MediaControls(id="media_controls")
            yield TimeRemaining(id="time")

            # Labels
            with VerticalGroup(id="media_label_container"):
                yield Label(f"File: {self.meta.filename}", id="current_filename")
                yield Label(f"Playing: {self.meta.title}", id="current_title")
                yield Label(f"Album: {self.meta.album}", id="current_album")
                yield Label(f"Artist: {self.meta.artist}", id="current_artist")

            yield Image(image=f"{str(BASE_DIR)}/unknown.png", id="media_image")

        # Bottom split between recently played and queue
        with Horizontal(id="bottom"):
            with Vertical(id="queue", classes="bottom_panel"):
                yield Label("Queue", id="queue_label", classes="bottom_top_label")
                yield VerticalScroll(id="queue_scroll")

            with Vertical(id="played", classes="bottom_panel"):
                yield Label(
                    "Recently played", id="palyed_label", classes="bottom_top_label"
                )
                yield VerticalScroll(id="played_scroll")

        yield Footer()

    def watch_queue(self) -> None:
        scroll = self.query_one("#queue_scroll", VerticalScroll)
        scroll.remove_children()

        if len(self.queue) != 0:
            for meta in self.queue:
                scroll.mount(MetaCard(meta))

    def watch_played(self) -> None:
        scroll = self.query_one("#played_scroll", VerticalScroll)
        scroll.remove_children()

        if len(self.played) != 0:
            for meta in self.played:
                scroll.mount(MetaCard(meta))

    def watch_meta(self, old: Metadata, new: Metadata) -> None:
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
        self.sub_title = "A music player"

        self.theme = "tokyo-night"

        # Tick every 1 sec
        self.timer = self.set_interval(1 / 60, self.tick, pause=True)
        self.timer.pause()  # The player will not play anything by default

    def tick(self) -> None:
        widget = self.query_one(TimeRemaining)
        widget.media_position = self.player.curr_pos

        if (
            self.player.duration > 0
            and self.player.curr_pos >= self.player.duration
            and len(self.queue) > 0
        ):
            self.next()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        idb = event.button.id

        if idb == "play":
            self.toggle_play()
        elif idb == "previous":
            self.previous()
        elif idb == "next":
            self.next()

    def action_open_file(self) -> None:
        path: str = open_file("Chose a file to add to the queue", filter="*.mp3")
        if len(path) == 0:
            return

        if len(self.queue) == 0 and not self.media_loaded:
            self.load_file(path)
        else:
            if len(path) > 0:
                self.queue_append(self.get_metadata(path))

    def queue_append(self, item: Metadata) -> None:
        self.queue.append(item)
        self.watch_queue()

    def played_append(self, item: Metadata) -> None:
        self.played.append(item)
        self.watch_played()

    def action_play(self) -> None:
        self.toggle_play()

    def action_next(self) -> None:
        self.next()

    def action_clear(self) -> None:
        self.clear()

    def action_previous(self) -> None:
        self.previous()

    def action_toggle_dark(self) -> None:
        self.theme = "tokyo-night" if self.theme == "textual-light" else "textual-light"

    # ===== Playback logic =====

    def load_file(self, path: str) -> None:
        self.media_loaded = False
        try:
            self.player.load_file(path)
            widget = self.query_one(TimeRemaining)
            widget.media_length = self.player.duration

            self.media_loaded = True
            self.meta = self.get_metadata(path)
        except Exception as e:
            print(f'Failed to open file at path "{path}": {e}', file=stderr)

    def get_metadata(self, path: str) -> Metadata:
        cover_path: str | None = None

        inspector = MediaInspector(path)
        cover_bytes = inspector.get_cover_art()
        if cover_bytes is not None:
            cover_hash = hashlib.sha256(cover_bytes).hexdigest()
            cover_lookup: Path | None = self.img_cache.get(cover_hash)

            if cover_lookup and cover_lookup.exists():
                cover_path = cover_lookup
            else:
                cover_path = f"{str(BASE_DIR)}/cache/{cover_hash}.png"
                self.img_cache[cover_hash] = Path(cover_path)
                with open(cover_path, "wb") as f:
                    f.write(cover_bytes)

        meta = TinyTag.get(path)
        return Metadata(
            path=path,
            title=meta.title,
            artist=meta.artist,
            album=meta.album,
            filename=meta.filename,
            album_art_path=cover_path,
            duration_seconds=meta.duration,
        )

    def toggle_play(self) -> None:
        if not self.media_loaded:
            pass
        elif self.player.playing:
            self.pause()
        elif not self.player.playing:
            self.play()

    def next(self) -> None:
        if len(self.queue) > 0:
            obj = self.queue.pop(0)
            if obj.path:
                if self.meta.is_some():
                    self.played_append(self.meta)

                self.load_file(obj.path)
                self.play()

                self.watch_queue()
                self.watch_played()
            else:
                exit("Metadata instance from queue didnt have path field.")

    def previous(self) -> None:
        if len(self.played) > 0:
            obj = self.played.pop(-1)
            if obj.path:
                if self.meta.is_some():
                    self.queue_append(self.meta)

                self.load_file(obj.path)
                self.play()

                self.watch_played()
                self.watch_queue()
            else:
                exit("Metadata instance from played didnt have path field.")

    # Reset app as if it was just launched
    def clear(self) -> None:
        self.media_loaded = False
        self.meta = Metadata()
        self.player.stop()
        self.player = Playback()
        self.queue.clear()
        self.played.clear()

        widget = self.query_one(TimeRemaining)
        widget.media_position = 0
        widget.media_length = 0

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
