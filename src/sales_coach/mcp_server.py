from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP
from .engine import Engine
from .models import CallContext, Confirmation


def create_mcp(engine):
    @asynccontextmanager
    async def lifespan(server):
        yield {}
        engine.close()

    mcp = FastMCP("Sales Coaching Engine", lifespan=lifespan,
        instructions="Self-hosted sales coaching. Staged examples are not real audio. Confirm the representative with the human before confirm_speaker. Never guess their identity. Audio submission/retry can incur user-funded provider charges.")

    @mcp.tool()
    def create_example(name: str = "discovery") -> dict:
        """Create an explicitly staged discovery, followup or casual transcript. No provider calls."""
        return engine.submit_fixture(name)

    @mcp.tool()
    def submit_audio(path: str, context: dict | None = None) -> dict:
        """Submit local media inside COACH_AUDIO_ROOT to Deepgram. Uses operator's paid key. Returns job ID; poll get_call."""
        return engine.submit_path(path, CallContext.model_validate(context or {}))

    @mcp.tool()
    def get_call(call_id: str) -> dict:
        """Get job status, transcript, revision and feedback. Needs-confirmation means ask the human which label is the rep."""
        return engine.get(call_id)

    @mcp.tool()
    def confirm_speaker(call_id: str, rep_id: str, rep_name: str, speaker: str, expected_revision: int) -> dict:
        """Record HUMAN-CONFIRMED identity (or correction), invalidate old feedback and queue analysis. Do not guess."""
        return engine.confirm(call_id, Confirmation(rep_id=rep_id, rep_name=rep_name,
            speaker=speaker, expected_revision=expected_revision))

    @mcp.tool()
    def get_report(call_id: str) -> str:
        """Get a readable report with timestamped evidence and limitations."""
        return engine.report(call_id)

    @mcp.tool()
    def rep_history(rep_id: str) -> list[dict]:
        """Read current confirmed call history. Descriptive metrics are not causal improvement claims."""
        return engine.history(rep_id)

    @mcp.tool()
    def retry_call(call_id: str, expected_revision: int) -> dict:
        """Explicitly retry a failed job. A previous provider request may have been billed; retry may cost again."""
        return engine.retry(call_id, expected_revision)

    @mcp.tool()
    def delete_call(call_id: str) -> dict:
        """Delete local call/audio on explicit user request. Does not guarantee provider-side erasure."""
        return engine.delete(call_id)

    return mcp


def main():
    create_mcp(Engine()).run(transport="stdio")


if __name__ == "__main__":
    main()
