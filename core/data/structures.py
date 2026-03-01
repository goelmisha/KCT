import re
import datetime
import json
from abc import ABC, abstractmethod
from enum import Enum
import requests

class AssetType(Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    LINK = "link"
    MODAL = "modal"

class AssetObject:
    def __init__(self, content, source_url, asset_type, source_name, metadata=None):
        self.content = content
        self.source_url = source_url
        self.asset_type = asset_type
        self.source_name = source_name
        self.metadata = metadata or {}
    def __repr__(self):
        return f"AssetObject(type={self.asset_type}, source={self.source_name})"

class DataSource(ABC):
    @abstractmethod
    def fetch_data(self, source_identifier):
        pass
    @abstractmethod
    def standardize_output(self, raw_data):
        pass
    def get_assets(self, source_identifier):
        raw_data = self.fetch_data(source_identifier)
        return self.standardize_output(raw_data)


import re
import datetime
import json
from abc import ABC, abstractmethod
from enum import Enum
import requests

class AssetType(Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    LINK = "link"
    MODAL = "modal"
    TEXT = "text" # Added this to match your standardize_output logic

class AssetObject:
    def __init__(self, content, source_url, asset_type, source_name, metadata=None):
        self.content = content
        self.source_url = source_url
        self.asset_type = asset_type
        self.source_name = source_name
        self.metadata = metadata or {}
        
    def __repr__(self):
        # Snipped content for cleaner console output
        display_content = (self.content[:50] + '...') if self.content and len(self.content) > 50 else self.content
        return f"AssetObject(type={self.asset_type.value}, source={self.source_name}, content='{display_content}')"

class DataSource(ABC):
    @abstractmethod
    def fetch_data(self, source_identifier):
        pass
    @abstractmethod
    def standardize_output(self, raw_data):
        pass
    def get_assets(self, source_identifier):
        raw_data = self.fetch_data(source_identifier)
        return self.standardize_output(raw_data)

class ArenaSource(DataSource):
    def fetch_data(self, channel_slug):
        # FIXED: Use v2 and f-string for the actual slug
        url = f"https://api.are.na/v3/channels/{channel_slug}/contents"
        params = {"per": 10, "direction": "desc"} # Limiting to 10 for the test
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            print(f"Response status: {response.status_code}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching from Are.na: {e}")
            return {"contents": []}

    def standardize_output(self, raw_data):
        assets = []
        
        # ERROR SPOTTER 1: Check the top-level key
        # Your JSON shows the list is under "data", not "contents"
        items = raw_data.get("data")
        
        if items is None:
            print("[ERROR] Key 'data' not found in API response. Keys present: ", list(raw_data.keys()))
            return []

        print(f"[INFO] Found {len(items)} items in 'data'. Starting extraction...")

        for index, block in enumerate(items):
            try:
                # ERROR SPOTTER 2: Check the type/class key
                # Your JSON uses "type", but some Are.na endpoints use "class"
                b_type = block.get("type") or block.get("class")
                b_id = block.get("id")

                if b_type == "Channel":
                    a_type = AssetType.LINK # Mapping a nested channel to a link
                    # In your JSON, the slug is used for the URL
                    content = f"https://www.are.na/channel/{block.get('slug')}"
                
                elif b_type == "Text":
                    a_type = AssetType.TEXT
                    content = block.get("content")
                
                elif b_type == "Link":
                    a_type = AssetType.LINK
                    # Checking common Are.na nesting for links
                    source_info = block.get("source", {})
                    content = source_info.get("url") or block.get("title")
                
                else:
                    print(f"      [SKIP] Index {index}: Unknown type '{b_type}'")
                    continue

                assets.append(AssetObject(
                    content=content,
                    source_url=f"https://www.are.na/block/{b_id}" if b_type != "Channel" else content,
                    asset_type=a_type,
                    source_name="Arena",
                    metadata={
                        "id": b_id, 
                        "raw_type": b_type,
                        "updated": block.get("updated_at")
                    }
                ))

            except Exception as e:
                print(f"      [BLOCK ERROR] Failed at index {index}: {str(e)}")
        
        return assets

# --- TEST BLOCK ---
if __name__ == "__main__":
    # Initialize the source
    arena = ArenaSource()
    
    # Use the slug you provided earlier
    test_slug = "timekeeping-timetraveling"
    
    print(f"--- Fetching assets from: {test_slug} ---")
    assets = arena.get_assets(test_slug)
    
    if not assets:
        print("No assets found or error occurred.")
    else:
        for i, asset in enumerate(assets, 1):
            print(f"{i}. {asset}")
            # print(f"   URL: {asset.source_url}\n")