import ollama
from core.interfaces import LLMProvider

class OllamaService(LLMProvider):
    def __init__(self, model_name='llama3.1'):
        self.model_name = model_name

    def generate_response(self, messages: list) -> str:
        try:
            response = ollama.chat(model=self.model_name, messages=messages)
            return response['message']['content']
        except Exception as e:
            print(f"!!! Ошибка Ollama: {e}")
            return "Произошел сбой нейросети, сэр."