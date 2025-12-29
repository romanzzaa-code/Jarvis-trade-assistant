import json
import re
import random
from core.interfaces import ToolExecutor, LLMProvider # Добавляем LLMProvider

class Brain:
    # Внедряем зависимость llm_provider через конструктор
    def __init__(self, llm_provider: LLMProvider, tool_executor: ToolExecutor):
        self.llm = llm_provider  # Теперь мозг использует абстракцию
        self.tool_executor = tool_executor
        
        self.ack_phrases = [
            "Выполняю, сэр.",
            "Слушаюсь, сэр.",
            "Запускаю, сэр.",
            "Включаю, сэр.",
            "Открываю, сэр.",
            "Сделано, сэр."
        ]
        
        self.system_prompt = {
            'role': 'system', 
            'content': """
            Ты — Джарвис, ИИ-дворецкий. Обращайся к пользователю "Сэр".
            ТВОЯ ЦЕЛЬ: Управлять компьютером через JSON.
            
            ПРАВИЛА ИСПРАВЛЕНИЯ ОШИБОК РАСПОЗНАВАНИЯ:
            1. BYBIT: "байбит", "babbit" -> { "tool": "open_website", "args": "bybit.com" }
            2. САЙТЫ: "ютуб" -> youtube.com, "вк" -> vk.com
            3. ПРИЛОЖЕНИЯ: "калькулятор" -> Calculator, "сафари" -> Safari
            
            На команды управления отвечай ТОЛЬКО JSON.
            """
        }
        self.history = []

    def clear_memory(self):
        self.history = []
        print("--> [Brain] Память очищена.")

    def think(self, user_text):
        if len(self.history) > 20:
            self.history = self.history[-10:]

        messages = [self.system_prompt] + self.history + [{'role': 'user', 'content': user_text}]
        
        print(f"--> [Brain] Думаю...")
        
        # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
        # Было: response = ollama.chat(...)
        # Стало: используем наш провайдер
        content = self.llm.generate_response(messages)
        # -----------------------
        
        # --- Логика обработки команд осталась прежней ---
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        
        if json_match:
            try:
                json_str = json_match.group(0)
                command_data = json.loads(json_str)
                print(f"--> [Brain] Команда: {command_data}")
                
                self.tool_executor.execute(command_data)
                
                fast_response = random.choice(self.ack_phrases)
                
                self.history.append({'role': 'user', 'content': user_text})
                self.history.append({'role': 'assistant', 'content': fast_response})
                
                return fast_response
                
            except Exception as e:
                print(f"[Brain Error] {e}")
                return "Возникла проблема при выполнении команды, сэр."
        
        self.history.append({'role': 'user', 'content': user_text})
        self.history.append({'role': 'assistant', 'content': content})
        
        return content