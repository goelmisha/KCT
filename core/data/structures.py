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
        items = raw_data.get("data") or raw_data.get("contents")
        
        if items is None:
            return []

        for index, block in enumerate(items):
            try:
                b_type = block.get("class") or block.get("type")
                b_id = block.get("id")
                content = None
                a_type = None

                # --- UPDATED IMAGE LOGIC ---
                if b_type == "Image":
                    a_type = AssetType.IMAGE
                    img_dict = block.get("image", {})
                    
                    # Based on your debug: using 'src' first, then falling back to 'large' or 'medium'
                    content = (img_dict.get("src") or 
                               img_dict.get("large") or 
                               img_dict.get("medium") or
                               img_dict.get("display", {}).get("url"))

                elif b_type == "Attachment":
                    a_type = AssetType.DOCUMENT
                    content = block.get("attachment", {}).get("url")

                elif b_type == "Text":
                    a_type = AssetType.TEXT
                    # Handle if content is a dict (like your log shows) or a raw string
                    raw_content = block.get("content")
                    content = raw_content.get("plain") if isinstance(raw_content, dict) else raw_content

                elif b_type in ["Link", "Channel"]:
                    a_type = AssetType.LINK
                    if b_type == "Link":
                        content = block.get("source", {}).get("url") or block.get("embed", {}).get("url")
                    else:
                        content = f"https://www.are.na/channel/{block.get('slug')}"

                if a_type and content:
                    assets.append(AssetObject(
                        content=content,
                        source_url=f"https://www.are.na/block/{b_id}" if b_type != "Channel" else content,
                        asset_type=a_type,
                        source_name="Arena",
                        metadata={"id": b_id, "type": b_type}
                    ))

            except Exception as e:
                print(f"[ERROR] Index {index}: {str(e)}")
        
        return assets

# --- TEST ---
if __name__ == "__main__":
    slug = "timekeeping-timetraveling"
    arena = ArenaSource()
    results = arena.get_assets(slug)
    
    print(f"\n--- Final Output: {len(results)} assets found ---")
    for item in results:
        print(item)