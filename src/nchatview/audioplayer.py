from textual.app import App, ComposeResult
from textual.widgets import Header, Static, ProgressBar, Footer, Button
from textual.containers import Vertical, Horizontal
from textual import on
import time
import sys
import threading
import sounddevice as sd
import soundfile as sf
import numpy as np
from pathlib import Path
import subprocess
import tempfile
import os


class AudioPlayer:
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.samplerate = None
        self.audio_data = None
        self.position = 0.0
        self.volume = 1.0
        self.playing = False
        self.lock = threading.Lock()
        self.stream = None
        self.playback_speed = 1.0

        try:
            self.audio_data, self.samplerate = sf.read(self.file_path)
        except sf.LibsndfileError:
            self._convert_with_ffmpeg()

        if self.audio_data.dtype != np.float32:
            self.audio_data = self.audio_data.astype(np.float32)

        if self.audio_data.ndim == 1:
            self.audio_data = self.audio_data.reshape(-1, 1)

    def _convert_with_ffmpeg(self):
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
                temp_wav = tmpfile.name

            ffmpeg_cmd = [
                "ffmpeg",
                "-i",
                str(self.file_path),
                "-c:a",
                "pcm_f32le",
                "-ar",
                "44100",
                "-ac",
                "2",
                "-y",
                temp_wav,
            ]

            subprocess.run(
                ffmpeg_cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            self.audio_data, self.samplerate = sf.read(temp_wav)
        finally:
            if os.path.exists(temp_wav):
                os.remove(temp_wav)

    def _playback_loop(self):
        if self.stream:
            self.stream.close()
        with sd.OutputStream(
            samplerate=self.samplerate,
            channels=self.audio_data.shape[1],
            callback=self._audio_callback,
            blocksize=1024,
        ) as self.stream:
            while self.playing:
                time.sleep(0.01)

    def _audio_callback(self, outdata, frames, time, status):
        with self.lock:
            if not self.playing:
                raise sd.CallbackStop

            adjusted_frames = int(frames * self.playback_speed)
            start_sample = int(self.position * self.samplerate)
            end_sample = start_sample + adjusted_frames

            if start_sample >= len(self.audio_data):
                raise sd.CallbackStop

            if end_sample > len(self.audio_data):
                end_sample = len(self.audio_data)
                self.playing = False

            chunk = self.audio_data[start_sample:end_sample] * self.volume
            outdata[:] = chunk
            self.position += adjusted_frames / self.samplerate

    def play_pause(self):
        if not self.playing:
            self.playing = True
            self.thread = threading.Thread(target=self._playback_loop)
            self.thread.start()
        else:
            with self.lock:
                self.playing = False

    def seek(self, seconds):
        with self.lock:
            self.position = np.clip(seconds, 0, self.duration)

    def set_volume(self, volume):
        with self.lock:
            self.volume = np.clip(volume, 0.0, 1.0)

    def set_playback_speed(self, speed):
        with self.lock:
            was_playing = self.playing
            if was_playing:
                self.playing = False  # Stop current playback

            self.playback_speed = np.clip(speed, 0.5, 2.0)

            if was_playing:
                self.playing = True  # Restart with new speed
                self.thread = threading.Thread(target=self._playback_loop)
                self.thread.start()

    @property
    def duration(self):
        return len(self.audio_data) / self.samplerate


class AudioPlayerApp(App[None]):
    CSS = """
        Screen {
            layout: vertical;
            padding: 1;
        }
        #title_card {
            padding: 1;
            border: round $accent;
            width: 100%;
        }
        #title {
            text-style: bold;
            color: $warning;
            text-align: center;
        }
        #metadata {
            padding: 1 2;
            background: $boost;
            border: round $accent;
        }
        #controls {
            height: 5;
            align: center middle;
            border: round $accent;
        }
        #speed_controls {
            height: 3;
            width: 50%;
            align: center middle;
        }
        #volume_container {
            padding: 1;
            border: round $accent;
        }
        Button {
            width: 16;
            margin: 1 2;
        }
        #status_bar {
            padding: 1;
            background: $boost;
            text-align: center;
        }
    """

    BINDINGS = [
        ("space", "play_pause", "Play/Pause"),
        ("s,right", "seek_forward", "Seek +5s"),
        ("a,left", "seek_backward", "Seek -5s"),
        ("up", "volume_up", "Volume Up"),
        ("down", "volume_down", "Volume Down"),
        ("b", "speed_up", "Speed +"),
        ("n", "speed_down", "Speed -"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, file_path: str) -> None:
        super().__init__()
        self.audio_player = AudioPlayer(file_path)
        self.title_text = f"🎵 {Path(file_path).name}"
        self.duration = self.audio_player.duration
        self.sample_rate = self.audio_player.samplerate
        self.channels = self.audio_player.audio_data.shape[1]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Vertical(
                Static(self.title_text, id="title"),
                ProgressBar(id="progress", show_eta=False),
                id="title_card",
            ),
            Static(
                f"⏱ {self.duration:.1f}s | 🎚 {self.sample_rate}Hz | "
                f"🎛 {self.channels}ch | 🐇 {self.audio_player.playback_speed:.1f}x",
                id="metadata",
            ),
            Horizontal(
                Button("⏮ -5s (A/←)", id="seek_back"),
                Button("⏯ Play/Pause (Space)", id="play_pause"),
                Button("⏭ +5s (S/→)", id="seek_forward"),
                id="controls",
            ),
            Horizontal(
                Button("🐢 Speed - (N)", id="speed_down"),
                Button("🐇 Speed + (B)", id="speed_up"),
                id="speed_controls",
            ),
            Vertical(
                Static("🔊 Volume (↑/↓)", id="volume_label"),
                ProgressBar(id="volume_bar", total=1.0, show_eta=False),
                id="volume_container",
            ),
            Static(id="status_bar"),
        )
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(0.1, self.update_ui)
        self.query_one("#progress", ProgressBar).update(total=self.duration)
        self.update_status(f"Loaded {self.title_text}")

    def update_ui(self) -> None:
        with self.audio_player.lock:
            position = self.audio_player.position
            playing = self.audio_player.playing
            volume = self.audio_player.volume
            speed = self.audio_player.playback_speed

        self.query_one("#progress", ProgressBar).update(progress=position)
        self.query_one("#play_pause", Button).label = (
            f"{'⏸ Pause' if playing else '▶ Play'} (Space)"
        )
        self.query_one("#volume_bar", ProgressBar).update(progress=volume)
        self.query_one("#metadata", Static).update(
            f"⏱ {position:.1f}/{self.duration:.1f}s | 🎚 {self.sample_rate}Hz | "
            f"🎛 {self.channels}ch | 🐇 {speed:.1f}x"
        )

    def update_status(self, message: str, timeout: float = 2.0):
        self.query_one("#status_bar", Static).update(message)
        self.set_timer(
            timeout, lambda: self.query_one("#status_bar", Static).update("")
        )

    @on(Button.Pressed)
    def handle_button(self, event: Button.Pressed):
        actions = {
            "seek_back": self.action_seek_backward,
            "seek_forward": self.action_seek_forward,
            "play_pause": self.action_play_pause,
            "speed_up": self.action_speed_up,
            "speed_down": self.action_speed_down,
        }
        if event.button.id in actions:
            actions[event.button.id]()

    def action_play_pause(self):
        self.audio_player.play_pause()
        self.update_status("Playing" if self.audio_player.playing else "Paused")

    def action_seek_forward(self):
        self.audio_player.seek(min(self.audio_player.position + 5, self.duration))
        self.update_status("Seeked +5s")

    def action_seek_backward(self):
        self.audio_player.seek(max(self.audio_player.position - 5, 0))
        self.update_status("Seeked -5s")

    def action_speed_up(self):
        new_speed = min(self.audio_player.playback_speed + 0.1, 2.0)
        self.audio_player.set_playback_speed(new_speed)
        self.update_status(f"Speed: {new_speed:.1f}x")

    def action_speed_down(self):
        new_speed = max(self.audio_player.playback_speed - 0.1, 0.5)
        self.audio_player.set_playback_speed(new_speed)
        self.update_status(f"Speed: {new_speed:.1f}x")

    def action_volume_up(self):
        new_vol = min(self.audio_player.volume + 0.1, 1.0)
        self.audio_player.set_volume(new_vol)
        self.update_status(f"Volume: {new_vol * 100:.0f}%")

    def action_volume_down(self):
        new_vol = max(self.audio_player.volume - 0.1, 0.0)
        self.audio_player.set_volume(new_vol)
        self.update_status(f"Volume: {new_vol * 100:.0f}%")

    def action_quit(self):
        self.audio_player.playing = False
        self.exit()


def play_file(file_path: str):
    app = AudioPlayerApp(file_path)
    app.audio_player.play_pause()
    app.run()
