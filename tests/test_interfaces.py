import asyncio
import os
import sys
import time
from fastapi.testclient import TestClient
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from sales_coach.api import create_app


def test_api_confirmation_auth_and_report(settings, engine):
    headers = {"Authorization": "Bearer test-token"}
    with TestClient(create_app(settings, engine)) as client:
        assert client.post("/v1/examples/discovery").status_code == 401
        assert client.get("/health").status_code == 200
        created = client.post("/v1/examples/discovery", headers=headers).json()
        assert created["status"] == "needs_confirmation"
        body = {"rep_id": "maya", "rep_name": "Maya", "speaker": "A", "expected_revision": created["revision"]}
        base = f"/v1/calls/{created['id']}"
        response = client.post(base + "/confirmation", json=body, headers=headers)
        assert response.status_code == 202
        for _ in range(100):
            result = client.get(base, headers=headers).json()
            if result["status"] == "completed":
                break
            time.sleep(.01)
        assert result["status"] == "completed"
        assert result["result"]["delivery"]["recognized_filler_count"] == 3
        assert "staged_rules_only" in client.get(base + "/report", headers=headers).text
        assert client.post(base + "/confirmation", json=body, headers=headers).status_code == 409
        assert client.get(base + "/audio", headers=headers).status_code == 422
        assert client.delete(base, headers=headers).status_code == 200
        assert client.get(base, headers=headers).status_code == 404


def test_api_rejects_oversized_and_bad_context(settings, engine):
    settings.max_upload_bytes = 10
    h = {"Authorization": "Bearer test-token"}
    with TestClient(create_app(settings, engine)) as client:
        assert client.post("/v1/calls", headers=h, files={"audio": ("x.wav", b"RIFF" * 10)}).status_code == 413
        assert client.post("/v1/calls", headers=h, data={"context": '{"invented":true}'},
                           files={"audio": ("x.wav", b"RIFF")}).status_code == 422


async def test_real_mcp_stdio_roundtrip(tmp_path):
    env = {**os.environ, "COACH_DATA_DIR": str(tmp_path / "mcp-data"), "DEEPGRAM_API_KEY": "",
           "ANTHROPIC_API_KEY": "", "ANTHROPIC_MODEL": ""}
    params = StdioServerParameters(command=sys.executable, args=["-m", "sales_coach.mcp_server"], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            assert {"create_example", "submit_audio", "confirm_speaker", "get_call"} <= {t.name for t in listed.tools}
            result = await session.call_tool("create_example", {"name": "discovery"})
            assert not result.isError
            import json
            call = json.loads(result.content[0].text)
            assert call["status"] == "needs_confirmation"
            response = await session.call_tool("confirm_speaker", {"call_id": call["id"], "rep_id": "maya",
                "rep_name": "Maya", "speaker": "A", "expected_revision": call["revision"]})
            assert not response.isError
            for _ in range(100):
                result = await session.call_tool("get_call", {"call_id": call["id"]})
                done = json.loads(result.content[0].text)
                if done["status"] == "completed":
                    break
                await asyncio.sleep(.01)
            assert done["status"] == "completed"
            assert done["result"]["delivery"]["recognized_filler_count"] == 3
            assert done["result"]["coaching_mode"] == "staged_rules_only"
