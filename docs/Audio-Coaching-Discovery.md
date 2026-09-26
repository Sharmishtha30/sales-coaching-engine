# Sales coaching engine — discovery and research v0.3

Updated: 26 September 2026. Status: discovery; not an approved PRD or TRD. No product implementation started.

## 0. Current project charter — learning in public

The founder has confirmed that this is an in-depth open-source AI learning project. Monetization, pricing, customer acquisition and distribution are not project goals. A unique commercial moat is not a prerequisite to building. Prior market research remains useful for understanding alternatives and avoiding unsupported novelty claims.

Deliver one self-hosted sales-coaching engine, an embeddable API and an MCP server over the same functionality. Both interfaces are in scope. Users provide their own provider credentials, compute and storage and bear their own operating costs. The maintainer does not provide a free hosted inference endpoint. A fully local model stack is a possible later option, not implied by self-hosting the engine.

The intended repository is public, superseding earlier private-repository recommendations. No remote repository has been created or pushed. Public code does not make user recordings, voice references, credentials or private evaluation labels public. Only cleared demo data and aggregate results belong in public releases. An explicit open-source license is still to be selected before publication.

Success means a reproducible working engine, understandable tradeoffs, evidence-backed output, documented failure cases and measurable improvements across versions. Adoption is welcome but is not a gate. Manager usefulness remains the product-quality check; a developer's ability to install and integrate it is the usability check.

### Learning questions

- How do transcription mistakes change downstream coaching, and which mistakes matter most?
- When do source channels or speaker metadata outperform diarization or voice matching?
- What can be measured directly in audio, what requires contextual interpretation, and when should the system abstain?
- Does prior-call memory improve useful feedback, or repeat stale and incorrect judgments?
- What is the accuracy/cost/latency tradeoff of each provider and processing stage?
- Can API and MCP produce equivalent results, correction behavior and access boundaries?
- Which failures come from audio quality, missing context, model choice, prompts or evaluation labels?

### Accuracy must be a scorecard

| Layer | Candidate measurement | Key caveat |
| --- | --- | --- |
| Transcription | Word error rate on human transcripts; separate names, numbers and sales terms | An accurate polished transcript may still omit fillers |
| Speaker attribution | Segment attribution errors, diarization error and unknown coverage | Wrong-person coaching is more serious than an unresolved speaker |
| Voice matching, if enabled | False matches, missed matches and unknown rejection | Compare across microphones and recording conditions |
| Fillers and pauses | Event precision/recall and timestamp deviation | State the annotation rules and speaking-time denominator |
| Sales analysis | Rubric agreement and correct supporting evidence | Human reviewers can disagree; retain uncertainty |
| Recommendations | Relevance, actionability and unsupported-claim rate | A persuasive recommendation is not necessarily correct |
| Memory | Correct prior-fact retrieval, stale-context errors and correction propagation | A corrected identity must not leave old judgments attached |
| Interfaces | Schema validity, equivalent outputs and reliable job/correction handling | Interface success does not establish coaching quality |

Report denominators, dataset/model/rubric versions, settings and uncertainty. Compare on a fixed held-out set; if used to guide changes, treat it as development data and obtain fresh holdout examples. Publish regressions as well as gains. Separate synthetic-demo performance from real-call performance. Do not manufacture a single overall accuracy percentage.

### Experiment record for every meaningful iteration

Record the question, hypothesis, baseline, isolated change, dataset split, model/provider versions, prompts/configuration, results by metric and relevant audio condition, cost per audio hour, processing time, failure examples, limitations and the decision to keep or revert. Prefer one meaningful change at a time. Do not add agents, retrieval or fine-tuning unless a measured failure motivates them.

Proposed ablations: transcript-only versus audio-aware analysis; no memory versus verified memory; source identity versus inferred speaker identity; generic rubric versus sales-context rubric. These are planned comparisons, not completed experiments.

### Public documentation plan

Maintain a README/quickstart, PRD, TRD, architecture decision records, evaluation guide, experiment log, failure catalogue, API/MCP usage examples and changelog. Each public update should explain what was attempted, what changed, what failed and what remains uncertain. No posting to social accounts is authorized or performed.

## 1. Decisions captured from the founder

