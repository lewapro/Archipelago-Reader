import os
import sys
import ast

def get_config_path():
    """Возвращает путь к файлу конфигурации"""
    if getattr(sys, 'frozen', False):
        # Если приложение запущено как EXE
        return os.path.join(os.path.dirname(sys.executable), "config.py")
    else:
        # Если приложение запущено из исходного кода
        return os.path.join(os.path.dirname(__file__), "config.py")

def load_config():
    """Загружает конфигурацию из файла"""
    config_path = get_config_path()
    
    if not os.path.exists(config_path):
        # Создаем файл с настройками по умолчанию, если он не существует
        default_config = '''# Application settings
SERVER_URI = "ws://localhost:38281"
PLAYER_NAME = "lewapro"
PASSWORD = ""
GAME = "Manual_TeamFortress2_GP"
TARGET_PLAYERS = ['lewapro', 'man']
MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10 MB
'''
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(default_config)
    
    # Читаем и выполняем код из config.py
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Парсим содержимое config.py
    parsed = ast.parse(content)
    
    # Извлекаем значения переменных
    config = {}
    for node in parsed.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id
                    try:
                        # Пытаемся получить значение переменной
                        config[var_name] = ast.literal_eval(node.value)
                    except:
                        # Если не удается вычислить, сохраняем как строку
                        config[var_name] = ast.get_source_segment(content, node.value)
    
    return config

def save_config(new_config):
    """Сохраняет конфигурацию в файл"""
    config_path = get_config_path()
    
    # Читаем текущий конфиг
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Обновляем значения в файле
    for key, value in new_config.items():
        if isinstance(value, str):
            value_str = f'"{value}"'
        elif isinstance(value, list):
            value_str = str(value)
        else:
            value_str = str(value)
        
        # Находим и заменяем значение переменной
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{key} ="):
                lines[i] = f"{key} = {value_str}"
                break
        
        content = '\n'.join(lines)
    
    # Записываем обновленный конфиг
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)