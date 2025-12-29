import subprocess

class MacController:
    @staticmethod
    def run(command_data):
        """Принимает словарь {'tool': ..., 'args': ...}"""
        tool = command_data.get("tool")
        arg = command_data.get("args")
        
        if tool == "open_app":
            return MacController._open_app_smart(arg)
        
        elif tool == "set_volume":
            try:
                subprocess.run(["osascript", "-e", f"set volume output volume {int(arg)}"])
                return f"Громкость {arg}%"
            except: return "Ошибка громкости"
            
        elif tool == "open_website":
            return MacController._open_url(arg)
            
        return "Неизвестная команда"

    @staticmethod
    def _open_app_smart(app_name):
        print(f"[CMD] Пробую открыть приложение: {app_name}")
        
        # 1. Пытаемся открыть как приложение
        # capture_output=True позволяет перехватить текст ошибки, чтобы он не лез в консоль
        result = subprocess.run(["open", "-a", app_name], capture_output=True, text=True)
        
        if result.returncode == 0:
            return f"Запускаю {app_name}"
        else:
            # 2. Если приложения нет (код ошибки != 0), пробуем открыть как сайт
            # Это "Smart Fallback"
            print(f"[WARN] Приложение не найдено. Пробую как сайт: {app_name}.com")
            return MacController._open_url(app_name)

    @staticmethod
    def _open_url(url_fragment):
        # Если это не полноценная ссылка, делаем её таковой
        if not url_fragment.startswith("http"):
            # Простая эвристика: если нет точек, добавляем .com (для youtube, google и т.д.)
            if "." not in url_fragment:
                url = f"https://{url_fragment}.com"
            else:
                url = f"https://{url_fragment}"
        else:
            url = url_fragment

        subprocess.run(["open", url])
        return f"Открываю сайт {url_fragment}"