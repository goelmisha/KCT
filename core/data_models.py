from enum import Enum

class AssetType(Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    LINK = "link"
    TEXT = "text"

class AssetObject:
    def __init__(self, content, source_url, asset_type, source_name, metadata=None):
        self.content = content
        self.source_url = source_url
        self.asset_type = asset_type
        self.source_name = source_name
        self.metadata = metadata or {}
        
    def __repr__(self):
        display = (str(self.content)[:50] + '...') if self.content and len(str(self.content)) > 50 else self.content
        return f"Asset(type={self.asset_type.value}, source={self.source_name}, content='{display}')"
