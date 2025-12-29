import json
import re
import random
from core.interfaces import ToolExecutor, LLMProvider
from core.enums import JarvisMode
from core.prompts import COMMAND_MODE_PROMPT, CHAT_MODE_PROMPT, TRADE_MODE_PROMPT

class Brain:
    def __init__(self, llm_provider: LLMProvider, tool_executor: ToolExecutor):
        self.llm = llm_provider
        self.tool_executor = tool_executor
        
        # По умолчанию режим команд (безопасный и быстрый)
        self.current_mode = JarvisMode.COMMAND
        self.history = []

    def clear_memory(self):
        self.history = []
        # При очистке памяти сбрасываем режим на дефолтный? 
        # Или оставляем текущий? Давай оставим текущий для удобства.
        print(f"--> [Brain] Память очищена. Текущий режим: {self.current_mode.value}")

    def _get_system_prompt(self):
        """Возвращает промпт для текущего режима"""
        if self.current_mode == JarvisMode.COMMAND:
            return {'role': 'system', 'content': COMMAND_MODE_PROMPT}
        elif self.current_mode == JarvisMode.CHAT:
            return {'role': 'system', 'content': CHAT_MODE_PROMPT}
        elif self.current_mode == JarvisMode.TRADE:
            return {'role': 'system', 'content': TRADE_MODE_PROMPT}
        return {'role': 'system', 'content': COMMAND_MODE_PROMPT}

    def _check_mode_switch(self, text):
        """
        Проверяет, не попросил ли пользователь сменить режим.
        Использует поиск по ключевым корням для гибкости.
        """
        text = text.lower()
        
        # Ключевые слова-триггеры (достаточно корня)
        triggers = ["актив", "включ", "режим", "перейд", "давай"]
        
        # Если в фразе нет триггера действия, выходим (оптимизация)
        if not any(t in text for t in triggers):
            return None

        # 1. Голосовой режим / Чат
        if any(w in text for w in ["голос", "чат", "болта", "разговор"]):
            if self.current_mode != JarvisMode.CHAT:
                self.current_mode = JarvisMode.CHAT
                self.history = []
                return "Голосовой режим активирован, сэр. Я вас слушаю."
            return "Мы уже в голосовом режиме, сэр."

        # 2. Торговый режим
        if any(w in text for w in ["торгов", "трейд", "бирж", "крипт"]):
            if self.current_mode != JarvisMode.TRADE:
                self.current_mode = JarvisMode.TRADE
                self.history = []
                return "Режим торговли активирован. Жду ваших ордеров."
            return "Торговый протокол уже активен."

        # 3. Командный режим
        if any(w in text for w in ["команд", "управлени", "мак", "mac", "компьютер"]):
            if self.current_mode != JarvisMode.COMMAND:
                self.current_mode = JarvisMode.COMMAND
                self.history = []
                return "Режим команд активирован. Управление системами восстановлено."
            return "Я уже ожидаю ваших команд, сэр."
            
        return None

    def think(self, user_text):
        # 1. Проверка на смену режима (Приоритет №1)
        mode_switch_response = self._check_mode_switch(user_text)
        if mode_switch_response:
            print(f"--> [MODE] Переключение на: {self.current_mode}")
            return mode_switch_response

        # 2. Формируем контекст с учетом текущего режима
        if len(self.history) > 10:
            self.history = self.history[-5:]

        messages = [self._get_system_prompt()] + self.history + [{'role': 'user', 'content': user_text}]
        
        print(f"--> [Brain] Думаю (Режим: {self.current_mode.value})...")
        
        try:
            # Запрос к LLM
            content = self.llm.generate_response(messages)
            
            # 3. Обработка ответа в зависимости от режима
            
            # --- РЕЖИМ КОМАНД И ТОРГОВЛИ (Ожидаем JSON) ---
            if self.current_mode in [JarvisMode.COMMAND, JarvisMode.TRADE]:
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        command_data = json.loads(json_match.group(0))
                        print(f"--> [CMD] {command_data}")
                        
                        # Если режим торговли - пока просто выводим (в будущем отправим в BybitService)
                        if self.current_mode == JarvisMode.TRADE:
                            return f"Принял ордер: {json.dumps(command_data, ensure_ascii=False)}"
                        
                        # Если режим команд - выполняем через MacController
                        result = self.tool_executor.execute(command_data)
                        
                        # Короткий ответ для TTS
                        self.history.append({'role': 'user', 'content': user_text})
                        self.history.append({'role': 'assistant', 'content': "Готово"})
                        return result
                        
                    except Exception as e:
                        print(f"[JSON Error] {e}")
                        return "Ошибка в данных команды."
                else:
                    # Если LLM не вернула JSON в командном режиме
                    return "Я не понял команду. В этом режиме я принимаю только приказы."

            # --- РЕЖИМ ЧАТА (Просто текст) ---
            else:
                self.history.append({'role': 'user', 'content': user_text})
                self.history.append({'role': 'assistant', 'content': content})
                return content

        except Exception as e:
            return f"Сбой обработки: {e}"