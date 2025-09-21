import PyInstaller.__main__
import os

# Определите пути к вашим файлам
files = [
    "main.py",
    "archipelago_client.py",
    "archipelago_gui.py",
    "config.py",
    "data_package_manager.py",
    "message_processor.py"
]

# Формируем аргументы для PyInstaller
args = [
    "--name=ArchipelagoReader",
    "--onefile",
    "--windowed",
    "--add-data=config.py;.",  # Включаем config.py как данные
    "--hidden-import=websockets",
    "--hidden-import=tkinter",
    "--hidden-import=asyncio",
    "--hidden-import=json",
    "--hidden-import=uuid",
    "--hidden-import=queue",
    "--hidden-import=threading",
    "--clean"
]

# Добавляем основные файлы
for file in files:
    if os.path.exists(file):
        args.append(file)
    else:
        print(f"⚠️ Файл {file} не найден!")

# Запускаем сборку
PyInstaller.__main__.run(args)