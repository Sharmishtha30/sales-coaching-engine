# Engineering counterpart notes

## 1. Why this is a pipeline, not an autonomous agent

The steps are known: ingest, transcribe, confirm, analyze, persist, return. A pipeline makes failures inspectable. An agent chooses steps dynamically; that adds another source of variation before we can measure baseline quality. Tool use is justified when a user task requires decisions about which operation to perform, not merely because an LLM is present.

**Challenge:** draw the boundary between computation that must be deterministic and judgment that can be probabilistic. Filler counts from recognized words are deterministic; deciding whether an explanation addresses the buyer's actual concern is not.

## 2. Ports and adapters

The engine is application logic. Deepgram and Claude are outbound adapters; HTTP and MCP are inbound adapters. Changing the speech service should alter transcript conversion, not identity, storage and report behavior. The first adapters are intentionally small Python classes; a plugin registry would add complexity before a second implementation exists.

**Tradeoff:** using services gets us to a measurable baseline quickly but incurs variable costs and sends data externally. Self-hosted models offer more control but introduce model downloads, hardware sizing, throughput and license questions. Self-hosted application code does not mean all inference is local.

## 3. ASR, diarization and identification

ASR converts speech to words. Diarization assigns anonymous speaker labels. Identification connects a label to an actual person. Those are three different error sources. We confirm a stable rep ID manually in v1. A voiceprint would require enrollment, similarity thresholds and unknown-speaker rejection; we have not built or validated that yet.

**Challenge:** if two reps share a microphone, which source metadata remains trustworthy? When the model is uncertain, should it guess or ask? Measure false attribution separately from missing attribution.

## 4. State machines and concurrency

The status field is a state machine. Confirmation cannot occur before transcription exists, nor while another analysis is running. A SQLite revision is optimistic concurrency control: update only if the version is still the one the client saw. Otherwise return a conflict and make the client refresh.

A single worker bounds simultaneous provider calls. The active-job limit bounds the queue. A process lock prevents two engines from treating each other's work as interrupted. SQLite transactions protect individual writes; the lock and deployment restriction simplify broader coordination.

**Tradeoff:** a process-local executor is easy to inspect, but not a durable distributed queue. Restarted jobs become explicit failures. A future queue needs leases, retries, idempotency and dead-letter handling. Exactly-once paid API execution cannot be assumed when a timeout hides whether the provider finished.

## 5. Grounding and structured output

Structured output means the JSON matches a schema. Grounding means a claim is connected to relevant evidence. We validate the schema and utterance IDs, then reconstruct quotes from the transcript. This prevents invented quote text in the output path. It cannot establish that an interpretation follows from that quote.

**Challenge:** create a model response citing a real utterance that does not support its conclusion. It can pass reference validation while failing semantic evaluation. That is why we need human labels and unsupported-claim measurements.

## 6. Memory is data management before it is retrieval

V1 memory is persisted, human-confirmed rep identity and earlier call records. History is computed from current records, so correction/deletion changes future reads. We do not maintain a cached summary saying a person is "unconfident." We do not yet feed historical semantic advice back into Claude.

**Tradeoff:** scanning records is simple but grows with usage. Later add indexed rep/date columns and explicit retrieval budgets. A vector database is not required for exact identity lookup. Add semantic retrieval only for a demonstrated need, such as finding similar objections across a large archive.

## 7. What our timing metrics mean

An utterance span includes its internal pauses. Dividing word count by these spans is an approximate speaking rate, not articulation rate. Accurate pause analysis needs word alignment or voice activity detection and context for interruptions, packet loss and deliberate silence. V1 does not label silence as a defect.

We count a small filler lexicon rather than every "like" or "so." This sacrifices recall to reduce obvious false positives. It is an explicit precision/recall tradeoff. Zero recognized fillers can also mean the transcriber omitted them.

## 8. Threat boundaries

Recorded speech can contain instructions aimed at the model. We treat it as untrusted data and provide no model tools. Schema and evidence checks reduce some risks but do not guarantee prompt-injection immunity. Human review remains necessary.

HTTP needs a token; local MCP relies on the host's permissions. A permitted file root reduces accidental file disclosure. It is not a sandbox against a malicious local administrator. We reject remote URLs rather than building an SSRF-safe fetcher in this release.

## 9. Evaluation versus a green test suite

A passing test verifies a software behavior. It does not prove speech recognition or coaching quality. Mocked providers test how our code handles responses, not whether the real service returns accurate results. Staged scripts test the workflow; real audio is needed for acoustic validity.

**First real experiment:** record a consenting two-person staged script, manually label words and speakers, then run live transcription. Compare filler omissions, speaker changes and timing errors. Vary microphones and background noise while holding the script stable. Do not claim general accuracy from one recording.

## 10. Next experiments, in order

1. Record and label the provided scripts; establish a real-audio baseline.
2. Compare a second speech adapter against Deepgram on the same held-out examples.
3. Measure filler event precision/recall, not only transcript word error rate.
4. Compare source-channel identity to diarization plus human confirmation.
5. Evaluate Claude findings blindly against human notes and a transcript-only baseline.
6. Add historical context only after defining what facts may be retrieved and corrected.
7. Test stage-aware practice recommendations on similar future calls.
8. Explore pyannote/WhisperX with pinned model licenses and measured compute requirements.
9. Add voice enrollment only with a false-match evaluation protocol.
10. Implement durable queueing only after workload/reliability measurements justify it.

For each, write the hypothesis before results. Record rejected approaches. The project becomes valuable as a learning artifact through these decisions, not through the number of services added.
