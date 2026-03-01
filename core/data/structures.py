import re
import datetime
import json
import os
import requests
from abc import ABC, abstractmethod
from enum import Enum
from bs4 import BeautifulSoup

# --- 1. Enumerations & Data Objects ---

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

# --- 2. Base Infrastructure ---

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
        """Unified entry point for all sources with built-in logging."""
        print(f"\n[{self.__class__.__name__}] Fetching: {source_identifier}")
        raw_data = self.fetch_data(source_identifier)
        if not raw_data:
            return []
        
        assets = self.standardize_output(raw_data)
        print(f"[{self.__class__.__name__}] Success: Extracted {len(assets)} assets.")
        return assets

# --- 3. Specific Source Implementations ---

class ArenaSource(DataSource):
    def fetch_data(self, channel_slug):
        url = f"https://api.are.na/v3/channels/{channel_slug}/contents"
        try:
            response = requests.get(url, params={"per": 20}, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"  [Arena Error] {e}")
            return None

    def standardize_output(self, raw_data):
        assets = []
        items = raw_data.get("data") or raw_data.get("contents") or []

        for block in items:
            b_type = block.get("class") or block.get("type")
            try:
                content, a_type = self._parse_block(block, b_type)
                if content:
                    assets.append(AssetObject(
                        content=content,
                        source_url=f"https://www.are.na/block/{block.get('id')}" if b_type != "Channel" else content,
                        asset_type=a_type,
                        source_name="Arena",
                        metadata={"id": block.get("id"), "raw_type": b_type}
                    ))
            except Exception:
                continue
        return assets

    def _parse_block(self, block, b_type):
        """Helper to handle nested Are.na media resolutions."""
        if b_type == "Image":
            img = block.get("image", {})
            url = img.get("src") or img.get("large") or img.get("display", {}).get("url")
            return url, AssetType.IMAGE
        
        if b_type == "Text":
            c = block.get("content")
            text = c.get("plain") if isinstance(c, dict) else c
            return text, AssetType.TEXT
        
        if b_type == "Attachment":
            return block.get("attachment", {}).get("url"), AssetType.DOCUMENT
        
        if b_type in ["Link", "Channel"]:
            url = block.get("source", {}).get("url") if b_type == "Link" else f"https://www.are.na/channel/{block.get('slug')}"
            return url, AssetType.LINK
        
        return None, None

class WebSource(DataSource):
    def fetch_data(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return {"url": url, "html": response.text, "status": response.status_code}
        except Exception as e:
            print(f"  [Web Error] {e}")
            return None

    def standardize_output(self, raw_data):
        try:
            soup = BeautifulSoup(raw_data["html"], "html.parser")
            for noise in soup(["script", "style", "nav", "footer", "header", "aside"]):
                noise.decompose()

            # Target high-signal content areas
            main_content = soup.find('article') or soup.find('main') or soup
            title = soup.title.string if soup.title else "Untitled Webpage"
            clean_text = main_content.get_text(separator="\n", strip=True)

            return [AssetObject(
                content=clean_text[:5000],
                source_url=raw_data["url"],
                asset_type=AssetType.TEXT,
                source_name="Web",
                metadata={"title": title.strip(), "time": datetime.datetime.now().isoformat()}
            )]
        except Exception as e:
            print(f"  [Parsing Error] {e}")
            return []

class LocalSource(DataSource):
    def fetch_data(self, file_path):
        if not os.path.exists(file_path):
            print(f"  [Local Error] File not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return {
                    "path": file_path,
                    "raw_text": f.read(),
                    "ext": os.path.splitext(file_path)[1]
                }
        except Exception as e:
            print(f"  [Local Error] {e}")
            return None

    def _sanitize_pii(self, text):
        return re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', "[REDACTED_EMAIL]", text)

    def standardize_output(self, raw_data):
        clean_content = self._sanitize_pii(raw_data["raw_text"])
        return [AssetObject(
            content=clean_content,
            source_url=f"file://{os.path.abspath(raw_data['path'])}",
            asset_type=AssetType.TEXT,
            source_name="Local",
            metadata={"file_ext": raw_data["ext"], "security": "PII_REDACTED"}
        )]

# --- 4. The Master Ingestor ---

class DataIngestor:
    """Unified factory to route requests to appropriate sources."""
    def __init__(self):
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

# --- 5. Main Execution ---

if __name__ == "__main__":
    manager = DataIngestor()

    # Test Arena
    arena_results = manager.ingest("arena", "paragonday")
    
    # Test Web
    web_results = manager.ingest("web", "https://calnewport.com/blog/")

    # Test Local
    with open("test_kct.md", "w") as f: f.write("Deep Work notes. Email: misha@trading.com")
    local_results = manager.ingest("local", "test_kct.md")

    # Combine for final summary
    all_extracted = arena_results + web_results + local_results
    print("\n" + "="*30)
    print(f"KCT INGESTION COMPLETE: {len(all_extracted)} Assets Processed.")
    print("="*30)