- Start with sales teams or platforms serving sales teams. Interview preparation and general conversations are later markets.
- Evaluate the salesperson across the journey from first call through closing.
- Current workflow: a manager manually samples a handful of calls to diagnose problems.
- Desired analysis includes delivery, filler words, pauses, pitch, understanding the buyer's needs and fitting the offering to those needs.
- Feedback should lead to concrete practice, such as a five-day spoken-pitch cadence, and future calls should reveal whether behavior changes.
- Remember identity, goals, weaknesses, prior advice, business context and outcomes; managers are the initial consumers of history.
- English first. Post-call asynchronous processing is acceptable. Roll out progressively by version.
- Easy integration is a goal; the first distribution channel and customer segment remain undecided.
- Future product: extract buyer pain points and product feedback from the same calls.
- Founder offered to review ten recordings and provide human notes.
- Requested new repository under Sharmishtha30. Connected GitHub identity is abhishtapathak; no accessible Sharmishtha30 repositories were returned. Available connector supports file writes but not repository creation. Remote creation and pushing remain blocked on an accessible target. Do not create under a different owner silently.

## 2. Working product proposition

Help a sales manager identify specific, coachable behaviors across recorded calls, prescribe focused practice, and verify improvement in subsequent calls, using the company's sales context and evidence that can be replayed.

This proposition is a hypothesis, not proof of demand or uniqueness. Audio processing is an enabling component. The learning objective is to build and evaluate useful coaching, with less manual review where the evidence supports it.

## 3. Earlier commercial analysis — retained as context, not launch requirements

| Candidate customer | User and buyer | Job to be done | Main risk | Validation needed |
| --- | --- | --- | --- | --- |
| Small/mid-sized consultative B2B sales team | Manager uses; sales leader owns budget | Review more reps and improve discovery, objection handling and next steps | Established tools already cover much of this | Accessible calls, weekly manager review, paid pilot intent |
| High-volume inside-sales team | Team leader/QA uses; sales operations buys | Find repeated delivery and qualification problems across many calls | Price sensitivity, recording quality, operations complexity | Connected-call minutes, usable recordings, cost ceiling |
| CRM/dialer/coaching platform | Developer integrates; product/commercial owner buys | Add coaching without building the audio and evaluation pipeline | Integration and procurement take time; platform may build internally | Named integration sponsor and willingness to embed/pay |

Recommendation pending founder input: begin with one reachable team as a design partner, ideally with recorded consultative sales calls and a manager willing to correct feedback weekly. Treat an embeddable platform offering as a distribution hypothesis. Team customers and platform customers have different buying journeys even if the engine is shared.

Do not choose a channel using an invented global phone-versus-video share. McKinsey's 2024 survey covered nearly 4,000 B2B decision makers across 13 countries. It reports an average of ten interaction channels and roughly thirds in preferences for in-person, remote and self-service interaction. This is not a count of phone versus video calls. [S1]

No defensible universal split was established in this research. Nor does channel prevalence establish willingness to pay. Obtain a 30-day channel inventory from pilot teams: connected calls, recorded calls, usable audio minutes, stages, exportability, rep/deal identifiers and manager review time.

For market sizing, start bottom-up after selecting a geography and segment: reachable accounts × eligible teams × plausible annual contract value. Separately estimate platform opportunities. Do not combine raw dialing attempts, recorded conversations and sales revenue as equivalent measures.

## 4. Channel and identity choices

| Source | Available context | Implication | Limits to verify |
| --- | --- | --- | --- |
| Business dialer/telephony | Recording and call identifiers; integration may supply rep and CRM mapping | Strong candidate for stable rep identity without voice enrollment | Provider, channel configuration, agent transfers, conferences and recording access |
| Twilio/Flex dual-channel recording | Agent and customer audio can be on distinct channels [S2] | Prefer channel attribution when supplied | Do not assume every uploaded stereo file uses that mapping |
| Zoom | Separate participant audio can be recorded; local setup is documented [S3] | Preserve individual tracks and source names when available | Configuration and export determine what we actually receive; display name is not verified identity |
| Google Meet | Transcript entries include participant reference, text and start/end times [S4] | Source attribution can assist speaker mapping | Transcript access does not guarantee audio access or preserved fillers; artifact permissions vary |
| Generic mixed audio upload | Possibly no participant metadata | Diarize, play sample clips and request manager confirmation | Voice matching needs separate evaluation and authorized enrollment |

