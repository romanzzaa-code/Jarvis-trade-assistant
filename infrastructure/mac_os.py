import subprocess

class MacController:
    def __init__(self):
        self._commands = {
            "open_app": self._open_app_smart,
            "set_volume": self._set_volume,
            "open_website": self._open_url,
            "error": self._handle_error 
        }

    def run(self, command_data: dict) -> str:
        """
        Находит нужный метод в реестре по ключу 'tool' и запускает его.
        """
        tool = command_data.get("tool")
        arg = command_data.get("args")
        
        # Получаем функцию из словаря. Если ключа нет — возвращаем None
        handler = self._commands.get(tool)
        
        if handler:
            try:
                return handler(arg)
            except Exception as e:
                return f"Ошибка при выполнении команды '{tool}': {e}"
            
        return f"Я пока не умею выполнять команду: {tool}"

    def _set_volume(self, level):
        try:
            vol = int(level)
            # Ограничиваем громкость от 0 до 100 для безопасности ушей
            vol = max(0, min(100, vol))
            subprocess.run(["osascript", "-e", f"set volume output volume {vol}"])
            return f"Громкость установлена на {vol}%"
        except ValueError:
            return "Ошибка: уровень громкости должен быть числом."

    def _open_app_smart(self, app_name):
        print(f"[CMD] Пробую открыть приложение: {app_name}")
        
        # 1. Пробуем открыть как приложение
        result = subprocess.run(["open", "-a", app_name], capture_output=True, text=True)
        
        if result.returncode == 0:
            return f"Запускаю {app_name}"
        else:
            # 2. Smart Fallback: если приложения нет, пробуем как сайт
            print(f"[WARN] Приложение не найдено. Пробую открыть как сайт.")
            return self._open_url(app_name)

    def _open_url(self, url_fragment):
        if not url_fragment.startswith("http"):
            if "." not in url_fragment:
                url = f"https://{url_fragment}.com"
            else:
                url = f"https://{url_fragment}"
        else:
            url = url_fragment

        subprocess.run(["open", url])
        return f"Открываю {url}"
        
    def _handle_error(self, arg):
        # Это заглушка, чтобы Джарвис не пытался выполнять "not_a_command"
        return "В командном режиме я не веду диалоги, сэр. Только приказы."    