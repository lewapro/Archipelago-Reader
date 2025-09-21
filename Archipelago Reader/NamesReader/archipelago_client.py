import asyncio
import websockets
import json
import uuid
from config_manager import load_config
from message_processor import MessageProcessor
from data_package_manager import DataPackageManager

class ArchipelagoClient:
    def __init__(self, target_players, gui=None):
        self.target_players = target_players
        self.gui = gui
        self.data_package_manager = DataPackageManager()
        self.message_processor = MessageProcessor(target_players, self.data_package_manager, gui)
        self.websocket = None
        self.connected = False
    
    async def connect(self):
        """Establishes connection with Archipelago server"""
        try:
            # Load current config
            config = load_config()
            
            self.websocket = await websockets.connect(config["SERVER_URI"], max_size=config["MAX_MESSAGE_SIZE"])
            print(f"✅ Connected to Archipelago: {config['SERVER_URI']}")
            
            if self.gui:
                self.gui.update_connection_status("Connected", True)
            
            self.connected = True
            print(f"🔍 Filtering messages for players: {', '.join(self.target_players)}")
            
            # Authenticate with current settings
            if await self.authenticate(self.websocket, config):
                # Listen for server messages
                await self.listen(self.websocket)
                
        except Exception as e:
            error_msg = f"❌ Connection error: {e}"
            print(error_msg)
            if self.gui:
                self.gui.update_connection_status("Connection Failed", False)
    
    async def close(self):
        """Closes connection with server"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            print("✅ Connection closed")
    
    async def authenticate(self, websocket, config):
        """Authenticates with server using current settings"""
        connect_message = [
            {
                "cmd": "Connect",
                "password": config["PASSWORD"],
                "game": config["GAME"],
                "name": config["PLAYER_NAME"],
                "version": {
                    "major": 0,
                    "minor": 6,
                    "build": 3,
                    "class": "Version"
                },
                "tags": ["AP"],
                "items_handling": 7,
                "uuid": str(uuid.uuid4())
            }
        ]
        
        await websocket.send(json.dumps(connect_message))
        print("✅ Connection message sent")
        return True
    
    async def listen(self, websocket):
        """Listens for server messages"""
        data_package_requested = False
        
        try:
            async for message in websocket:
                try:
                    messages = json.loads(message)
                    
                    if not isinstance(messages, list):
                        messages = [messages]
                    
                    for msg in messages:
                        # Process message
                        request_data_package, close_connection = await self.message_processor.process_message(msg, websocket)
                        
                        # If connection needs to be closed
                        if close_connection:
                            await self.close()
                            return
                        
                        # If data package needs to be requested
                        if request_data_package and not data_package_requested:
                            data_package_requested = True
                            # Request full data package
                            await self.data_package_manager.request_data_package(websocket)
                            
                except json.JSONDecodeError:
                    # Check if message contains target players
                    if any(player in message for player in self.target_players) and \
                       any(keyword in message for keyword in ["sent", "received", "found"]):
                        print(f"📢 {message}")
                except Exception as e:
                    error_msg = f"❌ Message processing error: {e}"
                    print(error_msg)
                    print(f"Received message: {message}")
        except websockets.exceptions.ConnectionClosed:
            print("❌ Connection closed by server")
            if self.gui:
                self.gui.update_connection_status("Disconnected", False)