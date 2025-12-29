import torch
import os

# Секреты лучше брать из переменных окружения, но для старта оставим тут
ACCESS_KEY = "ВСТАВЬТЕ_СЮДА_ВАШ_КЛЮЧ" 

class Config:
    WAKE_WORD = 'jarvis'
    DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"
    
    # --- НАСТРОЙКИ ГОЛОСА И СЛУХА ---
    # Чувствительность к имени (0.0 - глухой, 1.0 - слышит каждый шорох)
    # 0.5 - стандарт, 0.7-0.8 - идеально для комфортного общения
    PICOVOICE_SENSITIVITY = 0.8 
    
    SILENCE_THRESHOLD = 300
    MAX_SILENT_CHUNKS = 60
    REVERB_TAIL_SECONDS = 0.5 
    
    TTS_ENGINE = 'silero'
    VOICE_SAMPLE_PATH = "jarvis_sample.wav"