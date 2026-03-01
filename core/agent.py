import ollama
import json
from core.engines.orchestrator import AgenticOrchestrator

class OllamaKCTAgent:
    """
    KCT Agentic Orchestrator powered by Ollama.
    It reasons about user intent to trigger specific ingestion and synthesis paths.
    """
    def __init__(self, model="llama3"):
        self.model = model
        self.orchestrator = AgenticOrchestrator(sources={}) # Pass your initialized sources here

    def _reason_tasks(self, prompt):
        """Phase 1: Decision Making. LLM identifies which tools to use."""
        system_prompt = (
            "You are the KCT Brain. Analyze the user request and return a JSON map of tasks. "
            "Keys must be 'arena' (for slugs), 'web' (for URLs), or 'local' (for file paths). "
            "Example: {'arena': 'design-inspo', 'web': 'https://example.com'}"
        )
        
        response = ollama.chat(
            model=self.model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ],
            format='json'
        )
        return json.loads(response['message']['content'])

    def _generate_synthesis(self, assets, tone_instruction):
        """Phase 2: LLM-Powered Synthesis. Replaces hard-coded logic."""
        context = "\n".join([f"Source: {a.source_name} | Content: {a.content[:300]}" for a in assets])
        
        prompt = f"Tone: {tone_instruction}\n\nContext:\n{context}\n\nProvide a cohesive narrative summary."
        
        response = ollama.generate(model=self.model, prompt=prompt)
        return response['response']

    def run(self, user_query):
        print(f"[Agent] Reasoning about: {user_query}")
        
        # 1. Decide which tools to use
        raw_tasks = self._reason_tasks(user_query)
        print(f"[Agent] Raw Decision: {raw_tasks}")

        # 2. CLEANING LAYER: Map LLM keys to valid Ingestor keys
        # This prevents KeyErrors from keys like ' arenas' or 'notebooks'
        valid_tasks = {}
        mapping = {
            "arena": "arena", "arenas": "arena", " arenas": "arena",
            "web": "web", "webs": "web", "website": "web",
            "local": "local", "files": "local", "notebooks": "local"
        }

        for k, v in raw_tasks.items():
            clean_key = k.strip().lower()
            if clean_key in mapping:
                # If the value is a complex dict (like in your error), 
                # we extract the primary identifier (slug/url/path)
                if isinstance(v, dict):
                    # Usually the first key in the sub-dict is the slug
                    identifier = list(v.keys())[0]
                else:
                    identifier = v
                
                valid_tasks[mapping[clean_key]] = identifier

        print(f"[Agent] Cleaned Tasks: {valid_tasks}")

        # 3. Execute Ingestion via Orchestrator
        all_assets = []
        for src, identifier in valid_tasks.items():
            if src in self.orchestrator.sources:
                assets = self.orchestrator.sources[src].get_assets(identifier)
                all_assets.extend(assets)

        # 4. Perform Agentic Synthesis
        narrative = self._generate_synthesis(all_assets, "Scholarly")

        return {
            "narrative": narrative,
            "citations": [{"url": a.source_url, "src": a.source_name} for a in all_assets],
            "task_map": valid_tasks
        }
