import whisper
import os
from config import Config

class WhisperService:
    def __init__(self):
        print(f"--- Загрузка Whisper ({Config.DEVICE}) ---")
        self.model = whisper.load_model("base", device=Config.DEVICE)

    def transcribe(self, audio_path):
        if not os.path.exists(audio_path): return ""
        try:
            # Отключаем галлюцинации через condition_on_previous_text=False
            result = self.model.transcribe(
                audio_path, 
                language="russian", 
                fp16=True,
                condition_on_previous_text=False
            )
            return result["text"].strip()
        except Exception as e:
            print(f"Ошибка STT: {e}")
            return ""