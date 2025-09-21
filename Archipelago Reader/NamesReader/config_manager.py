import os
import sys
import ast

# Global variable for runtime configuration
runtime_config = None

def get_default_config():
    """Returns default configuration"""
    return {
        "SERVER_URI": "ws://localhost:38281",
        "PLAYER_NAME": "lewapro",
        "PASSWORD": "",
        "GAME": "Manual_TeamFortress2_GP",
        "TARGET_PLAYERS": [],
        "MAX_MESSAGE_SIZE": 10 * 1024 * 1024,
        "MAX_MESSAGES": 1000,
        "FONT_SIZE": 12,
        "FONT_FAMILY": "TkDefaultFont",
        "BG_COLOR": "#0D141C",
        "TEXT_COLOR": "#9CCAFF",
        "WIDGET_BG_COLOR": "#242B33"
    }

def get_config_path():
    """Returns path to configuration file"""
    if getattr(sys, 'frozen', False):
        # If application is running as EXE
        return os.path.join(os.path.dirname(sys.executable), "config.py")
    else:
        # If application is running from source code
        return os.path.join(os.path.dirname(__file__), "config.py")

def load_config():
    """Loads configuration from file"""
    global runtime_config
    
    config_path = get_config_path()
    default_config = get_default_config()
    
    if not os.path.exists(config_path):
        # Create file with default settings if it doesn't exist
        default_config_str = '''# Application settings
SERVER_URI = "wss://localhost:38281"
PLAYER_NAME = "lewapro"
PASSWORD = ""
GAME = "Manual_TeamFortress2_GP"
TARGET_PLAYERS = []  # Empty list will show all messages
MAX_MESSAGE_SIZE = 10485760  # 10 MB
MAX_MESSAGES = 1000
FONT_SIZE = 12
FONT_FAMILY = "TkDefaultFont"
BG_COLOR = "#0D141C"
TEXT_COLOR = "#9CCAFF"
WIDGET_BG_COLOR = "#242B33"
'''
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(default_config_str)
    
    # Read and execute code from config.py
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse config.py content
    parsed = ast.parse(content)
    
    # Extract variable values
    config = default_config.copy()
    for node in parsed.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id
                    try:
                        # Try to get variable value
                        config[var_name] = ast.literal_eval(node.value)
                    except:
                        # If unable to evaluate, save as string
                        config[var_name] = ast.get_source_segment(content, node.value)
    
    # Update runtime config
    runtime_config = config
    
    return config

def update_runtime_config(new_config):
    """Updates runtime configuration without restart"""
    global runtime_config
    runtime_config = new_config

def save_config(new_config):
    """Saves configuration to file"""
    config_path = get_config_path()
    
    # Read current config
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update values in file
    for key, value in new_config.items():
        if isinstance(value, str) and not (value.startswith('[') or value.startswith('"') or value.startswith("'")):
            value_str = f'"{value}"'
        elif isinstance(value, list):
            value_str = str(value)
        else:
            value_str = str(value)
        
        # Find and replace variable value
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{key} ="):
                lines[i] = f"{key} = {value_str}"
                break
        
        content = '\n'.join(lines)
    
    # Write updated config
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Update runtime config
    update_runtime_config(new_config)