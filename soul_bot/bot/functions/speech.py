import os

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
    os.system(f"ffmpeg -i {input_path} -acodec pcm_s16le -ac 1 -ar 16000 -map_channel 0.0.0 {output_path}")


