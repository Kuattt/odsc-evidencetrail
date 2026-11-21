"""Run one genuine research task and save its trace without printing secrets."""
import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from src.evidencetrail.agent import ResearchAgent


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", default="What does recent evidence say about the benefits and limitations of heat pumps in cold climates?")
    args = parser.parse_args()
    key = os.getenv("NEBIUS_API_KEY", "").strip()
    tavily = os.getenv("TAVILY_API_KEY", "").strip()
    if not key or not tavily:
        print("Missing keys:", ", ".join(k for k, v in (("NEBIUS_API_KEY", key), ("TAVILY_API_KEY", tavily)) if not v))
        return 2
    model = os.getenv("NEBIUS_MODEL", "").strip()
    if not model:
        client = OpenAI(base_url="https://api.tokenfactory.nebius.com/v1/", api_key=key, timeout=30)
        listed = [entry.id for entry in client.models.list().data]
        preferred = [x for x in listed if "gpt-oss-20b" in x.lower()]
        if not preferred:
            preferred = [x for x in listed if any(tag in x.lower() for tag in ("llama", "qwen", "mistral")) and not any(tag in x.lower() for tag in ("embed", "rerank", "vision"))]
        if not preferred:
            print("No suitable chat model found in account's model list")
            return 3
        model = preferred[0]
        with (ROOT / ".env").open("a") as file:
            file.write(f"\nNEBIUS_MODEL={model}\n")
        os.environ["NEBIUS_MODEL"] = model
    print("Nebius model:", model)
    result = ResearchAgent(model=model).run(args.question, lambda e: print(e.step, e.detail))
    destination = ROOT / "artifacts" / "live-research.json"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
    print("Verified:", result.tavily_searches, "Tavily searches;", result.nebius_calls, "Nebius inference calls;", len(result.sources), "sources")
    print("Saved:", destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
