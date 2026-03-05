import os
import sys
from core.ingestors.arena import ArenaSource
from core.ingestors.web import WebSource
from core.ingestors.local import LocalSource
from core.engines.orchestrator import AgenticOrchestrator

# Load .env automatically when present (keeps secrets out of git)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[main] dotenv loaded")
except ImportError:
    print("[main] python-dotenv not installed; ensure GITHUB_PAT is exported manually")
except Exception as e:
    print(f"[main] unexpected error loading dotenv: {e}")

try:
    from core.agent import KCTAgent
    from core.llm_providers import GitHubClient, OllamaClient
except Exception:
    # We'll handle missing providers at runtime: main chooses which client to build.
    pass


def main():
    # 1. Environment Setup
    if not os.path.exists("notes.md"):
        with open("notes.md", "w") as f:
            f.write("Deep work is a superpower in our increasingly competitive economy.")

    # 2. Initialize Ingestion Tools
    sources = {
        "arena": ArenaSource(),
        "web": WebSource(),
        "local": LocalSource()
    }
    
    # 3. Initialize the Orchestrator
    orchestrator = AgenticOrchestrator(sources)
    
    # 4. Initialize the Agent
    # GitHub models are preferred. If you truly *don't want* ollama,
    # you can set USE_OLLAMA=true to enable a fallback (disabled by default).
    use_ollama = os.getenv("USE_OLLAMA", "false").lower() in ("1", "true")
    github_pat = os.getenv("GITHUB_PAT") or ""
    # strip accidental quotes from dotenv values
    github_pat = github_pat.strip().strip('"').strip("'")
    azure_key = os.getenv("AZURE_API_KEY")
    api_url = os.getenv("GITHUB_API_URL")
    model_name = os.getenv("MODEL_NAME", "microsoft/Phi-4-multimodal-instruct")
    print(
        f"[main debug] USE_OLLAMA={use_ollama}, "
        f"raw github_pat={repr(github_pat)}, "
        f"azure_key={'SET' if azure_key else 'unset'}, "
        f"api_url={api_url}, model_name={model_name}"
    )
    llm_client = None

    if github_pat:
        try:
            api_url = os.getenv("GITHUB_API_URL")
            model_name = os.getenv("MODEL_NAME", "microsoft/Phi-4-multimodal-instruct")
            llm_client = GitHubClient(token=github_pat, model=model_name, api_url=api_url)
        except Exception as e:
            print(f"Failed to initialize GitHub client: {e}")
            if "404" in str(e):
                print("Hint: you may need to set GITHUB_API_URL to the correct generative endpoint.")
            if "model" in str(e).lower():
                print("Hint: ensure MODEL_NAME environment variable is valid.")

    if llm_client is None and use_ollama:
        try:
            llm_client = OllamaClient(model="llama3.2:1b")
            print("[main] using ollama fallback (USE_OLLAMA=true)")
        except Exception as e:
            print(f"Failed to initialize ollama client: {e}")

    if llm_client is None:
        print("No LLM provider is configured. Set GITHUB_PAT or allow ollama with USE_OLLAMA.")
        return

    agent = KCTAgent(llm_client=llm_client)
    agent.orchestrator = orchestrator

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
