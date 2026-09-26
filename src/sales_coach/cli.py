import argparse
import json
from .engine import Engine
from .models import Confirmation


def main():
    parser = argparse.ArgumentParser(description="Self-hosted sales coaching learning release")
    parser.add_argument("command", choices=["demo", "serve", "mcp"])
    args = parser.parse_args()
    if args.command == "serve":
        import uvicorn
        uvicorn.run("sales_coach.api:create_app", factory=True, host="127.0.0.1", port=8000)
    elif args.command == "mcp":
        from .mcp_server import main as run_mcp
        run_mcp()
    else:
        engine = Engine()
        try:
            calls = []
            for name in ("discovery", "followup"):
                call = engine.submit_fixture(name)
                # Identity is authored with the fixture, not inferred from voice.
                engine.confirm(call["id"], Confirmation(rep_id="staged-maya", rep_name="Maya (fictional)",
                    speaker="A", expected_revision=call["revision"]), background=False)
                calls.append(engine.get(call["id"]))
            print(json.dumps({"notice": "STAGED TRANSCRIPTS; no audio recognition performed", "calls": calls}, indent=2))
        finally:
            engine.close()
