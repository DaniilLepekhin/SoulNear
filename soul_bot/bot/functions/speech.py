import os
import subprocess

import speech_recognition as sr


r = sr.Recognizer()


def recognize(filename):
    try:
        with sr.AudioFile(filename) as source:
            audio_text = r.record(source)
            text = r.recognize_google(audio_text, language='ru_RU')
            print('Converting audio transcripts into text ...')
            print(text)
            return text
    except sr.UnknownValueError:
        print('Google Speech Recognition could not understand audio')
        return "Не удалось распознать аудио."
    except sr.RequestError as e:
        print(f'Could not request results from Google Speech Recognition service; {e}')
        return f"Ошибка сервиса: {e}"


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


