import tkinter as tk
from tkinter import scrolledtext, messagebox, Frame, Label, Button, Entry, PanedWindow
import threading
import queue
import asyncio
import time
import re
from config_manager import load_config, save_config, get_default_config

class ArchipelagoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Archipelago Reader")
        self.root.geometry("800x600")
        self.root.minsize(400, 300)
        
        # Load configuration
        config = load_config()
        
        # Color scheme from config
        self.bg_color = config["BG_COLOR"]  # Main background
        self.header_bg = config["WIDGET_BG_COLOR"]  # Header background
        self.text_color = config["TEXT_COLOR"]  # Text color
        self.widget_bg = config["WIDGET_BG_COLOR"]  # Widget background
        self.scrollbar_bg = "#2A3035"  # Scrollbar background
        self.entry_bg = config["WIDGET_BG_COLOR"]  # Entry background
        self.font_size = config["FONT_SIZE"]
        self.font_family = config["FONT_FAMILY"]
        self.max_messages = config["MAX_MESSAGES"]
        
        # Apply colors to main window
        self.root.configure(bg=self.bg_color)
        
        # Queue for messages from other threads
        self.message_queue = queue.Queue()
        self.client = None
        self.thread = None
        self.loop = None
        self.connected = False
        
        # Message buffers and update control
        self.incoming_buffer = []
        self.outgoing_buffer = []
        self.last_update_time = 0
        self.update_interval = 0.1  # Update GUI every 100ms (10 times per second)
        
        self.setup_ui()
        self.start_queue_processing()
    
    def setup_ui(self):
        # Main frame
        main_frame = Frame(self.root, bg=self.bg_color, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Connection frame
        connection_frame = Frame(main_frame, bg=self.bg_color)
        connection_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Connect button
        self.connect_btn = Button(
            connection_frame, 
            text="Connect", 
            command=self.toggle_connection,
            bg=self.widget_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=5
        )
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Status label
        self.status_label = Label(
            connection_frame, 
            text="Disconnected",
            bg=self.bg_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size)
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Settings button (changed to text)
        settings_btn = Button(
            connection_frame, 
            text="Settings", 
            command=self.open_settings,
            bg=self.widget_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=5
        )
        settings_btn.pack(side=tk.RIGHT)
        
        # PanedWindow for resizable top/bottom sections
        paned_window = PanedWindow(
            main_frame, 
            orient=tk.VERTICAL, 
            bg=self.header_bg,
            bd=0,
            sashwidth=4,
            sashrelief=tk.FLAT
        )
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Incoming messages frame
        incoming_frame = Frame(paned_window, bg=self.bg_color, bd=1, relief=tk.SOLID)
        paned_window.add(incoming_frame, height=300)  # Set initial height
        
        # Incoming label
        incoming_label = Label(
            incoming_frame, 
            text="Received",
            bg=self.header_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            pady=5
        )
        incoming_label.pack(fill=tk.X)
        
        # Outgoing messages frame
        outgoing_frame = Frame(paned_window, bg=self.bg_color, bd=1, relief=tk.SOLID)
        paned_window.add(outgoing_frame, height=300)  # Set initial height
        
        # Outgoing label
        outgoing_label = Label(
            outgoing_frame, 
            text="Sent",
            bg=self.header_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            pady=5
        )
        outgoing_label.pack(fill=tk.X)
        
        # Incoming text area (without scrollbar)
        self.incoming_text = tk.Text(
            incoming_frame, 
            wrap=tk.WORD, 
            state=tk.DISABLED,
            bg=self.bg_color,
            fg=self.text_color,
            insertbackground=self.text_color,
            selectbackground="#3D4F5D",
            font=(self.font_family, self.font_size),
            relief=tk.FLAT,
            highlightthickness=0,
            bd=0
        )
        self.incoming_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Outgoing text area (without scrollbar)
        self.outgoing_text = tk.Text(
            outgoing_frame, 
            wrap=tk.WORD, 
            state=tk.DISABLED,
            bg=self.bg_color,
            fg=self.text_color,
            insertbackground=self.text_color,
            selectbackground="#3D4F5D",
            font=(self.font_family, self.font_size),
            relief=tk.FLAT,
            highlightthickness=0,
            bd=0
        )
        self.outgoing_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Set initial sash position to the middle
        paned_window.paneconfig(incoming_frame, height=300)
        paned_window.paneconfig(outgoing_frame, height=300)
    
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
        self.connect_btn.config(text="Connect", state=tk.NORMAL)
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
        settings_window.geometry("540x450")
        settings_window.resizable(True, True)
        settings_window.grab_set()  # Modal window
        
        # Apply color scheme to settings window
        settings_window.configure(bg=self.bg_color)
        
        # Main frame with scrollbar
        main_frame = Frame(settings_window, bg=self.bg_color, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a canvas without scrollbar
        canvas = tk.Canvas(main_frame, bg=self.bg_color, highlightthickness=0)
        scrollable_frame = Frame(canvas, bg=self.bg_color)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Pack canvas to fill the entire space
        canvas.pack(side="left", fill="both", expand=True)

        # Remove scrollbar creation and packing completely
        # scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        # scrollbar.pack(side="right", fill="y")

        # Keep mouse wheel scrolling functionality
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Load current config
        config = load_config()
        default_config = get_default_config()
        
        # Server URI setting with new layout
        label_reset_frame = Frame(scrollable_frame, bg=self.bg_color)
        label_reset_frame.grid(row=0, column=0, sticky='w', pady=(0, 5))

        reset_btn = Button(
            label_reset_frame,
            text="↺",
            command=lambda: server_uri_var.set(default_config["SERVER_URI"]),
            bg=self.widget_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            relief=tk.FLAT,
            bd=0,
            padx=3,
            pady=1,
            width=2
        )
        reset_btn.pack(side=tk.LEFT, padx=(0, 5))

        Label(
            label_reset_frame, 
            text="Server URI (ws:// or wss:///):",
            bg=self.bg_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size)
        ).pack(side=tk.LEFT)

        server_uri_var = tk.StringVar(value=config["SERVER_URI"])
        server_uri_entry = Entry(
            scrollable_frame, 
            textvariable=server_uri_var, 
            bg=self.entry_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            insertbackground=self.text_color,
            relief=tk.FLAT,
            bd=1
        )
        server_uri_entry.grid(row=0, column=1, sticky='ew', pady=(0, 5), padx=(5, 0))

        # Player name setting with new layout
        label_reset_frame = Frame(scrollable_frame, bg=self.bg_color)
        label_reset_frame.grid(row=1, column=0, sticky='w', pady=(0, 5))

        reset_btn = Button(
            label_reset_frame,
            text="↺",
            command=lambda: player_name_var.set(default_config["PLAYER_NAME"]),
            bg=self.widget_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            relief=tk.FLAT,
            bd=0,
            padx=3,
            pady=1,
            width=2
        )
        reset_btn.pack(side=tk.LEFT, padx=(0, 5))

        Label(
            label_reset_frame, 
            text="Player name:",
            bg=self.bg_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size)
        ).pack(side=tk.LEFT)

        player_name_var = tk.StringVar(value=config["PLAYER_NAME"])
        player_name_entry = Entry(
            scrollable_frame, 
            textvariable=player_name_var, 
            bg=self.entry_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            insertbackground=self.text_color,
            relief=tk.FLAT,
            bd=1
        )
        player_name_entry.grid(row=1, column=1, sticky='ew', pady=(0, 5), padx=(5, 0))

        # Password setting with new layout
        label_reset_frame = Frame(scrollable_frame, bg=self.bg_color)
        label_reset_frame.grid(row=2, column=0, sticky='w', pady=(0, 5))

        reset_btn = Button(
            label_reset_frame,
            text="↺",
            command=lambda: password_var.set(default_config["PASSWORD"]),
            bg=self.widget_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            relief=tk.FLAT,
            bd=0,
            padx=3,
            pady=1,
            width=2
        )
        reset_btn.pack(side=tk.LEFT, padx=(0, 5))

        Label(
            label_reset_frame, 
            text="Password:",
            bg=self.bg_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size)
        ).pack(side=tk.LEFT)

        password_var = tk.StringVar(value=config["PASSWORD"])
        password_entry = Entry(
            scrollable_frame, 
            textvariable=password_var, 
            show="*",
            bg=self.entry_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            insertbackground=self.text_color,
            relief=tk.FLAT,
            bd=1
        )
        password_entry.grid(row=2, column=1, sticky='ew', pady=(0, 5), padx=(5, 0))

        # Game setting with new layout
        label_reset_frame = Frame(scrollable_frame, bg=self.bg_color)
        label_reset_frame.grid(row=3, column=0, sticky='w', pady=(0, 5))

        reset_btn = Button(
            label_reset_frame,
            text="↺",
            command=lambda: game_var.set(default_config["GAME"]),
            bg=self.widget_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            relief=tk.FLAT,
            bd=0,
            padx=3,
            pady=1,
            width=2
        )
        reset_btn.pack(side=tk.LEFT, padx=(0, 5))

        Label(
            label_reset_frame, 
            text="Game:",
            bg=self.bg_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size)
        ).pack(side=tk.LEFT)

        game_var = tk.StringVar(value=config["GAME"])
        game_entry = Entry(
            scrollable_frame, 
            textvariable=game_var, 
            bg=self.entry_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            insertbackground=self.text_color,
            relief=tk.FLAT,
            bd=1
        )
        game_entry.grid(row=3, column=1, sticky='ew', pady=(0, 5), padx=(5, 0))

        # Target players setting with new layout
        label_reset_frame = Frame(scrollable_frame, bg=self.bg_color)
        label_reset_frame.grid(row=4, column=0, sticky='w', pady=(0, 5))

        reset_btn = Button(
            label_reset_frame,
            text="↺",
            command=lambda: target_players_var.set(", ".join(default_config["TARGET_PLAYERS"])),
            bg=self.widget_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            relief=tk.FLAT,
            bd=0,
            padx=3,
            pady=1,
            width=2
        )
        reset_btn.pack(side=tk.LEFT, padx=(0, 5))

        Label(
            label_reset_frame, 
            text="Target players (comma separated):",
            bg=self.bg_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size)
        ).pack(side=tk.LEFT)

        target_players_var = tk.StringVar(value=", ".join(config["TARGET_PLAYERS"]))
        target_players_entry = Entry(
            scrollable_frame, 
            textvariable=target_players_var, 
            bg=self.entry_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            insertbackground=self.text_color,
            relief=tk.FLAT,
            bd=1
        )
        target_players_entry.grid(row=4, column=1, sticky='ew', pady=(0, 5), padx=(5, 0))

        # Max messages setting with new layout
        label_reset_frame = Frame(scrollable_frame, bg=self.bg_color)
        label_reset_frame.grid(row=5, column=0, sticky='w', pady=(5, 5))

        reset_btn = Button(
            label_reset_frame,
            text="↺",
            command=lambda: max_messages_var.set(str(default_config["MAX_MESSAGES"])),
            bg=self.widget_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            relief=tk.FLAT,
            bd=0,
            padx=3,
            pady=1,
            width=2
        )
        reset_btn.pack(side=tk.LEFT, padx=(0, 5))

        Label(
            label_reset_frame, 
            text="Max messages:",
            bg=self.bg_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size)
        ).pack(side=tk.LEFT)

        max_messages_var = tk.StringVar(value=str(config["MAX_MESSAGES"]))
        max_messages_entry = Entry(
            scrollable_frame, 
            textvariable=max_messages_var, 
            bg=self.entry_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            insertbackground=self.text_color,
            relief=tk.FLAT,
            bd=1
        )
        max_messages_entry.grid(row=5, column=1, sticky='ew', pady=(5, 5), padx=(5, 0))

        # Font size setting with new layout
        label_reset_frame = Frame(scrollable_frame, bg=self.bg_color)
        label_reset_frame.grid(row=6, column=0, sticky='w', pady=(0, 5))

        reset_btn = Button(
            label_reset_frame,
            text="↺",
            command=lambda: font_size_var.set(str(default_config["FONT_SIZE"])),
            bg=self.widget_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            relief=tk.FLAT,
            bd=0,
            padx=3,
            pady=1,
            width=2
        )
        reset_btn.pack(side=tk.LEFT, padx=(0, 5))

        Label(
            label_reset_frame, 
            text="Font size (Restart required):",
            bg=self.bg_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size)
        ).pack(side=tk.LEFT)

        font_size_var = tk.StringVar(value=str(config["FONT_SIZE"]))
        font_size_entry = Entry(
            scrollable_frame, 
            textvariable=font_size_var, 
            bg=self.entry_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            insertbackground=self.text_color,
            relief=tk.FLAT,
            bd=1
        )
        font_size_entry.grid(row=6, column=1, sticky='ew', pady=(0, 5), padx=(5, 0))

        # Font family setting with new layout
        label_reset_frame = Frame(scrollable_frame, bg=self.bg_color)
        label_reset_frame.grid(row=7, column=0, sticky='w', pady=(0, 5))

        reset_btn = Button(
            label_reset_frame,
            text="↺",
            command=lambda: font_family_var.set(default_config["FONT_FAMILY"]),
            bg=self.widget_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            relief=tk.FLAT,
            bd=0,
            padx=3,
            pady=1,
            width=2
        )
        reset_btn.pack(side=tk.LEFT, padx=(0, 5))

        Label(
            label_reset_frame, 
            text="Font family (Restart required):",
            bg=self.bg_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size)
        ).pack(side=tk.LEFT)

        font_family_var = tk.StringVar(value=config["FONT_FAMILY"])
        font_family_entry = Entry(
            scrollable_frame, 
            textvariable=font_family_var, 
            bg=self.entry_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            insertbackground=self.text_color,
            relief=tk.FLAT,
            bd=1
        )
        font_family_entry.grid(row=7, column=1, sticky='ew', pady=(0, 5), padx=(5, 0))

        # Background color setting with new layout
        label_reset_frame = Frame(scrollable_frame, bg=self.bg_color)
        label_reset_frame.grid(row=8, column=0, sticky='w', pady=(0, 5))

        reset_btn = Button(
            label_reset_frame,
            text="↺",
            command=lambda: bg_color_var.set(default_config["BG_COLOR"]),
            bg=self.widget_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            relief=tk.FLAT,
            bd=0,
            padx=3,
            pady=1,
            width=2
        )
        reset_btn.pack(side=tk.LEFT, padx=(0, 5))

        Label(
            label_reset_frame, 
            text="Background color (Restart required):",
            bg=self.bg_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size)
        ).pack(side=tk.LEFT)

        bg_color_var = tk.StringVar(value=config["BG_COLOR"])
        bg_color_entry = Entry(
            scrollable_frame, 
            textvariable=bg_color_var, 
            bg=self.entry_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            insertbackground=self.text_color,
            relief=tk.FLAT,
            bd=1
        )
        bg_color_entry.grid(row=8, column=1, sticky='ew', pady=(0, 5), padx=(5, 0))

        # Text color setting with new layout
        label_reset_frame = Frame(scrollable_frame, bg=self.bg_color)
        label_reset_frame.grid(row=9, column=0, sticky='w', pady=(0, 5))

        reset_btn = Button(
            label_reset_frame,
            text="↺",
            command=lambda: text_color_var.set(default_config["TEXT_COLOR"]),
            bg=self.widget_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            relief=tk.FLAT,
            bd=0,
            padx=3,
            pady=1,
            width=2
        )
        reset_btn.pack(side=tk.LEFT, padx=(0, 5))

        Label(
            label_reset_frame, 
            text="Text color (Restart required):",
            bg=self.bg_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size)
        ).pack(side=tk.LEFT)

        text_color_var = tk.StringVar(value=config["TEXT_COLOR"])
        text_color_entry = Entry(
            scrollable_frame, 
            textvariable=text_color_var, 
            bg=self.entry_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            insertbackground=self.text_color,
            relief=tk.FLAT,
            bd=1
        )
        text_color_entry.grid(row=9, column=1, sticky='ew', pady=(0, 5), padx=(5, 0))

        # Widget background color setting with new layout
        label_reset_frame = Frame(scrollable_frame, bg=self.bg_color)
        label_reset_frame.grid(row=10, column=0, sticky='w', pady=(0, 5))

        reset_btn = Button(
            label_reset_frame,
            text="↺",
            command=lambda: widget_bg_color_var.set(default_config["WIDGET_BG_COLOR"]),
            bg=self.widget_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            relief=tk.FLAT,
            bd=0,
            padx=3,
            pady=1,
            width=2
        )
        reset_btn.pack(side=tk.LEFT, padx=(0, 5))

        Label(
            label_reset_frame, 
            text="Button color (Restart required):",
            bg=self.bg_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size)
        ).pack(side=tk.LEFT)

        widget_bg_color_var = tk.StringVar(value=config["WIDGET_BG_COLOR"])
        widget_bg_color_entry = Entry(
            scrollable_frame, 
            textvariable=widget_bg_color_var, 
            bg=self.entry_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            insertbackground=self.text_color,
            relief=tk.FLAT,
            bd=1
        )
        widget_bg_color_entry.grid(row=10, column=1, sticky='ew', pady=(0, 5), padx=(5, 0))

        # Button frame at the bottom
        button_frame = Frame(scrollable_frame, bg=self.bg_color)
        button_frame.grid(row=11, column=0, columnspan=2, pady=(20, 0))

        # Save button
        save_btn = Button(
            button_frame, 
            text="Save", 
            command=lambda: self.save_settings(
                server_uri_var.get(),
                player_name_var.get(),
                password_var.get(),
                game_var.get(),
                target_players_var.get(),
                max_messages_var.get(),
                font_size_var.get(),
                font_family_var.get(),
                bg_color_var.get(),
                text_color_var.get(),
                widget_bg_color_var.get(),
                settings_window
            ),
            bg=self.widget_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=5
        )
        save_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # Cancel button
        cancel_btn = Button(
            button_frame, 
            text="Cancel", 
            command=settings_window.destroy,
            bg=self.widget_bg,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=5
        )
        cancel_btn.pack(side=tk.RIGHT)

        # Configure column weights for proper expansion
        scrollable_frame.columnconfigure(1, weight=1)

        # Make the window scrollable with mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def save_settings(self, server_uri, player_name, password, game, target_players, max_messages, font_size, font_family, bg_color, text_color, widget_bg_color, settings_window):
        """Saves settings to config.py and applies them immediately"""
        try:
            # Validate required fields
            if not server_uri.strip():
                raise ValueError("Server URI cannot be empty")
            if not player_name.strip():
                raise ValueError("Player name cannot be empty")
            if not game.strip():
                raise ValueError("Game cannot be empty")
            
            # Process target players (can be empty)
            target_players_list = [p.strip() for p in target_players.split(",") if p.strip()]
            
            # Validate numeric values
            try:
                max_messages_int = int(max_messages)
                if max_messages_int <= 0:
                    raise ValueError("Max messages must be a positive integer")
            except ValueError:
                raise ValueError("Max messages must be a valid integer")
            
            try:
                font_size_int = int(font_size)
                if font_size_int <= 0:
                    raise ValueError("Font size must be a positive integer")
            except ValueError:
                raise ValueError("Font size must be a valid integer")
            
            # Validate color formats (simple check for # followed by 6 hex digits)
            color_regex = "^#[0-9A-Fa-f]{6}$"
            if not re.match(color_regex, bg_color):
                raise ValueError("Background color must be in #RRGGBB format")
            if not re.match(color_regex, text_color):
                raise ValueError("Text color must be in #RRGGBB format")
            if not re.match(color_regex, widget_bg_color):
                raise ValueError("Widget background color must be in #RRGGBB format")
            
            # Create new config dictionary
            new_config = {
                "SERVER_URI": server_uri,
                "PLAYER_NAME": player_name,
                "PASSWORD": password,
                "GAME": game,
                "TARGET_PLAYERS": target_players_list,
                "MAX_MESSAGE_SIZE": 10 * 1024 * 1024,  # 10 MB
                "MAX_MESSAGES": max_messages_int,
                "FONT_SIZE": font_size_int,
                "FONT_FAMILY": font_family,
                "BG_COLOR": bg_color,
                "TEXT_COLOR": text_color,
                "WIDGET_BG_COLOR": widget_bg_color
            }
            
            # Save using config_manager
            save_config(new_config)
            
            # Apply new settings immediately
            self.apply_new_settings(new_config)
            
            # Close settings window
            settings_window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def apply_new_settings(self, new_config):
        """Applies new settings to the GUI without restart"""
        # Update settings
        self.max_messages = new_config["MAX_MESSAGES"]
        self.font_size = new_config["FONT_SIZE"]
        self.font_family = new_config["FONT_FAMILY"]
        self.bg_color = new_config["BG_COLOR"]
        self.text_color = new_config["TEXT_COLOR"]
        self.widget_bg = new_config["WIDGET_BG_COLOR"]
        
        # Update main window
        self.root.configure(bg=self.bg_color)
        
        # Update connection frame
        for widget in self.root.winfo_children():
            if isinstance(widget, Frame):
                widget.configure(bg=self.bg_color)
                for child in widget.winfo_children():
                    if isinstance(child, (Label, Button)):
                        child.configure(
                            bg=self.widget_bg if isinstance(child, Button) else self.bg_color,
                            fg=self.text_color,
                            font=(self.font_family, self.font_size)
                        )
        
        # Update text widgets
        self.incoming_text.configure(
            bg=self.bg_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size)
        )
        
        self.outgoing_text.configure(
            bg=self.bg_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size)
        )
    
    def add_message(self, message, message_type):
        """Adds message to appropriate buffer"""
        # Filter only messages starting with 📢
        if message.startswith("📢"):
            if message_type == "incoming":
                self.incoming_buffer.append(message)
            elif message_type == "outgoing":
                self.outgoing_buffer.append(message)
    
    def update_text_widgets(self):
        """Updates text widgets with buffered messages at controlled rate"""
        current_time = time.time()
        
        # Only update if enough time has passed since last update
        if current_time - self.last_update_time >= self.update_interval:
            self.last_update_time = current_time
            
            # Process incoming messages
            if self.incoming_buffer:
                self.incoming_text.configure(state=tk.NORMAL)
                
                # Add all buffered incoming messages
                for msg in self.incoming_buffer:
                    self.incoming_text.insert(tk.END, msg + "\n")
                
                # Clear the buffer
                self.incoming_buffer.clear()
                
                # Limit message history
                lines = int(self.incoming_text.index('end-1c').split('.')[0])
                if lines > self.max_messages:
                    # Delete oldest messages to stay within limit
                    delete_count = lines - self.max_messages
                    self.incoming_text.delete(1.0, f"{delete_count + 1}.0")
                
                self.incoming_text.see(tk.END)  # Auto-scroll to bottom
                self.incoming_text.configure(state=tk.DISABLED)
            
            # Process outgoing messages
            if self.outgoing_buffer:
                self.outgoing_text.configure(state=tk.NORMAL)
                
                # Add all buffered outgoing messages
                for msg in self.outgoing_buffer:
                    self.outgoing_text.insert(tk.END, msg + "\n")
                
                # Clear the buffer
                self.outgoing_buffer.clear()
                
                # Limit message history
                lines = int(self.outgoing_text.index('end-1c').split('.')[0])
                if lines > self.max_messages:
                    # Delete oldest messages to stay within limit
                    delete_count = lines - self.max_messages
                    self.outgoing_text.delete(1.0, f"{delete_count + 1}.0")
                
                self.outgoing_text.see(tk.END)  # Auto-scroll to bottom
                self.outgoing_text.configure(state=tk.DISABLED)
        
        # Schedule next update
        self.root.after(int(self.update_interval * 1000), self.update_text_widgets)
    
    def start_queue_processing(self):
        """Starts message processing"""
        self.update_text_widgets()