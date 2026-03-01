from abc import ABC, abstractmethod
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
        display_content = (str(self.content)[:50] + '...') if self.content and len(str(self.content)) > 50 else self.content
        return f"AssetObject(type={self.asset_type.value}, source={self.source_name}, content='{display_content}')"


class DataSource(ABC):
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    @abstractmethod
    def fetch_data(self, source_identifier):
        pass

    @abstractmethod
    def standardize_output(self, raw_data):
        pass

    def get_assets(self, source_identifier):
        print(f"\n[{self.__class__.__name__}] Fetching: {source_identifier}")
        raw_data = self.fetch_data(source_identifier)
        if not raw_data:
            return []

        assets = self.standardize_output(raw_data)
        print(f"[{self.__class__.__name__}] Success: Extracted {len(assets)} assets.")
        return assets


class DataIngestor:
    """Unified factory to route requests to appropriate sources.

    Uses lazy imports inside __init__ to avoid circular imports between
    the base definitions and individual source modules.
    """
    def __init__(self):
        # Lazy imports to avoid circular module imports at import-time
        from .arena import ArenaSource
        from .web import WebSource
        from .local import LocalSource

        self.sources = {
            "arena": ArenaSource(),
            "web": WebSource(),
            "local": LocalSource()
        }

    def ingest(self, source_type, identifier):
        source = self.sources.get(source_type.lower())
        if not source:
            print(f"Source '{source_type}' not supported.")
            return []
        return source.get_assets(identifier)
