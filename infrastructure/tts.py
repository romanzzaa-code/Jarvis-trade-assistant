import torch
import os
import subprocess
import re
import random
from num2words import num2words
from config import Config

try:
    from TTS.api import TTS
except ImportError:
    TTS = None

class SpeakerService:
    def __init__(self):
        print(f"--> [TTS] Инициализация (Движок: {Config.TTS_ENGINE})...")
        self.device = Config.DEVICE
        self.model = None
        self.model_silero = None 
        
        # --- БАНК ЗВУКОВ ---
        self.sound_bank = {
            'greeting': ['sounds/greet1.wav', 'sounds/greet2.wav', 'sounds/greet3.wav'],
            'ok': ['sounds/ok1.wav', 'sounds/ok2.wav', 'sounds/ok3.wav', 'sounds/ok4.wav'],
            'run': ['sounds/run.wav'], 
            'ready': ['sounds/game_mode.wav'], 
            'error': ['sounds/not_found.wav']
        }

        if Config.TTS_ENGINE == 'xtts':
            self._init_xtts()
        
        if not self.model:
            self._init_silero()

    def _init_xtts(self):
        if TTS is None: return
        if not os.path.exists(Config.VOICE_SAMPLE_PATH): return
        try:
            print("--> [TTS] Загрузка XTTS...")
            self.model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
            print("--> [TTS] XTTS готов.")
        except Exception as e:
            print(f"!!! [TTS Error] XTTS упал: {e}")

    def _init_silero(self):
        try:
            print("--> [TTS] Загрузка Silero (V4)...")
            self.model_silero, _ = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                         model='silero_tts',
                                         language='ru',
                                         speaker='v4_ru')
            self.model_silero.to('cpu')
            print("--> [TTS] Silero готов.")
        except Exception as e:
            print(f"!!! [TTS Critical] Silero не загрузился: {e}")

    def play_sound(self, category):
        if category in self.sound_bank:
            sound_file = random.choice(self.sound_bank[category])
            if os.path.exists(sound_file):
                subprocess.run(["afplay", sound_file])
                return True
        return False

    def _filter_text(self, text):
        if not text: return ""
        text = re.sub(r"(\d+)", lambda x: num2words(int(x.group(0)), lang='ru'), text)
        if not self.model: 
            mapping = {'jarvis': 'джарвис', 'sir': 'сэр', 'youtube': 'ютуб'}
            lower = text.lower()
            for k, v in mapping.items():
                if k in lower: text = re.sub(k, v, text, flags=re.IGNORECASE)
            text = re.sub(r"[^а-яА-ЯёЁ0-9\s.,!?-]", "", text)
        return text

    def speak(self, text):
        if not text: return
        
        text_lower = text.lower()
        
        # [FIX] Теперь ЛЮБОЕ действие (открываю, запускаю, выполняю) вызывает звук 'ok'
        # Мы убрали 'run' отсюда. run.wav играет ТОЛЬКО при старте main.py.
        # Все эти слова - это просто подтверждение приказа.
        action_triggers = [
            "выполняю", "слушаюсь", "сделано", "готово", "принято", "одну минуту",
            "запускаю", "открываю", "включаю", "активирую"
        ]
        
        if any(x in text_lower for x in action_triggers):
            if self.play_sound('ok'): return
             
        if any(x in text_lower for x in ["привет", "на связи", "да сэр", "здравствуйте"]):
             if self.play_sound('greeting'): return
             
        # Далее генерация речи...
        clean_text = self._filter_text(text)
        print(f"🗣 Джарвис: {clean_text}")
        output_path = "response.wav"

        if self.model:
            try:
                self.model.tts_to_file(text=clean_text, speaker_wav=Config.VOICE_SAMPLE_PATH, language="ru", file_path=output_path)
                subprocess.run(["afplay", output_path])
                os.remove(output_path)
                return
            except: pass
        
        if self.model_silero:
            try:
                self.model_silero.save_wav(text=clean_text, speaker='aidar', sample_rate=48000, audio_path=output_path)
                subprocess.run(["afplay", output_path])
                os.remove(output_path)
                return
            except: pass

        subprocess.run(["say", text])