import time
import os
import traceback
from config import Config
from infrastructure.microphone import MicrophoneService
from infrastructure.stt import WhisperService
from infrastructure.tts import SpeakerService
from infrastructure.mac_os import MacController
from core.brain import Brain
from core.interfaces import ToolExecutor

# Список слов для выхода из диалога
STOP_WORDS = ["спасибо", "хватит", "отбой", "конец связи", "пока"]

# --- [ADAPTER PATTERN] ---
# Адаптер для связи абстрактного "Мозга" с конкретным контроллером macOS.
# Это позволяет нам менять исполнителя (например, на Windows) без переписывания мозга.
class MacExecutorAdapter(ToolExecutor):
    def execute(self, command_data: dict) -> str:
        return MacController.run(command_data)
# -------------------------

def run_dialogue_session(ear, stt, brain, speaker):
    """
    Внутренний цикл активного диалога.
    Запускается ПОСЛЕ того, как Джарвис услышал свое имя.
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
            # Можно добавить звук выключения, если есть (speaker.play_sound('off'))
            session_active = False
            break

        # 2. Запись фразы пользователя
        audio_file = ear.record_utterance()
        
        # Если файл слишком маленький (шум < 3kb), игнорируем и сбрасываем цикл
        if os.path.getsize(audio_file) < 3000:
            if os.path.exists(audio_file): os.remove(audio_file)
            continue

        # 3. Распознавание речи (STT)
        user_text = stt.transcribe(audio_file)
        
        # Удаляем временный файл
        if os.path.exists(audio_file): os.remove(audio_file)

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
        # Мозг сам решит: выполнить команду или просто ответить.
        # Если команда выполнена, он вернет фразу типа "Выполняю, сэр".
        response = brain.think(user_text)

        # 6. Озвучка ответа (TTS)
        ear.stop() # Глушим микрофон, чтобы Джарвис не слышал сам себя
        speaker.speak(response)
        
        # Небольшая пауза, чтобы эхо утихло
        time.sleep(Config.REVERB_TAIL_SECONDS) 
        ear.start() # Снова включаем слух

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
        mac_executor = MacExecutorAdapter() # Создаем руки
        brain = Brain(tool_executor=mac_executor) # Передаем руки в мозг
        print("3. Мозг готов.")
        
        # 4. Инициализация Динамиков (TTS)
        speaker = SpeakerService()
        print("4. Динамики готовы.")

        print(f"--- ДЖАРВИС: СИСТЕМА АКТИВНА [{Config.DEVICE}] ---")
        
        # [SOUND] Играем звук запуска (run.wav) вместо речи
        # Это создает эффект мгновенной готовности
        speaker.play_sound("run")
        
        # Очищаем память контекста при старте
        brain.clear_memory()

        # Запускаем прослушивание Wake Word
        ear.start()
        print("--> Жду команду (Loop started)...")

        while True:
            # Слушаем ключевое слово "Джарвис"
            # ВАЖНО: Здесь НЕТ time.sleep, так как ear.listen_for_wake_word()
            # работает синхронно с потоком аудио. Добавление sleep приведет к глухоте.
            if ear.listen_for_wake_word():
                print("\n[!] ДЖАРВИС УСЛЫШАЛ ВАС")
                
                ear.stop()
                
                # [SOUND] Играем приветствие (greet1.wav и т.д.)
                speaker.play_sound("greeting")
                
                # Короткая пауза (300мс), чтобы звук приветствия успел проиграться 
                # и не наложился на вашу следующую команду
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