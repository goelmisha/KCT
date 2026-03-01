from core.ingestors.arena import ArenaSource
from core.ingestors.web import WebSource
from core.ingestors.local import LocalSource
from core.engines.orchestrator import AgenticOrchestrator
import os

def main():
    if not os.path.exists("notes.md"):
        with open("notes.md", "w") as f:
            f.write("Deep work is a superpower in our increasingly competitive economy.")

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