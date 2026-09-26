# v0.1 release evidence

Date: 26 September 2026. Status: learning release. Source repository: https://github.com/Sharmishtha30/sales-coaching-engine

## Delivered

Shared Python engine, token-authenticated HTTP API, official SDK stdio MCP server, local SQLite persistence, human speaker confirmation/correction, async job processing, bounded active jobs, explicit retries, local deletion, staged scripts, Deepgram adapter, optional Claude adapter, reports, Docker definition, dependency lockfile and CI definition.

PRD-v1 and TRD-v1 were committed before implementation. Earlier discovery documents are historical; this release note and those versioned specifications describe the implemented slice. MIT is the chosen permissive project-code license. No real calls or provider credentials are included.

## Checks actually run

- 22 automated tests passed under Python 3.12.14.
- Actual MCP stdio subprocess/client: initialization, tool discovery, staged submission, human confirmation and result retrieval passed.
- Actual Uvicorn HTTP socket: startup, unauthorized-request rejection, staged submission, confirmation, completion and report passed.
- CLI demo: two completed fictional calls, recognized filler counts 3 and 0, second call has one prior call in a fresh store.
- Wheel and source-distribution builds succeeded.
- Provider HTTP adapters tested with mocks: required request flags, parsing, source evidence reconstruction and invalid-evidence rejection.
- Correction removes the old rep association; history excludes future calls and excludes mixing staged/live sources; local deletion removes stored audio.
- File-root and symlink rejection, stale revisions, process lock, restart handling, queue limit, upload limit, semantic input limit and sanitized errors tested.

Test suite emits one upstream Starlette deprecation warning about its HTTPX test-client integration. It does not fail the tests. The real socket check initially inherited a development-environment SOCKS proxy without its optional library; the loopback-only smoke client was corrected to bypass environment proxies. Normal deployment behind SOCKS requires installing HTTPX's optional SOCKS support.

## Not verified

- No live Deepgram or Anthropic request was made; no paid credentials were supplied. Real-provider operation and quality need a live smoke test.
- No real or synthesized audio recording was transcribed. Staged fixtures are text with authored timings, not speech-recognition evidence.
- No measured WER, diarization accuracy, acoustic confidence, semantic coaching accuracy or sales uplift.
- Docker was not executed because Docker is unavailable in this environment; Dockerfile is supplied, not certified by this run.
- CI is defined but has not run on GitHub.
- No external MCP host UI configuration, remote MCP, multi-tenant deployment or load test was performed.
- No biometric enrollment, automatic recurring-voice identification, semantic memory injection, roleplay, CRM connector or product-insight aggregation.

## Reproduce

Use the README quickstart. The lockfile records the resolved dependency graph. API and MCP must use separate data directories if run simultaneously. Example provider requests can incur charges; demo mode cannot. Keep recordings and API keys outside Git.

## Next release experiment

Record a consenting two-person staged script, annotate the actual words/speakers/timings, then run live transcription. Identify whether the largest downstream coaching errors originate in ASR, attribution, missing product context or the coaching model before adding complexity.

## Publication status

The founder created the public `Sharmishtha30/sales-coaching-engine` repository on 26 September 2026. The initial local release archive preserves local commits in a Git bundle. Repository publication carries the discovery, specification and implementation history forward. The checks listed above were run locally before publication; consult GitHub Actions for subsequent CI results. This is source publication, not a hosted API or remote MCP deployment.
