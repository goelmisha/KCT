from bs4 import BeautifulSoup
import re
import datetime
import json
from abc import ABC, abstractmethod
from enum import Enum
import requests
import os

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


class WebSource(DataSource):
    """
    Actual Web/Blog Ingestion using BeautifulSoup4.
    Extracts the main body text and title from a given URL.
    """
    def fetch_data(self, url):
        print(f"[1/2] FETCHING WEB: {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        try:
            # 10s timeout to prevent hanging on slow blogs
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return {
                "url": url, 
                "html": response.text, 
                "status": response.status_code
            }
        except Exception as e:
            print(f"[WEB ERROR] Failed to fetch {url}: {e}")
            return None

    def standardize_output(self, raw_data):
            if not raw_data: return []
            try:
                soup = BeautifulSoup(raw_data["html"], "html.parser")
                for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
                    element.decompose()

                # --- TARGETED SELECTION ---
                # Most blogs wrap main content in <article> or a 'content' id/class
                main_content = (soup.find('article') or 
                            soup.find('main') or 
                            soup.find(id='content') or 
                            soup.find(class_='post-content') or 
                            soup) # Fallback to body if none found

                title = soup.title.string if soup.title else "Untitled"
                clean_text = main_content.get_text(separator="\n", strip=True)

                return [AssetObject(
                    content=clean_text[:5000], # Increased for full blog posts
                    source_url=raw_data["url"],
                    asset_type=AssetType.TEXT,
                    source_name="Web",
                    metadata={
                        "title": title.strip(),
                        "ingestion_time": datetime.datetime.now().isoformat()
                    }
                )]
            except Exception as e:
                print(f"[PARSING ERROR] {e}")
                return []


class LocalSource(DataSource):
    """
    Real Local Ingestion for RAG workflows.
    Reads local files, handles PII, and extracts metadata.
    """
    def fetch_data(self, file_path):
        print(f"[1/2] READING FILE: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"[LOCAL ERROR] File not found: {file_path}")
            return None

        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext in [".txt", ".md", ".py", ".java", ".rs"]:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            elif ext == ".pdf":
                # Note: Requires 'pip install pypdf'
                import pypdf
                reader = pypdf.PdfReader(file_path)
                content = "\n".join([page.extract_text() for page in reader.pages])
            else:
                print(f"[LOCAL WARNING] Unsupported extension {ext}. Attempting raw read.")
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            
            return {
                "path": file_path,
                "raw_text": content,
                "ext": ext,
                "size": os.path.getsize(file_path)
            }
        except Exception as e:
            print(f"[LOCAL ERROR] Failed to read {file_path}: {e}")
            return None

    def _sanitize_pii(self, text):
        # Email Redaction
        text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', "[REDACTED_EMAIL]", text)
        # Simple Phone Number Redaction (Optional addition)
        # text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', "[REDACTED_PHONE]", text)
        return text

    def standardize_output(self, raw_data):
        if not raw_data: return []

        print(f"[2/2] SANITIZING & ENRICHING: {raw_data['path']}")
        clean_content = self._sanitize_pii(raw_data["raw_text"])
        
        return [AssetObject(
            content=clean_content,
            source_url=f"file://{os.path.abspath(raw_data['path'])}",
            asset_type=AssetType.DOCUMENT if raw_data["ext"] == ".pdf" else AssetType.TEXT,
            source_name="Local",
            metadata={
                "file_ext": raw_data["ext"],
                "file_size_kb": round(raw_data["size"] / 1024, 2),
                "security_layer": "PII_REDACTED",
                "ingested_at": datetime.datetime.now().isoformat()
            }
        )]

# --- TEST ---
if __name__ == "__main__":
    slug = "timekeeping-timetraveling"
    arena = ArenaSource()
    results = arena.get_assets(slug)
    
    print(f"\n--- Final Output: {len(results)} assets found ---")
    for item in results:
        print(item)
    print("\n" + "="*50 + "\n")

    # 2. Test the Web Source (New)
    web_scraper = WebSource()
    
    # Using a high-signal blog post as a test case
    test_urls = [
        "https://calnewport.com/blog/", # Productivity/Deep Work context
        "https://pudding.cool/2024/03/hype/" # Data-heavy site to test cleaning
    ]

    for url in test_urls:
        print(f"--- Starting Web Ingestion: {url} ---")
        web_assets = web_scraper.get_assets(url)
        
        if web_assets:
            asset = web_assets[0]
            print(f"SUCCESS: Extracted from {asset.metadata.get('title')}")
            # Print first 200 chars to verify it's clean text and not HTML tags
            print(f"PREVIEW: {asset.content[:200]}...")
            print(f"METADATA: {asset.metadata}")
        else:
            print(f"FAILURE: Could not extract content from {url}")
        print("-" * 30)

# 3. Test Local Source
    local_source = LocalSource() 
    
    # Create a quick dummy file for testing
    dummy_file = "test_deep_work.md"
    with open(dummy_file, "w") as f:
        f.write("# Project Deep Work\nContact misha@example.com for algorithmic trading logs.")

    print(f"\n--- Starting Local Ingestion: {dummy_file} ---")
    local_assets = local_source.get_assets(dummy_file)
    
    if local_assets:
        asset = local_assets[0]
        print(f"CLEAN CONTENT: {asset.content}")
        print(f"METADATA: {asset.metadata}")

    # Cleanup (Optional)
    # os.remove(dummy_file)