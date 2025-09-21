import json

class DataPackageManager:
    def __init__(self):
        self.game_data_packages = {}
        self.game_item_mappings = {}
        self.game_location_mappings = {}
        self.loaded = False
    
    async def request_data_package(self, websocket, games=None):
        """Requests data package via WebSocket connection"""
        try:
            if games:
                get_data_package_msg = [{"cmd": "GetDataPackage", "games": games}]
            else:
                get_data_package_msg = [{"cmd": "GetDataPackage"}]
                
            await websocket.send(json.dumps(get_data_package_msg))
            return True
        except Exception as e:
            print(f"❌ Error sending data package request: {e}")
            return False
    
    def process_data_package(self, data):
        """Processes received data package"""
        self.game_data_packages.update(data)
        
        # Process all games in data package
        games_data = data.get('games', {})
        for game_name, game_data in games_data.items():
            self._load_mappings(game_name, game_data)
        
        # Also process games at top level (if any)
        for game_name in data:
            if game_name != 'games' and game_name not in games_data:
                game_data = data[game_name]
                self._load_mappings(game_name, game_data)
        
        print(f"✅ Loaded mappings for games: {list(self.game_item_mappings.keys())}")
        return True
    
    def _load_mappings(self, game_name, game_data):
        """Loads mappings for specific game"""
        # Items
        item_name_to_id = game_data.get("item_name_to_id", {})
        self.game_item_mappings[game_name] = {v: k for k, v in item_name_to_id.items()}
        
        # Locations
        location_name_to_id = game_data.get("location_name_to_id", {})
        self.game_location_mappings[game_name] = {v: k for k, v in location_name_to_id.items()}
        
        self.loaded = True
    
    def resolve_item_name(self, game_name, item_id):
        """Gets item name by ID for specific game"""
        if game_name in self.game_item_mappings:
            return self.game_item_mappings[game_name].get(item_id, f"Item {item_id}")
        return f"Item {item_id}"
    
    def resolve_location_name(self, game_name, location_id):
        """Gets location name by ID for specific game"""
        if game_name in self.game_location_mappings:
            return self.game_location_mappings[game_name].get(location_id, f"Location {location_id}")
        return f"Location {location_id}"
    
    def resolve_item_name_any_game(self, item_id):
        """Tries to find item in any game"""
        for game_name, mappings in self.game_item_mappings.items():
            if item_id in mappings:
                return f"{mappings[item_id]} ({game_name})"
        return f"Item {item_id}"
    
    def resolve_location_name_any_game(self, location_id):
        """Tries to find location in any game"""
        for game_name, mappings in self.game_location_mappings.items():
            if location_id in mappings:
                return f"{mappings[location_id]} ({game_name})"
        return f"Location {location_id}"