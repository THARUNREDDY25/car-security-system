"""
core/voice_capture.py — Stage 3 (Part A)
Records a short voice clip from the USB microphone
using pyaudio and saves it as a .wav for SpeechBrain.
"""

import pyaudio
import wave
import os
import logging
import tempfile

logger = logging.getLogger("voice_capture")


class VoiceCapture:
    def __init__(self, settings):
        self.settings    = settings
        self.sample_rate = settings.AUDIO_SAMPLE_RATE
        self.channels    = settings.AUDIO_CHANNELS
        self.chunk       = settings.AUDIO_CHUNK
        self.duration    = settings.AUDIO_RECORD_SECONDS
        self._pa         = pyaudio.PyAudio()
        logger.info("VoiceCapture initialized (%.0f Hz, %ds clip).",
                    self.sample_rate, self.duration)

    # ── Public API ──────────────────────────────────────────────────────────

    def record_clip(self) -> str:
        """
        Record AUDIO_RECORD_SECONDS of audio from the USB mic.
        Saves to a temp .wav file and returns the file path.
        """
        logger.info("Recording %ds voice clip...", self.duration)

        stream = self._pa.open(
            format              = pyaudio.paInt16,
            channels            = self.channels,
            rate                = self.sample_rate,
            input               = True,
            frames_per_buffer   = self.chunk,
        )

        frames = []
        num_chunks = int(self.sample_rate / self.chunk * self.duration)
        for _ in range(num_chunks):
            data = stream.read(self.chunk, exception_on_overflow=False)
            frames.append(data)

        stream.stop_stream()
        stream.close()

        # Save to temp wav
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(tmp.name, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self._pa.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b"".join(frames))

        logger.info("Voice clip saved to %s", tmp.name)
        return tmp.name

    def cleanup(self):
        self._pa.terminate()
