from abc import ABC, abstractmethod

class ToolExecutor(ABC):
    @abstractmethod
    def execute(self, command_data: dict) -> str:
        pass

# --- ДОБАВЛЯЕМ ЭТОТ КЛАСС ---
class LLMProvider(ABC):
    @abstractmethod
    def generate_response(self, messages: list) -> str:
        """
        Принимает список сообщений (историю диалога) и возвращает ответ (строку).
        """
        pass