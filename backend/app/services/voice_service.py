"""Voice interaction service using OpenAI's Whisper (STT) and TTS APIs."""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import BinaryIO

from openai import OpenAI

from app.core.config import settings


class VoiceService:
    """Service for handling voice-to-text and text-to-voice conversions."""

    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for voice features")
        self.client = OpenAI(api_key=settings.openai_api_key)

    def transcribe_audio(self, audio_file: BinaryIO, filename: str = "audio.wav") -> str:
        """
        Convert speech to text using OpenAI Whisper.

        Args:
            audio_file: Binary audio file (WAV, MP3, etc.)
            filename: Original filename (helps Whisper detect format)

        Returns:
            Transcribed text
        """
        try:
            # Save to temp file with proper extension
            suffix = Path(filename).suffix or ".wav"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(audio_file.read())
                tmp_path = tmp.name

            # Transcribe using Whisper
            with open(tmp_path, "rb") as audio:
                transcript = self.client.audio.transcriptions.create(
                    model=settings.openai_whisper_model,
                    file=audio,
                    response_format="text",
                )

            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)

            return str(transcript)

        except Exception as e:
            raise RuntimeError(f"Failed to transcribe audio: {e}") from e

    def synthesize_speech(self, text: str, output_format: str = "mp3") -> bytes:
        """
        Convert text to speech using OpenAI TTS.

        Args:
            text: Text to convert to speech
            output_format: Audio format (mp3, opus, aac, flac)

        Returns:
            Audio bytes
        """
        try:
            response = self.client.audio.speech.create(
                model=settings.openai_tts_model,
                voice=settings.openai_tts_voice,
                input=text,
                response_format=output_format,
            )

            return response.content

        except Exception as e:
            raise RuntimeError(f"Failed to synthesize speech: {e}") from e

    def speak(self, text: str) -> bytes:
        """
        Quick helper to convert text to speech (MP3).

        Args:
            text: Text to speak

        Returns:
            MP3 audio bytes
        """
        return self.synthesize_speech(text, "mp3")
