from enum import Enum

class JarvisMode(Enum):
    COMMAND = "command"  # Файлы, приложения, скрипты (JSON)
    CHAT = "chat"        # Разговор (Текст)
    TRADE = "trade"      # Биржа (JSON)