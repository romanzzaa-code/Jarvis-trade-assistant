import pvporcupine
from pvrecorder import PvRecorder
import time
import numpy as np # <-- Добавляем numpy
from config import Config, ACCESS_KEY

class MicrophoneService:
    def __init__(self):
        self.porcupine = pvporcupine.create(
            access_key=ACCESS_KEY, 
            keywords=[Config.WAKE_WORD],
            sensitivities=[Config.PICOVOICE_SENSITIVITY] 
        )
        self.recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)
        self.is_running = False

    def start(self):
        if not self.is_running:
            self.recorder.start()
            self.is_running = True

    def stop(self):
        if self.is_running:
            self.recorder.stop()
            self.is_running = False

    def listen_for_wake_word(self):
        if not self.is_running: self.start()
        pcm = self.recorder.read()
        result = self.porcupine.process(pcm)
        return result >= 0

    def record_utterance(self): # -> np.ndarray
        """
        Записывает фразу и возвращает numpy-массив float32, готовый для Whisper.
        """
        if not self.is_running: self.start()
        
        frames = []
        silent_chunks = 0
        print("   (Слушаю...)")
        
        while True:
            frame = self.recorder.read()
            frames.extend(frame)
            
            # Расчет громкости (RMS) для детекции тишины
            rms = sum(abs(f) for f in frame) / len(frame)
            
            if rms < Config.SILENCE_THRESHOLD:
                silent_chunks += 1
            else:
                silent_chunks = 0
            
            # Условие выхода: тишина более N чанков ИЛИ запись слишком длинная
            if (silent_chunks > Config.MAX_SILENT_CHUNKS and len(frames) > 3000) or len(frames) > 200000:
                break
        
        # --- ИЗМЕНЕНИЕ: Конвертация в Float32 для Whisper ---
        # PvRecorder выдает int16 (от -32768 до 32767). 
        # Whisper требует float32 (от -1.0 до 1.0).
        audio_data = np.array(frames, dtype=np.int16).astype(np.float32) / 32768.0
        
        return audio_data

    def cleanup(self):
        self.recorder.delete()
        self.porcupine.delete()