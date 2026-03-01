import re
import datetime
import json
from abc import ABC, abstractmethod
from enum import Enum

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