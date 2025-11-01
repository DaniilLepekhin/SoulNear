import os
import subprocess

from openai import AsyncOpenAI

from config import OPENAI_API_KEY


_openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def transcribe_audio(filename: str) -> str:
    """Run Whisper transcription on the provided audio file."""
    try:
        with open(filename, "rb") as audio_file:
            response = await _openai_client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file,
                response_format="text",
                temperature=0,
            )
    except Exception as exc:  # pragma: no cover - network issues
        raise RuntimeError("Failed to transcribe audio") from exc

    if isinstance(response, str):
        return response.strip()

    text = getattr(response, "text", "").strip()
    if text:
        return text

    raise RuntimeError("Transcription returned empty result")


def convert_voice(input_path, output_path):
    command = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-ac",
        "1",
        "-ar",
        "16000",
        "-sample_fmt",
        "s16",
        output_path,
    ]

    process = subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if process.returncode != 0 or not os.path.exists(output_path):
        raise RuntimeError("Failed to convert voice message to WAV")


