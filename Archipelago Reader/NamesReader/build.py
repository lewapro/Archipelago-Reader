import PyInstaller.__main__
import os

# Define paths to your files
files = [
    "main.py",
    "archipelago_client.py",
    "archipelago_gui.py",
    "config.py",
    "config_manager.py",
    "data_package_manager.py",
    "message_processor.py"
]

# Form arguments for PyInstaller
args = [
    "--name=ArchipelagoReader",
    "--onefile",
    "--windowed",
    "--add-data=config.py;.",  # Include config.py as data
    "--hidden-import=websockets",
    "--hidden-import=tkinter",
    "--hidden-import=asyncio",
    "--hidden-import=json",
    "--hidden-import=uuid",
    "--hidden-import=queue",
    "--hidden-import=threading",
    "--clean"
]

# Add main files
for file in files:
    if os.path.exists(file):
        args.append(file)
    else:
        print(f"⚠️ File {file} not found!")

# Start build
PyInstaller.__main__.run(args)