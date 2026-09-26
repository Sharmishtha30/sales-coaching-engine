# Sales Coaching Engine

An open-source learning project: self-hosted, evidence-linked sales-call feedback through an HTTP API and MCP. Bring your own provider keys and storage. **v0.1 is a runnable baseline, not a validated sales coach.**

## What works

- No-key staged examples; live media adapter for Deepgram transcription, word timings and speaker labels.
- Human-confirmed rep identity before coaching; stable rep IDs and local call history.
- Recognized filler counts, timestamped evidence and conditional practice advice.
- Optional Claude analysis of sales category/stage, discovery, offering fit, objections and next steps.
- JSON and readable reports, speaker corrections, explicit retries and local deletion.
- Authenticated HTTP API and a real stdio MCP server using the same engine.

**Not implemented:** biometric voice matching, detailed prosody/emotion analysis, automatic CRM ingestion, roleplay, remote MCP hosting, multi-tenant SaaS or proven coaching improvement. SQLite stores confirmed identity and call history, not a trained voice model. Staged examples contain authored transcripts and timings, **not synthesized recordings**.

## Quickstart — no keys or paid services

Python 3.11+ on Linux/macOS (Windows: use Docker/WSL).

```bash
git clone https://github.com/Sharmishtha30/sales-coaching-engine.git
cd sales-coaching-engine
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
sales-coach demo
pytest -q
```

Or use `uv sync --extra dev --frozen` once the included lockfile is available, then `uv run sales-coach demo`.

The demo stores two fictional calls for Maya. The first contains three recognized fillers; the second contains none. This demonstrates history and deterministic analysis, **not better selling or verified speech recognition**. Repeat runs add new calls. Delete `data/` only when you intend to reset all local demo records and audio.

## HTTP API

```bash
export COACH_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
sales-coach serve
```

Open http://127.0.0.1:8000/docs for interactive endpoint documentation. Requests use `Authorization: Bearer <token>`. `/health` and schema docs expose no call data. The command binds to localhost.

In another terminal, export the same token, then:

```bash
curl -X POST http://127.0.0.1:8000/v1/examples/discovery \
  -H "Authorization: Bearer $COACH_API_TOKEN"
```

Copy the returned ID/revision; inspect the transcript. For this authored example only, A is Maya:

```bash
curl -X POST http://127.0.0.1:8000/v1/calls/CALL_ID/confirmation \
  -H "Authorization: Bearer $COACH_API_TOKEN" -H 'Content-Type: application/json' \
  -d '{"rep_id":"staged-maya","rep_name":"Maya","speaker":"A","expected_revision":0}'
```

Poll `GET /v1/calls/CALL_ID` until `completed` or `failed`. `GET /v1/calls/CALL_ID/report` returns Markdown text. `GET /v1/reps/staged-maya/history` returns current history. Use the latest revision when correcting a speaker. Unknown labels and stale revisions are rejected.

## Real audio — operator pays providers

Export `DEEPGRAM_API_KEY`. Optionally export **both** `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` (an available model ID from your own Claude account). No model choice or paid call is hidden in demo mode.

```bash
curl -X POST http://127.0.0.1:8000/v1/calls \
  -H "Authorization: Bearer $COACH_API_TOKEN" \
  -F 'audio=@my-call.wav' \
  -F 'context={"deal_id":"deal-01","stage":"discovery","call_goal":"Understand workflow and agree next step","product_context":"Describe actual product capabilities and restrictions here"}'
```

States: `queued → transcribing → needs_confirmation → analyzing → completed`, or `failed`.

Speaker labels from speech recognition are not verified identity. Listen to your original file (or authenticated `/audio` endpoint) and confirm the rep. Without Claude, live calls receive delivery-only rules and an explicit `uncertain` category. With Claude, valid model findings cite existing utterances; server-supplied quotes/timestamps prevent invented quotations. **An existing citation does not prove the interpretation is correct.**

Raw audio is sent to Deepgram; transcript and supplied business context are sent to Anthropic only when configured. Local deletion does not delete provider-retained data. Review provider retention before using sensitive recordings. Credentials live in environment variables, never in call records. No automatic paid retries: `POST /v1/calls/ID/retry` requires `{"expected_revision": N}` and may incur another charge.

Supported upload containers: WAV, MP3, M4A, OGG, FLAC, WebM, MP4. Header checks are preliminary; the speech provider validates decoding. Default byte limit is 100 MiB, configurable. Provider duration/format limits still apply. We do not silently truncate. Long text above the configurable coaching limit retains delivery results and explicitly skips Claude. Audio duration itself is not scored as a quality defect.

## MCP — connect a compatible local host

Install the project first. Configure a host supporting stdio MCP, replacing these absolute paths:

```json
{
  "mcpServers": {
    "sales-coach": {
      "command": "/absolute/path/sales-coaching-engine/.venv/bin/sales-coach-mcp",
      "env": {
        "COACH_DATA_DIR": "/absolute/path/mcp-coach-data",
        "COACH_AUDIO_ROOT": "/absolute/path/permitted-audio"
      }
    }
  }
}
```

Add provider credentials to the process environment for live analysis; keep them out of committed client configuration. Local path access is restricted to `COACH_AUDIO_ROOT`, including symlink resolution. The MCP host shares your machine's permissions; this is not an authentication boundary against other local users.

Tools: `create_example`, `submit_audio`, `get_call`, `confirm_speaker`, `get_report`, `rep_history`, `retry_call`, `delete_call`. Ask: “Create the discovery example, show me the speaker labels, and ask me which one is the rep.” Confirmations are human decisions; the host must not guess.

Run **one engine process per data directory**. API and MCP can run separately with distinct data directories. They share code, not a distributed runtime. Unified concurrent transports are future work. A public GitHub repository is not a hosted MCP endpoint.

## Deployment and configuration

See `.env.example` for variables; the app does not automatically load that file. Generate your own token. API tokens are operator-wide, not per-user authorization. Do not expose this learning release as a multi-tenant public service.

```bash
docker build -t sales-coach .
docker run --rm -p 127.0.0.1:8000:8000 \
  -e COACH_API_TOKEN -v coach-data:/app/data sales-coach
```

Container setup is supplied but Docker execution may not be available in the development environment; consult `docs/RELEASE-v0.1.md` for actual checks run. Default uploads cap at 100 MiB and active jobs at 32. Change `COACH_MAX_UPLOAD_MB`, `COACH_MAX_ACTIVE_JOBS`, or `COACH_MAX_COACHING_CHARS` deliberately. One worker processes one provider job at a time. A restart marks incomplete work failed; explicit retry is required. HTTPS, backups, disk encryption and provider accounts are operator responsibilities.

## Learn the engineering

- [PRD](docs/PRD-v1.md): behavior and boundaries.
- [TRD](docs/TRD-v1.md): architecture, state and tradeoffs.
- [Learning guide](docs/LEARNING.md): technical vocabulary and experiments.
- [Evaluation](docs/EVALUATION.md): how to measure quality without misleading yourself.
- [Release evidence](docs/RELEASE-v0.1.md): what was actually tested and what was not.
- [Research](docs/Audio-Coaching-Discovery.md): project history and competitor/component research.

The direct dependencies are open-source infrastructure (FastAPI, Pydantic, HTTPX, Uvicorn, MCP SDK). Deepgram and Anthropic are optional commercial services, not bundled open-source models. WhisperX and pyannote remain researched alternatives, **not dependencies installed by this release**.

MIT license for project code; dependencies and model weights retain their own licenses. No real customer recordings or provider keys are included.
