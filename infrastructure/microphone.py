import pvporcupine
from pvrecorder import PvRecorder
import wave
import struct
import time
from config import Config, ACCESS_KEY

class MicrophoneService:
    def __init__(self):
        # [FIX] Передаем sensitivities
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
        """Возвращает True, если услышал имя"""
        if not self.is_running: self.start()
        
        # Чтение блокирующее, поэтому CPU не сгорит без sleep
        pcm = self.recorder.read()
        result = self.porcupine.process(pcm)
        return result >= 0

    def record_utterance(self) -> str:
        # ... (этот метод оставьте без изменений, как был) ...
        # Копирую его сюда кратко, чтобы вы не потеряли контекст
        if not self.is_running: self.start()
        frames = []
        silent_chunks = 0
        print("   (Слушаю...)")
        while True:
            frame = self.recorder.read()
            frames.extend(frame)
            rms = sum(abs(f) for f in frame) / len(frame)
            if rms < Config.SILENCE_THRESHOLD:
                silent_chunks += 1
            else:
                silent_chunks = 0
            if (silent_chunks > Config.MAX_SILENT_CHUNKS and len(frames) > 3000) or len(frames) > 200000:
                break
        
        filename = "command_buffer.wav"
        with wave.open(filename, 'wb') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(self.recorder.sample_rate)
            f.writeframes(struct.pack('<' + 'h' * len(frames), *frames))
        return filename

    def cleanup(self):
        self.recorder.delete()
        self.porcupine.delete()