from cx_Freeze import setup, Executable
import sys
import os
import site

# Проверяем наличие werkzeug
try:
    import werkzeug
    print("Werkzeug успешно импортирован")
except ImportError:
    print("Ошибка: Werkzeug не найден в окружении!")
    sys.exit(1)

# Определяем базовую настройку: консольное приложение
base = None
if sys.platform in ["win32", "darwin", "linux"]:
    base = "Console"

# Список исполняемых файлов
executables = [
    Executable("app.py", base=base, target_name="AutomaticTradingViewBot")
]

# Динамически получаем путь к site-packages
site_packages = site.getsitepackages()
if not site_packages:
    site_packages = [os.path.join(sys.prefix, "lib", "python" + sys.version[:3], "site-packages")]

# Минимальные настройки сборки
build_options = {
    "includes": ["werkzeug", "flask"],  # Только необходимые модули
    "path": os.pathsep.join(site_packages + sys.path + [os.getcwd()]),
    "silent": False,
}

# Основная настройка
setup(
    name="AutomaticTradingViewBot",
    version="1.0",
    description="Flask-based trading bot",
    options={"build_exe": build_options},
    executables=executables
)