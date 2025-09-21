import asyncio
import sys
import threading
import tkinter as tk
from config_manager import load_config
from archipelago_client import ArchipelagoClient
from archipelago_gui import ArchipelagoGUI

def run_asyncio_loop(client, loop):
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(client.connect())
    except Exception as e:
        print(f"Error in asyncio loop: {e}")
    finally:
        loop.close()

def main():
    # Create GUI
    root = tk.Tk()
    gui = ArchipelagoGUI(root)
    
    # Start GUI main loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()