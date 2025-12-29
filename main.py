import time
import os
import traceback
from config import Config
from infrastructure.microphone import MicrophoneService
from infrastructure.stt import WhisperService
from infrastructure.tts import SpeakerService
from infrastructure.mac_os import MacController
from infrastructure.llm import OllamaService  # <--- Добавлен импорт LLM
from core.brain import Brain
from core.interfaces import ToolExecutor

# Список слов для выхода из диалога
STOP_WORDS = ["спасибо", "хватит", "отбой", "конец связи", "пока"]

# --- [ADAPTER PATTERN] ---
# Адаптер теперь создает экземпляр контроллера, а не использует статику
class MacExecutorAdapter(ToolExecutor):
    def __init__(self):
        # Композиция: Адаптер "владеет" экземпляром контроллера
        self.controller = MacController()

    def execute(self, command_data: dict) -> str:
        return self.controller.run(command_data)
# -------------------------

def run_dialogue_session(ear, stt, brain, speaker):
    """
    Внутренний цикл активного диалога.
    """
    session_active = True
    last_interaction_time = time.time()
    # Время ожидания перед уходом в сон (20 секунд тишины)
    TIMEOUT_SECONDS = 20.0 

    print("--> [Session] Сессия диалога открыта.")
    ear.start() 

    while session_active:
        # 1. Проверка тайм-аута
        if time.time() - last_interaction_time > TIMEOUT_SECONDS:
            print("\n[i] Тайм-аут. Уход в режим ожидания.")
            ear.stop()
            session_active = False
            break

        # 2. Запись фразы пользователя (теперь возвращает массив numpy, а не путь к файлу)
        audio_data = ear.record_utterance()
        
        # Если массив слишком короткий (шум < 0.5 сек), игнорируем
        # 16000 семплов * 0.5 сек = 8000
        if len(audio_data) < 8000:
            continue

        # 3. Распознавание речи (STT) - передаем данные напрямую
        user_text = stt.transcribe(audio_data)
        
        # (Удаление файла больше не нужно, так как мы работаем в RAM)

        # Если ничего внятного не услышал - пропускаем
        if not user_text or len(user_text) < 2:
            continue

        print(f"Вы: {user_text}")
        last_interaction_time = time.time() # Сбрасываем таймер тишины

        # 4. Проверка на стоп-слова
        if any(word in user_text.lower() for word in STOP_WORDS):
            ear.stop()
            speaker.speak("До связи, сэр.")
            session_active = False
            break

        # 5. Обработка мозгом (Brain)
        response = brain.think(user_text)

        # 6. Озвучка ответа (TTS)
        ear.stop() 
        speaker.speak(response)
        
        # Небольшая пауза, чтобы эхо утихло
        time.sleep(Config.REVERB_TAIL_SECONDS) 
        ear.start() 

def run_app():
    print("--- [INIT] Инициализация модулей... ---")
    
    try:
        # 1. Инициализация Микрофона (Picovoice)
        ear = MicrophoneService()
        print(f"1. Микрофон готов (Чувствительность: {Config.PICOVOICE_SENSITIVITY}).")
        
        # 2. Инициализация STT (Whisper)
        stt = WhisperService()
        print("2. Whisper (STT) загружен.")
        
        # 3. Сборка Мозга (Dependency Injection)
        # Создаем сервис LLM
        llm_service = OllamaService(model_name='llama3.1')
        
        # Создаем исполнителя команд
        mac_executor = MacExecutorAdapter()
        
        # Передаем ОБЕ зависимости в мозг: и LLM, и Руки
        brain = Brain(llm_provider=llm_service, tool_executor=mac_executor) 
        print("3. Мозг готов (Ollama подключена).")
        
        # 4. Инициализация Динамиков (TTS)
        speaker = SpeakerService()
        print("4. Динамики готовы.")

        print(f"--- ДЖАРВИС: СИСТЕМА АКТИВНА [{Config.DEVICE}] ---")
        
        speaker.play_sound("run")
        brain.clear_memory()

        # Запускаем прослушивание Wake Word
        ear.start()
        print("--> Жду команду (Loop started)...")

        while True:
            # Слушаем ключевое слово "Джарвис"
            if ear.listen_for_wake_word():
                print("\n[!] ДЖАРВИС УСЛЫШАЛ ВАС")
                
                ear.stop()
                speaker.play_sound("greeting")
                time.sleep(0.3)
                
                # Передаем управление в диалоговую сессию
                run_dialogue_session(ear, stt, brain, speaker)
                
                print("--- Конец сессии. Стираю память. ---")
                brain.clear_memory()
                
                print("--- Возврат в режим ожидания (Слушаю 'Джарвис') ---")
                ear.start()

    except Exception:
        print("\n!!! КРИТИЧЕСКАЯ ОШИБКА !!!")
        traceback.print_exc()
    except KeyboardInterrupt:
        print("\nОтключение систем...")
    finally:
        if 'ear' in locals():
            ear.cleanup()

if __name__ == "__main__":
    run_app()