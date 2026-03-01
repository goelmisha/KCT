from core.ingestors.arena import ArenaSource
from core.ingestors.web import WebSource
from core.ingestors.local import LocalSource
from core.engines.orchestrator import AgenticOrchestrator

def main():
    # Initialize Sources
    sources = {
        "arena": ArenaSource(),
        "web": WebSource(),
        "local": LocalSource()
    }
    
    # Initialize Orchestrator
    brain = AgenticOrchestrator(sources)
    
    # Define Research Tasks
    tasks = {
        "arena": "paragonday",
        "web": "https://calnewport.com/blog/",
        "local": "notes.md"
    }
    
    # Execute Pipeline
    result = brain.process_pipeline(tasks)
    
    print(f"--- KCT OUTPUT ---\nTONE: {result['tone']}\nDRAFT: {result['draft']}")
    print(f"SOURCES VERIFIED: {len(result['citations'])}")

if __name__ == "__main__":
    main()