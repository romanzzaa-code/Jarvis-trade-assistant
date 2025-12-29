import whisper
import os
import numpy as np # На всякий случай для аннотаций
from config import Config

class WhisperService:
    def __init__(self):
        print(f"--- Загрузка Whisper ({Config.DEVICE}) ---")
        self.model = whisper.load_model("base", device=Config.DEVICE)

    def transcribe(self, audio_data):
        """
        audio_data: может быть путем к файлу (str) ИЛИ numpy-массивом.
        """
        # Если это строка (путь), проверяем, существует ли файл
        if isinstance(audio_data, str):
            if not os.path.exists(audio_data):
                return ""
        
        # Если это пустой массив или None
        if audio_data is None or len(audio_data) == 0:
            return ""

        try:
            # Whisper сам разберется: если это np.array, он обработает его напрямую
            result = self.model.transcribe(
                audio_data, 
                language="russian", 
                fp16=True,
                condition_on_previous_text=False
            )
            return result["text"].strip()
        except Exception as e:
            print(f"Ошибка STT: {e}")
            return ""