# PRD — Sales Coaching Engine v0.1

Status: implementation baseline, 26 September 2026. The founder authorized immediate v1 delivery with staged examples. This is a learning release, not a production accuracy claim.

## Purpose and users
An open-source, self-hosted engine for developers and technically assisted sales managers. Analyze English recorded calls, confirm which voice belongs to the salesperson, produce inspectable coaching, and retain user-owned history. API and MCP are equally supported. No billing, acquisition or hosted service.

## First usable slice
1. Start locally with no credentials using explicitly staged transcript fixtures.
2. For real audio, configure a Deepgram API key. Audio is sent to Deepgram for transcription, word timing and speaker labels.
3. Analysis pauses at `needs_confirmation`. The human supplies a stable rep ID, display name and speaker label after inspecting the transcript/audio.
4. Compute delivery observations from recognized words/timings. Optional Claude coaching evaluates discovery, fit, objections and next steps using supplied business context. Without a coaching key, return limited deterministic observations, not fabricated semantic feedback.
5. Return JSON and a readable report; save confirmed identities and call records in local SQLite.
6. Retrieve earlier calls for the same rep, scoped to one installation. Comparisons are descriptive, not proof of improvement.
7. Reassign a speaker or delete a call. Recompute analysis and derive history dynamically, so old identity associations do not persist in materialized summaries.

## Outputs and honesty
Explicit provenance (`staged_fixture` or `deepgram`), model/config metadata, processing state, transcript and speaker labels, recognized filler counts, approximate utterance-span speaking time, evidence timestamps, coaching mode, limitations, and optional prior-call references. Staged fixtures test software flow, not speech recognition. No confidence/personality inference, voice biometrics, guaranteed sales uplift or blanket accuracy score.

## Scope boundaries
API upload, job status, confirmation, report/history and deletion; MCP equivalents including permitted local-file submission. Async single-worker execution in one installation. Stable rep IDs provide continuity; biometric voice matching is deferred pending real audio. No CRM connector, browser recorder, dashboard, roleplay agent, automatic publication or cross-user hosted tenancy.

## Acceptance checks
- A no-key demo runs through confirmation and produces inspectable JSON.
- API and actual MCP client use the same engine with equivalent results.
- Analysis never attributes coaching to a named rep before confirmation.
- Bad input, missing credentials, provider errors and invalid model evidence fail explicitly.
- Correcting an identity removes the old rep's association; deleting records removes local audio and history.
- HTTP requires an operator token; MCP local paths are restricted to a configured root. No secrets or real calls ship with the repository.
- Tests cover behavior and failure paths. Live provider accuracy remains unverified until real calls and credentials are available.

## Learning/release loop
Ship a reproducible baseline, record its limitations, then obtain human-labeled real calls. Compare transcript-only and audio-aware pipelines on held-out examples. Evaluate transcription, attribution, filler detection and coaching separately. Publish experiment settings, failures, costs and regressions alongside improvements.
