import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import asyncio
from config_manager import load_config, save_config

class ArchipelagoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Archipelago Reader")
        self.root.geometry("800x600")
        self.root.minsize(400, 300)
        
        # Queue for messages from other threads
        self.message_queue = queue.Queue()
        self.client = None
        self.thread = None
        self.loop = None
        self.connected = False
        
        self.setup_ui()
        self.start_queue_processing()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Connection frame
        connection_frame = ttk.Frame(main_frame)
        connection_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Connect button
        self.connect_btn = ttk.Button(connection_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(connection_frame, text="Disconnected")
        self.status_label.pack(side=tk.LEFT)
        
        # Settings button
        settings_btn = ttk.Button(connection_frame, text="⚙️", width=3, command=self.open_settings)
        settings_btn.pack(side=tk.RIGHT)
        
        # PanedWindow for resizable top/bottom sections
        paned_window = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        paned_window.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Incoming messages frame
        incoming_frame = ttk.LabelFrame(paned_window, text="Received", padding="5")
        paned_window.add(incoming_frame, weight=1)
        
        # Outgoing messages frame
        outgoing_frame = ttk.LabelFrame(paned_window, text="Sent", padding="5")
        paned_window.add(outgoing_frame, weight=1)
        
        # Configure grid weights for frames
        incoming_frame.columnconfigure(0, weight=1)
        incoming_frame.rowconfigure(0, weight=1)
        outgoing_frame.columnconfigure(0, weight=1)
        outgoing_frame.rowconfigure(0, weight=1)
        
        # Text areas with scrollbars
        self.incoming_text = scrolledtext.ScrolledText(incoming_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.incoming_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.outgoing_text = scrolledtext.ScrolledText(outgoing_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.outgoing_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def toggle_connection(self):
        if not self.connected:
            self.connect()
        else:
            self.disconnect()
    
    def connect(self):
        """Establishes connection with server"""
        try:
            from archipelago_client import ArchipelagoClient
            from main import run_asyncio_loop
            
            # Update settings from config
            config = load_config()
            
            self.client = ArchipelagoClient(config["TARGET_PLAYERS"], self)
            self.loop = asyncio.new_event_loop()
            self.thread = threading.Thread(target=run_asyncio_loop, args=(self.client, self.loop), daemon=True)
            self.thread.start()
            
            self.connect_btn.config(text="Connecting...", state=tk.DISABLED)
            self.status_label.config(text="Connecting...")
            
        except Exception as e:
            error_msg = f"❌ Connection error: {e}"
            print(error_msg)
            self.status_label.config(text="Connection Failed")
            self.connect_btn.config(text="Connect", state=tk.NORMAL)
    
    def disconnect(self):
        """Disconnects from server"""
        if self.client and self.loop:
            # Stop client
            asyncio.run_coroutine_threadsafe(self.client.close(), self.loop)
            
        self.connected = False
        self.connect_btn.config(text="Connect")
        self.status_label.config(text="Disconnected")
    
    def update_connection_status(self, status, success=True):
        """Updates connection status"""
        self.connected = success
        if success:
            self.connect_btn.config(text="Disconnect", state=tk.NORMAL)
            self.status_label.config(text="Connected")
        else:
            self.connect_btn.config(text="Connect", state=tk.NORMAL)
            self.status_label.config(text=status)
    
    def open_settings(self):
        """Opens settings window"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x400")
        settings_window.resizable(False, False)
        settings_window.grab_set()  # Modal window
        
        # Main frame
        main_frame = ttk.Frame(settings_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Load current config
        config = load_config()
        
        # Server URI
        ttk.Label(main_frame, text="Server URI:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        server_uri_var = tk.StringVar(value=config["SERVER_URI"])
        server_uri_entry = ttk.Entry(main_frame, textvariable=server_uri_var, width=50)
        server_uri_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5), padx=(5, 0))
        
        # Player name
        ttk.Label(main_frame, text="Player name:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        player_name_var = tk.StringVar(value=config["PLAYER_NAME"])
        player_name_entry = ttk.Entry(main_frame, textvariable=player_name_var, width=50)
        player_name_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 5), padx=(5, 0))
        
        # Password
        ttk.Label(main_frame, text="Password:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        password_var = tk.StringVar(value=config["PASSWORD"])
        password_entry = ttk.Entry(main_frame, textvariable=password_var, width=50, show="*")
        password_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(0, 5), padx=(5, 0))
        
        # Game
        ttk.Label(main_frame, text="Game:").grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        game_var = tk.StringVar(value=config["GAME"])
        game_entry = ttk.Entry(main_frame, textvariable=game_var, width=50)
        game_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=(0, 5), padx=(5, 0))
        
        # Target players
        ttk.Label(main_frame, text="Target players (comma separated):").grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        target_players_var = tk.StringVar(value=", ".join(config["TARGET_PLAYERS"]))
        target_players_entry = ttk.Entry(main_frame, textvariable=target_players_var, width=50)
        target_players_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=(0, 5), padx=(5, 0))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(20, 0))
        
        # Save button
        save_btn = ttk.Button(button_frame, text="Save", 
                             command=lambda: self.save_settings(
                                 server_uri_var.get(),
                                 player_name_var.get(),
                                 password_var.get(),
                                 game_var.get(),
                                 target_players_var.get(),
                                 settings_window
                             ))
        save_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Cancel button
        cancel_btn = ttk.Button(button_frame, text="Cancel", 
                               command=settings_window.destroy)
        cancel_btn.pack(side=tk.RIGHT)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
    
    def save_settings(self, server_uri, player_name, password, game, target_players, settings_window):
        """Saves settings to config.py"""
        try:
            # Validate target players
            target_players_list = [p.strip() for p in target_players.split(",") if p.strip()]
            if not target_players_list:
                raise ValueError("At least one target player must be specified")
            
            # Create new config dictionary
            new_config = {
                "SERVER_URI": server_uri,
                "PLAYER_NAME": player_name,
                "PASSWORD": password,
                "GAME": game,
                "TARGET_PLAYERS": target_players_list,
                "MAX_MESSAGE_SIZE": 10 * 1024 * 1024  # 10 MB
            }
            
            # Save using config_manager
            save_config(new_config)
            
            messagebox.showinfo("Success", "Settings saved successfully!")
            settings_window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def add_message(self, message, message_type):
        """Adds message to appropriate text area"""
        # Put message in queue for processing in main thread
        self.message_queue.put((message, message_type))
    
    def process_queue(self):
        """Processes messages from queue"""
        try:
            while True:
                message, message_type = self.message_queue.get_nowait()
                
                # Filter only messages starting with 📢
                if message.startswith("📢"):
                    if message_type == "incoming":
                        text_widget = self.incoming_text
                    elif message_type == "outgoing":
                        text_widget = self.outgoing_text
                    else:
                        continue  # Skip other message types
                    
                    text_widget.configure(state=tk.NORMAL)
                    text_widget.insert(tk.END, message + "\n")
                    text_widget.see(tk.END)  # Auto-scroll to bottom
                    text_widget.configure(state=tk.DISABLED)
                
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_queue)
    
    def start_queue_processing(self):
        """Starts message queue processing"""
        self.root.after(100, self.process_queue)