Proposed identity priority: trusted source rep ID and channel mapping → manager-confirmed mapping → optional enrolled voice match with confidence and human confirmation → unknown. Never merge people across customers. A corrected speaker assignment must invalidate affected rep feedback and aggregates.

Retain rep identity across calls even without storing a voiceprint. A prospect's voiceprint is not necessary merely to link a deal. Use explicit CRM/deal identifiers where available. Recording permission and voice enrollment should be separate product choices; decide retention, deletion and access before the pilot. No voice cloning is proposed.

First input recommendation: audio upload plus a small metadata record (rep, deal, date, source and optional stage), with one source integration chosen after pilot inventory. Easy integration means a stable contract and good documentation, not simultaneous support for every provider.

## 5. Competitive check

Official product descriptions checked on 26 September 2026. These are advertised capabilities, not independently tested accuracy. Missing information is unknown, not evidence a feature is absent.

| Alternative | Relevant overlap | Consequence for our positioning | Open diligence |
| --- | --- | --- | --- |
| Gong | Sales coaching, skill gaps and coaching connected to business outcomes [S5] | Broad call intelligence and longitudinal coaching already exist | Pilot-fit quote, export/embed rights, quality on our calls |
| Avoma | Call scoring, coaching, talk patterns, filler words and topic tracking [S6] | Filler detection and product-feedback extraction alone are not differentiators | Test actionability and correction workflow; confirm total plan cost |
| Revenue.io | Coaching criteria, Salesforce workflows and linking coaching to outcomes [S7] | The closed feedback loop is already an incumbent claim | Integration dependence and suitability outside Salesforce |
| Second Nature | Sales practice and deal coaching [S8] | Personalized practice is also an existing category | How well practice is tied to actual observed behavior |
| Manual manager review | Business-specific judgment and existing trust | Our baseline must beat review effort while preserving quality | Measure current minutes spent and disagreements |
| Transcript plus general-purpose model | Cheap, flexible content feedback | We must show value from audio, continuity and workflow | Compare blind on the same held-out calls |

Avoma's official help page lists Conversation Intelligence at $29/$35 per seat for annual/monthly billing, as an add-on to a base Meeting Assistant plan. This is not the total subscription cost or proof customers will pay us the same amount. [S6]

Potential differentiation to test: an embeddable, manager-calibrated coaching engine for one specific sales motion, with audio evidence, editable rubrics, correction history and validated practice recommendations. None is yet an established moat.

Potential defensibility over time: permissioned domain-specific evaluation examples, useful manager corrections, trusted workflow integrations, and evidence that interventions improve relevant behaviors. Raw data accumulation alone is not a moat. Cross-customer model improvement would require an explicit permitted data use; private customer memory remains isolated by default.

These competitors do not remove the learning value of building. Reuse commodity components where useful and investigate the differences transparently. Lack of usable recordings or trustworthy evaluation is a reason to change the validation plan; lack of paying customers is not a reason to stop this project.

## 6. What the engine should and should not infer

| Dimension | Evidence to collect | Feedback approach |
| --- | --- | --- |
| Fillers and repetitions | Audio-verified occurrences and rate per rep speaking minute | Highlight disruptive clusters, not a zero-filler target |
| Pace and pauses | Timings, speech rate, pause locations and audio quality | Distinguish deliberate space, thinking, customer interruption and connection delay |
| Delivery | Audible behavior in specific excerpts | Describe the behavior; do not infer inner confidence or personality as fact |
| Discovery | Questions, follow-ups, acknowledged needs and buyer responses | Show missed opportunities and effective probing with quotes |
| Offering fit | Link buyer need to a verified offering capability | Detect generic pitching and unsupported promises |
| Objections | Objection, clarification, response and buyer reaction | Coach the response relevant to this stage and context |
| Progression | Agreed next step, owner and timing | Evaluate against the call objective; closing is not expected on every first call |

Important requirement: analyze audio as well as text. Some transcription systems remove fillers by default; AssemblyAI documents an explicit option to retain them. [S9] A polished transcript cannot establish that no fillers occurred. Clean and verbatim views should remain distinguishable.

Proposed feedback object: evidence excerpt and timestamps; observation; why it matters for this call; bounded interpretation and uncertainty; recommended exercise; how to check improvement; manager accept/edit/reject. Unknown or insufficient evidence must be valid outputs. Avoid a universal confidence score and rep rankings based on accent, loudness or speaking speed.

