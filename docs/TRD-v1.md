# TRD — Sales Coaching Engine v0.1

Written before implementation, 26 September 2026. Minimal vertical slice supporting PRD-v1.

## Architecture decisions
- Python: one language for API, MCP and later audio/ML experiments.
- FastAPI + Pydantic: HTTP routing and a typed contract. A schema validates shape and constraints; it does not prove a model's assertions are true.
- Official MCP Python SDK v1 (`mcp<2`): stdio adapter for compatible desktop/CLI hosts. Pin the supported major to avoid silently adopting a breaking API. This is not a public remote MCP endpoint.
- HTTPX: explicit timeouts and provider HTTP adapters. Deepgram supplies hosted ASR (automatic speech recognition) and diarization (who spoke when). Claude is optional for semantic coaching. End users pay providers.
- SQLite: durable local records with transactions. Single installation and one process; not multi-tenant SaaS. JSON documents simplify the first schema while retaining revision checks.
- Single background executor: bounded concurrency rather than a queue service. Persist state, mark interrupted work explicitly on restart, and allow an explicit retry. Do not auto-retry paid submissions after an unknown network outcome.
- No agent framework or vector database: a fixed workflow and explicit rep IDs solve the initial problem. Fetch prior metrics on demand rather than stale cached judgments.

## Flow and state
`queued → transcribing → needs_confirmation → analyzing → completed`; failures become `failed`. Correction invalidates the prior result before recomputation. A revision number prevents lost updates and a deleted job cannot be resurrected by a late worker.

Each call stores source mode, optional provider request/model metadata, created/call date, business/deal context, transcript, confirmed identity, result, error code and revision. Secrets are environment-only and never in records. A stable person ID is asserted by the operator, not inferred from a name.

## Analysis contract
Word/utterance timing bounds must be nonnegative and ordered. Count only a documented narrow filler lexicon; do not count ordinary uses of "like" or "so". Calculate rates per union of rep utterance spans (includes intra-utterance pauses), label that denominator. No acoustic emotion model. Silence between different speakers is not scored as rep hesitation.

Claude receives current transcript, trusted task instructions and user-supplied sales context clearly marked as untrusted data. Model output must match a schema and reference existing utterance IDs. The server reconstructs quotations and timestamps from source data. Referential evidence checks cannot establish that the interpretation is correct. Invalid results fail rather than being silently shown as valid. No model tools, browsing or side effects.

History is dynamically queried from current confirmed records. In v1 it supplies numerical comparisons and report links, not a persistent psychological profile or automatic causal attribution. Corrections therefore propagate without maintaining a vector index. Context-rich coaching memory is later work.

## Boundaries and operations
API token mandatory; bind localhost by default, no permissive CORS. Upload byte ceilings are configurable safety limits, not pricing. Duration depends on provider support; do not truncate. Reject arbitrary URLs (avoids SSRF). MCP resolves symlinks and restricts local files to AUDIO_ROOT. Use generated storage names. Local data directory is private; HTTPS/reverse proxy and disk encryption are operator responsibilities for deployment beyond localhost.

Deleting a call removes local record/audio; it does not certify provider-side erasure. Document provider retention separately. No application logging of raw transcripts or credentials. Limits on coaching input are explicit: oversized transcripts retain delivery metrics and clearly skip semantic coaching.

## Evaluation and remaining risks
Deterministic staged fixtures test identity, evidence, API/MCP parity, history and failure handling. Mock HTTP tests verify provider request/response contracts. They do not validate real service availability or speech accuracy. Live smoke tests require operator keys; the first release must disclose if not run. Multi-worker races, distributed queues, voice enrollment, detailed phonetic analysis and real-call accuracy are beyond this slice.

## Primary documentation consulted
- https://developers.deepgram.com/reference/speech-to-text/listen-pre-recorded
- https://developers.deepgram.com/docs/filler-words
- https://developers.deepgram.com/docs/utterances
- https://platform.claude.com/docs/en/api/messages/create
- https://py.sdk.modelcontextprotocol.io/v1/
- https://fastapi.tiangolo.com/tutorial/request-files/

Earlier AssemblyAI/WhisperX/pyannote research remains in the discovery memo. Deepgram is the first replaceable speech adapter, not an asserted winner of a benchmark. Claude model ID must be explicitly supplied so the operator chooses its price/quality tradeoff.
