import re
from data_package_manager import DataPackageManager

class MessageProcessor:
    def __init__(self, target_players, data_package_manager, gui=None):
        self.target_players = target_players
        self.data_package_manager = data_package_manager
        self.gui = gui
        self.players = {}
        self.slot_games = {}
        self.player_slots = {}  # Player name to slot mapping
    
    def update_players(self, players_data):
        """Updates player information"""
        for player in players_data:
            slot = player.get("slot")
            name = player.get("name")
            self.players[slot] = name
            self.player_slots[name] = slot
        players_info = f"Players: {self.players}"
        print(players_info)
    
    def update_slot_games(self, slot_info):
        """Updates game information for each slot"""
        for slot_str, info in slot_info.items():
            slot = int(slot_str)
            self.slot_games[slot] = info.get("game")
        games_info = f"Games by slots: {self.slot_games}"
        print(games_info)
    
    async def process_message(self, msg, websocket):
        """Processes incoming message"""
        cmd = msg.get("cmd")
        
        if cmd == "Connected":
            connected_msg = "✅ Successfully authenticated with Archipelago"
            print(connected_msg)
            self.update_players(msg.get("players", []))
            self.update_slot_games(msg.get("slot_info", {}))
            return True, False
        
        elif cmd == "DataPackage":
            data = msg.get("data", {})
            data_package_msg = "✅ Received data package via WebSocket"
            print(data_package_msg)
            
            keys_info = f"Keys in data package: {list(data.keys())}"
            print(keys_info)
            
            self.data_package_manager.process_data_package(data)
            return False, False
        
        elif cmd == "PrintJSON":
            await self.process_print_json(msg)
            return False, False
            
        elif cmd == "ConnectionRefused":
            errors = msg.get("errors", [])
            error_msg = f"❌ Server refused connection: {errors}"
            print(error_msg)
            if self.gui:
                self.gui.update_connection_status("Connection Refused", False)
            return False, True
        
        return False, False
    
    async def process_print_json(self, msg):
        """Processes PrintJSON messages"""
        try:
            data = msg.get("data", [])
            message_parts = []
            sender_slot = None
            receiver_slot = None
            message_type = None
            
            # First pass: determine message type and sender/receiver slots
            for i, item in enumerate(data):
                if item.get("type") == "player_id":
                    text = item.get("text", "")
                    if text.isdigit():
                        if sender_slot is None:
                            sender_slot = int(text)
                        else:
                            receiver_slot = int(text)
                elif item.get("type") == "text":
                    text = item.get("text", "").lower()
                    if "sent" in text:
                        message_type = "sent"
                    elif "received" in text:
                        message_type = "received"
                    elif "found" in text:
                        message_type = "found"
            
            # For "found" messages set receiver same as sender
            if message_type == "found" and receiver_slot is None:
                receiver_slot = sender_slot
            
            # Second pass: process message elements
            players_in_message = set()  # Set to store players mentioned in message
            
            for item in data:
                if item.get("type") == "text":
                    message_parts.append(item.get("text", ""))
                elif item.get("type") == "player_id":
                    text = item.get("text", "")
                    if text.isdigit():
                        player_slot = int(text)
                        player_name = self.players.get(player_slot, f"Player {player_slot}")
                        message_parts.append(player_name)
                        
                        # Add player to mentioned players set
                        players_in_message.add(player_name)
                    else:
                        message_parts.append(text)
                elif item.get("type") == "item_id":
                    text = item.get("text", "")
                    if text.isdigit():
                        item_id = int(text)
                        
                        # Determine game for item based on message type
                        if message_type == "sent":
                            # For sent items use sender's game
                            game_name = self.slot_games.get(sender_slot, "Unknown") if sender_slot else "Unknown"
                        elif message_type == "received":
                            # For received items use sender's game
                            game_name = self.slot_games.get(sender_slot, "Unknown") if sender_slot else "Unknown"
                        elif message_type == "found":
                            # For found items use sender's game
                            game_name = self.slot_games.get(sender_slot, "Unknown") if sender_slot else "Unknown"
                        else:
                            # Default to sender's game
                            game_name = self.slot_games.get(sender_slot, "Unknown") if sender_slot else "Unknown"
                        
                        item_name = self.data_package_manager.resolve_item_name(game_name, item_id)
                        
                        # If not found in specific game, try any game
                        if item_name == f"Item {item_id}":
                            item_name = self.data_package_manager.resolve_item_name_any_game(item_id)
                        
                        message_parts.append(item_name)
                    else:
                        message_parts.append(text)
                elif item.get("type") == "location_id":
                    text = item.get("text", "")
                    if text.isdigit():
                        location_id = int(text)
                        # For locations use sender's game
                        game_name = self.slot_games.get(sender_slot, "Unknown") if sender_slot else "Unknown"
                        location_name = self.data_package_manager.resolve_location_name(game_name, location_id)
                        if location_name == f"Location {location_id}":
                            location_name = self.data_package_manager.resolve_location_name_any_game(location_id)
                        message_parts.append(location_name)
                    else:
                        message_parts.append(text)
                else:
                    message_parts.append(item.get("text", ""))
            
            message_text = "".join(message_parts)
            
            # Determine if message is sent or received
            is_sent_message = "sent" in message_text.lower()
            is_received_message = "received" in message_text.lower()
            is_found_message = "found" in message_text.lower()
            
            # Check if message contains target players or if no target players specified
            if not self.target_players:
                # Show all messages if no target players specified
                target_players_found = True
            else:
                target_players_found = any(player in players_in_message for player in self.target_players)
            
            # Determine message type for GUI
            message_types = []
            
            if target_players_found and (is_sent_message or is_received_message or is_found_message):
                print(f"📢 {message_text}")
                
                # Determine which target player is sender and which is receiver
                sender_name = None
                receiver_name = None
                
                if sender_slot is not None:
                    sender_name = self.players.get(sender_slot)
                
                if receiver_slot is not None:
                    receiver_name = self.players.get(receiver_slot)
                
                # Determine message type based on target players' roles
                if is_sent_message:
                    if sender_name in self.target_players:
                        message_types.append("outgoing")
                    if receiver_name in self.target_players and receiver_name is not None:
                        message_types.append("incoming")
                    # If sender and receiver are the same player
                    if sender_name == receiver_name and sender_name in self.target_players:
                        message_types.append("incoming")
                        message_types.append("outgoing")
                
                elif is_received_message:
                    if sender_name in self.target_players:
                        message_types.append("incoming")
                    if receiver_name in self.target_players and receiver_name is not None:
                        message_types.append("outgoing")
                
                elif is_found_message:
                    # For found messages always add both types
                    if sender_name in self.target_players:
                        message_types.append("incoming")
                        message_types.append("outgoing")
                
                # Remove duplicates
                message_types = list(set(message_types))
                
                # If no target players specified, show in both sections
                if not self.target_players:
                    message_types = ["incoming", "outgoing"]
                
                # Send message to GUI for each determined type
                for message_type_gui in message_types:
                    if self.gui:
                        self.gui.add_message(f"📢 {message_text}", message_type_gui)
                    
        except Exception as e:
            error_msg = f"❌ PrintJSON processing error: {e}"
            print(error_msg)