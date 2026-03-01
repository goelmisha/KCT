import os
import sys
from core.ingestors.arena import ArenaSource
from core.ingestors.web import WebSource
from core.ingestors.local import LocalSource
from core.engines.orchestrator import AgenticOrchestrator
import os

try:
    from core.agent import OllamaKCTAgent
except ImportError:
    print("Error: 'ollama' library not found. Run 'pip install ollama'")
    sys.exit(1)

def main():
<<<<<<< HEAD
    # 1. Environment Setup
=======
>>>>>>> 747156d (finalize modular kct architecture with seperate ingestor and engines packages)
    if not os.path.exists("notes.md"):
        with open("notes.md", "w") as f:
            f.write("Deep work is a superpower in our increasingly competitive economy.")

<<<<<<< HEAD
    # 2. Initialize Ingestion Tools
=======
    # Initialize Sources
>>>>>>> 747156d (finalize modular kct architecture with seperate ingestor and engines packages)
    sources = {
        "arena": ArenaSource(),
        "web": WebSource(),
        "local": LocalSource()
    }
    
    # 3. Initialize the Orchestrator
    orchestrator = AgenticOrchestrator(sources)
    
    # 4. Initialize the Agent
    try:
        agent = OllamaKCTAgent(model="llama3.2:1b")
        agent.orchestrator = orchestrator
    except Exception as e:
        print(f"Agent Initialization Failed: {e}. Check if Ollama is running.")
        return

    # 5. Natural Language Input
    user_query = (
        "Analyze the connection between the 'paragonday' arena channel "
        "and Cal Newport's thoughts on focus in his blog, "
        "incorporating my local notes on deep work."
    )
    
    # 6. Execute Agentic Pipeline
    result = agent.run(user_query)
    
    # 7. Final Output
    print("\n" + "="*50)
    print("      KCT AGENTIC KNOWLEDGE PACKET")
    print("="*50)
    print(f"DECIDED TASKS: {result.get('task_map')}")
    print(f"\nSYNTHESIZED NARRATIVE:\n{result['narrative']}")
    print("\n" + "-"*50)
    print(f"VERIFIED CITATIONS ({len(result['citations'])}):")
    for citation in result['citations']:
        print(f" - [{citation['src']}] {citation['url']}")
    print("="*50)

if __name__ == "__main__":
    main()
