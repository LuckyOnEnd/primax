import os
import subprocess
import sys


def check_python():
    try:
        result = subprocess.run(
            [sys.executable, "--version"], check=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
            )
        print("✅ Python найден:", result.stdout.decode().strip())
        return True
    except FileNotFoundError:
        print("❌ Python не найден! Возможно, он не установлен или не добавлен в PATH.")
    except Exception as ex:
        print(f"⚠️ Ошибка при проверке Python: {ex}")
    return False


def install_requirements():
    if not os.path.exists("requirements.txt"):
        print("⚠️ Файл requirements.txt не найден, пропускаем установку зависимостей.")
        return False

    print("📦 Устанавливаем зависимости...")
    result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    if result.returncode == 0:
        print("✅ Установка зависимостей завершена.")
        return True
    else:
        print("❌ Ошибка при установке зависимостей!")
        return False


def run_fastapi():
    print("🚀 Запуск FastAPI...")
    subprocess.run([sys.executable, "app.py"])


if __name__ == "__main__":
    if not check_python():
        sys.exit(1)

    if install_requirements():
        run_fastapi()