Example only, not an analyzed call: During the pricing explanation, several repeated fillers interrupted otherwise clear sentences. Practise a short pricing explanation with deliberate pauses, then an unscripted objection. Reassess on later pricing conversations. This supports a focused exercise, not a claim that the rep lacks confidence or that practice will guarantee sales.

## 7. Ten-call seed evaluation set

Yes: start with ten human-reviewed calls. This is a calibration set, not statistical validation of production quality.

Selection target: include two or more rep histories, multiple stages, strong and weak examples, noise/overlap and varied English accents where available. Include linked calls from the same deal to test continuity. Label missing stages or outcomes rather than inventing them.

Suggested split: seven calls for rubric development and three untouched for a first blind check. Split by deal or rep where feasible so near-duplicate conversations do not leak across sets. Keep all earlier context for a held-out deal in its held-out bundle. If ten calls cannot meet both coverage and leakage constraints, document this and expand later. Add new unseen calls after tuning.

### Repeat this review card for each recording

- Call reference (secure location, not an audio attachment in Git):
- Company/product context and rubric version:
- Rep ID, role, deal ID, date, stage and intended next step:
- Source, duration, channels, language and audio-quality issues:
- Confirmed speakers and uncertain spans:
- Observations: timestamp range | exact words/audible behavior | dimension | effective/problematic/unclear | explanation:
- Important customer needs and evidence:
- Offering fit or mismatch and evidence:
- Two things the rep did well:
- One or two highest-priority improvements:
- Proposed exercise, duration and success check:
- Known next step/outcome and when it became known:
- What cannot be concluded from this recording:
- Reviewer identity and confidence in each judgment:

Keep the initial coaching review blind to eventual win/loss where possible. Reveal outcomes in a separate retrospective pass to reduce hindsight bias. A win does not prove good behavior and a loss does not prove poor behavior. Ask a second reviewer to independently label at least three calls; record disagreements instead of forcing false certainty.

### Candidate rubric anchors

For each relevant skill: 1 = important missed opportunity with evidence; 2 = partial attempt; 3 = meets this call's objective; 4 = effective adaptation to buyer response. N/A = no opportunity; unknown = insufficient audio/context. Do not average these into a global rep score before validating their usefulness.

### Evaluation dimensions and provisional pilot gates

- Correct rep attribution; unknown is preferable to confident misattribution.
- Filler event precision/recall and timestamp accuracy on manually checked spans.
- Coaching evidence correctness, usefulness, specificity and manager disagreement.
- Speaker/transcript corrections propagate to all affected analysis.
- Manager time per reviewed call and accepted actionable recommendations versus manual baseline.
- Practice completion and behavior change on comparable later calls; conversion remains exploratory until sample size and comparison design support causal claims.

Suggested gates to negotiate, not measured results: every coaching claim has inspectable evidence; no known wrong-rep assignment remains in the pilot release; at least 80% of priority recommendations are accepted or need only minor edits; median manager review time falls by at least 30% versus baseline. Three held-out calls cannot establish reliable percentages; report counts and expand the evaluation before broader release.

### Five-day practice cadence to validate

1. Listen to a marked excerpt; record a concise explanation in the rep's own words.
2. Repeat with deliberate pauses and review the recording.
3. Practise the same explanation for two different customer needs.
4. Add realistic objections and interruptions; do not memorize a single script.
5. Record an unscripted attempt and obtain a manager check.

Then verify the behavior on comparable live calls. The initial product may recommend and track this cadence without building a full roleplay system.

## 8. Open-source and buy-versus-build review

| Component | Candidate | Evidence and constraints | Proposed next step |
| --- | --- | --- | --- |
| Transcription and word alignment | WhisperX | Repository describes transcription, word timings and diarization; BSD-2-Clause code license [S10] | Benchmark filler retention, timestamps, accents and overlap; verify dependency/model licenses separately |
| Speaker segmentation | pyannote.audio | MIT toolkit; pretrained pipeline conditions must also be reviewed [S11] | Compare against source-channel attribution and hosted diarization |
| Hosted transcription | Deepgram or AssemblyAI | Commercial services; feature support and configuration vary [S9, S12] | Use a replaceable provider interface; benchmark rather than select by advertised accuracy |
| Recurring voice identification | pyannoteAI | Commercial voiceprint matching option [S13] | Defer unless metadata is inadequate; test false matches and unknown speakers |
| Acoustic feature extraction | openSMILE | Official docs state commercial products require commercial licensing [S14] | Do not assume free commercial deployment; evaluate alternatives or obtain terms |

