import ollama
import json
import re
import random
from core.interfaces import ToolExecutor

class Brain:
    def __init__(self, tool_executor: ToolExecutor):
        self.tool_executor = tool_executor
        
        # Фразы-ответы (триггерят звук 'ok' в tts.py)
        self.ack_phrases = [
            "Выполняю, сэр.",
            "Слушаюсь, сэр.",
            "Запускаю, сэр.",
            "Включаю, сэр.",
            "Открываю, сэр.",
            "Сделано, сэр."
        ]
        
        # [UPDATED] Усиленный промпт для исправления ошибок распознавания
        self.system_prompt = {
            'role': 'system', 
            'content': """
            Ты — Джарвис, ИИ-дворецкий. Обращайся к пользователю "Сэр".
            ТВОЯ ЦЕЛЬ: Управлять компьютером через JSON.
            
            ПРАВИЛА ИСПРАВЛЕНИЯ ОШИБОК РАСПОЗНАВАНИЯ:
            Пользователь может говорить нечетко, ты должен догадаться.
            
            1. BYBIT (Криптобиржа):
               Если слышишь: "байбит", "babbit", "bubit", "bibit", "babik", "buy bit"
               -> ОТВЕЧАЙ: { "tool": "open_website", "args": "bybit.com" }
               
            2. ДРУГИЕ САЙТЫ:
               - "ютуб" -> youtube.com
               - "вк" -> vk.com
               - "телеграм" -> web.telegram.org
            
            3. ПРИЛОЖЕНИЯ:
               - "калькулятор" -> Calculator
               - "сафари" -> Safari
               - "терминал" -> Terminal
            
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
        
        try:
            print(f"--> [Brain] Думаю...")
            response = ollama.chat(model='llama3.1', messages=messages)
            content = response['message']['content']
            
            # --- Обработка команд ---
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
            # ------------------------
            
            self.history.append({'role': 'user', 'content': user_text})
            self.history.append({'role': 'assistant', 'content': content})
            
            return content
            
        except Exception as e:
            return f"Сбой систем: {e}"