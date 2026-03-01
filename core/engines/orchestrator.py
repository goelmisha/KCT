#collection synthesis and orchestration

import datetime
from core.data_models import AssetType

import re

class SynthesisEngine:
    def analyze_tone(self, assets):
        srcs = [a.source_name for a in assets]
        return "Scholarly" if "Web" in srcs or "Local" in srcs else "Curated"

    def synthesize_text(self, assets, tone):
        # 1. Filter for content that is NOT just a URL
        url_pattern = re.compile(r'^https?://\S+$')
        
        # 2. Extract content and strip whitespace
        texts = []
        for a in assets:
            content_str = str(a.content).strip()
            # Only include if it's not a direct URL and has substantial text
            if content_str and not url_pattern.match(content_str) and len(content_str) > 5:
                texts.append(content_str)

        count = len(texts)
        # 3. Join with a clean separator for readability
        combined = " | ".join(texts)[:800] # Increased limit to see more content
        
        if count == 0:
            return f"[{tone}] No narrative text found (only images/links present)."
            
        return f"[{tone}] Summary of {count} verified text segments: {combined}..."

class CollectionEngine:
    def compile_citations(self, assets):
        return [{"src": a.source_name, "url": a.source_url} for a in assets]

class AgenticOrchestrator:
    def __init__(self, sources):
        self.sources = sources
        self.synthesis = SynthesisEngine()
        self.collection = CollectionEngine()

    def process_pipeline(self, request_map):
        all_assets = []
        for s_type, ident in request_map.items():
            if s_type in self.sources:
                all_assets.extend(self.sources[s_type].get_assets(ident))
        
        tone = self.synthesis.analyze_tone(all_assets)
        return {
            "tone": tone,
            "draft": self.synthesis.synthesize_text(all_assets, tone),
            "citations": self.collection.compile_citations(all_assets),
            "assets": all_assets
        }