Recommendation: self-host the engine by default; allow user-funded speech/model services behind replaceable adapters. Compare local components later when they answer a learning question or deployment need. Own the rubric, evidence model, corrections, memory and interface contracts. Engine hosting and model hosting are separate choices. No supplier is selected and no subscriptions have been purchased.

## 9. Interface recommendation, not a TRD decision

Both an API and MCP adapter are confirmed scope, backed by the same engine. Proposed behavior: submit audio/context, obtain a job reference, inspect status/results, provide speaker corrections and retrieve prior context. MCP exposes the same capabilities to compatible assistants [S15]. Detailed transport, authentication, schema and job design belong in the TRD. A user connects to their own installation; a public repository is not itself a running MCP endpoint.

A dedicated dashboard is deferred. API clients or an MCP host handle clarification and speaker confirmation; the engine returns explicit unresolved states. Stable structured JSON plus a readable report is proposed. We will include a minimal reproducible usage example so no commercial integration is needed to learn or test.

Full-journey analysis also requires explicit deal linkage, product/playbook context, call dates and known outcomes. Audio alone cannot reliably reconstruct missing calls, off-call email exchanges or CRM stage changes. Maintain separate memory for the rep's skills and the deal's facts.

## 10. Versions and product boundaries

| Version | User-visible outcome | Gate before moving on |
| --- | --- | --- |
| Discovery / v0 | PRD, then TRD; reference-call rubric and evaluation design | Requirements and evaluation criteria agreed before implementation |
| v0.1 reproducible baseline | Self-hosted engine, API and MCP; English audio, confirmed speaker mapping, structured evidence-backed feedback and basic user-owned persistence | Same sample succeeds through both interfaces; failures and baseline metrics documented |
| v0.2 measured improvement | Audio delivery features, stronger attribution, difficult-audio cases and systematic provider comparisons | Improvement and regressions measured on held-out examples |
| v0.3 continuity | Richer rep/deal histories, correction propagation, stage-aware comparison and practice tracking | Memory adds value in controlled comparisons without stale-identity leakage |
| Later | Optional voice enrollment, product insights, source adapters and local-model options | Each addition addresses a documented need and has its own evaluation |

In v0.1 retain stable rep/deal IDs and earlier confirmed notes where available, so continuity can be evaluated without promising mature trend analytics. This sequence is proposed, not a unilateral reduction of the founder's full-journey objective.

Future product insights: preserve pain-point evidence now; later deduplicate by account, separate customer statements from salesperson interpretation, attach timestamps and track frequency across distinct accounts. Do not treat one vocal prospect as market-wide demand or turn every objection into a roadmap request.

## 11. Capacity and budget

We do not need arbitrary product restrictions on call duration or monthly volume. We do need expected workloads to size uploads, processing, retries and spend. Technical file ceilings and per-customer quotas, if necessary, should be explicit and configurable. Long calls must not be silently truncated; chunking must preserve speaker continuity and evidence timestamps. High volume can queue when immediate feedback is unnecessary.

Sizing variable: monthly audio minutes = reps × calls per rep per workday × average recorded minutes × workdays. These are assumptions, not limits.

Illustrative volume only: 10 reps × 5 calls × 15 minutes × 22 days = 16,500 minutes/month. At Deepgram's checked pre-recorded Nova-3 monolingual list price of $0.0043/min, one transcription pass would be $70.95, before any multi-channel billing effects, add-ons, retries or other services. Pre-recorded diarization is listed as included. This is not a total product cost or provider commitment. [S12]

Budget buckets:
1. One-time discovery/build: engineering, integration work, human labeling and evaluation.
2. Variable operations: speech processing, audio feature extraction, language-model analysis, memory retrieval, reprocessing, storage and egress.
3. Fixed operations: hosting, database, monitoring, support and security work.
4. Human QA: manager review and calibration time; track separately even if founder-provided.

There is no pricing or monetization workstream. End users bear runtime costs. The founder's own development evaluations may still use paid APIs or local compute; those costs are separate from operating a public service. Record per-experiment costs and support bounded usage; choose any paid experiment budget when an actual run is proposed. No spend is authorized by the illustrative model.

## 12. Next questions and validation plan

1. Are ten real sales recordings available with permission for analysis? What is being sold, and are any calls linked to the same rep/deal? If unavailable, begin with clearly labeled staged examples and later validate on real calls.
2. What is the founder's current coding experience, and which tradeoffs should receive the deepest explanation? This affects teaching pace, not the intended depth of the engine.
3. Resolve the public GitHub repository target. Suggested name: sales-coaching-engine. Creation is not available in the exposed connector; the requested owner is not the connected account.

Working defaults for the PRD: English; recorded-file input; asynchronous execution; structured JSON and a readable report; user-controlled storage; both API and MCP; manager-confirmed speaker mapping; practice recommendations before an interactive roleplay system. Authentication, installation target, provider selection, license and optional voice retention need explicit treatment before release. No customer acquisition is required to proceed.

Optional user research: ask available managers to review the rubric and feedback. Sales outreach, buyer interviews and willingness-to-pay validation are removed as gates. Compare human notes, transcript-only feedback and the eventual audio-aware engine; incumbent trials are optional. No outreach or trials have been started.

PRD follows these answers: personas, problem, boundaries, workflows, metrics, retention/access and acceptance criteria. TRD follows PRD agreement: schemas, jobs, source adapters, provider comparison, evidence pipeline, identity correction, memory rules, tenant isolation, deletion, evaluation, costs and deployment. Neither is finalized now.

## 13. Sources and evidence limits

All accessed 26 September 2026. Research is an initial decision memo, not exhaustive market diligence. Vendor descriptions require pilot verification; prices require reconfirmation before purchase.

- S1 — McKinsey, B2B Pulse 2024 (published 12 September 2024): https://www.mckinsey.com/capabilities/growth-marketing-and-sales/our-insights/five-fundamental-truths-how-b2b-winners-keep-growing
- S2 — Twilio, dual-channel recording: https://www.twilio.com/docs/flex/developer/insights/enable-dual-channel-recordings
- S3 — Zoom, computer recording and participant audio: https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0076922
- S4 — Google Meet, TranscriptEntry: https://developers.google.com/workspace/meet/api/reference/rest/v2/conferenceRecords.transcripts.entries
- S5 — Gong, sales coaching: https://www.gong.io/sales-coaching-software
- S6 — Avoma, capabilities and add-on pricing: https://www.avoma.com/conversation-intelligence and https://help.avoma.com/avoma-pricing-recorder-seats-free-users-add-ons
- S7 — Revenue.io, coaching and outcomes: https://www.revenue.io/sales-enablement-training and https://www.revenue.io/ai-sales-coaching
- S8 — Second Nature, roleplay and Deal Coach: https://secondnature.ai/
- S9 — AssemblyAI, filler preservation: https://www.assemblyai.com/docs/pre-recorded-audio/include-filler-words
- S10 — WhisperX repository: https://github.com/m-bain/whisperX
- S11 — pyannote.audio repository: https://github.com/pyannote/pyannote-audio
- S12 — Deepgram pricing: https://deepgram.com/pricing
- S13 — pyannoteAI recurring-speaker tutorial, initial discovery source: https://www.pyannote.ai/blog/speaker-identification-system-recurring-meetings
- S14 — openSMILE license documentation: https://audeering.github.io/opensmile-python/
- S15 — MCP architecture: https://github.com/modelcontextprotocol/docs/blob/main/docs/concepts/architecture.mdx

## 14. Decision history

- v0.1: broad audio-coaching brief covering sales and interviews, initial questions and market hypotheses.
- v0.2: sales chosen first; manager workflow, audio evidence, source identity, seed evaluation, competitor/open-source review, phased delivery and cost model documented. API is a recommendation pending buyer validation. Remote Git creation/push remains outstanding.
- v0.3: founder confirmed learning in public, a public open-source repository, self-hosting and user-funded operation. Both API and MCP are required. Commercial validation and pricing are no longer gates. Added an accuracy scorecard, controlled experiments, public documentation plan and revised milestones. Remote publication remains outstanding; this revision is documentation only.
