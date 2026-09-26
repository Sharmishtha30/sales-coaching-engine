# Evaluation protocol v0.1

## Evidence levels

| Check | Current evidence | What it cannot establish |
| --- | --- | --- |
| Staged fixture | Authored transcript/timings and expected filler count | ASR or acoustic accuracy |
| Provider contract | Mocked HTTP request/response tests | Real-service availability, cost or recognition quality |
| API/MCP | Actual local clients and server/process execution | Performance at scale or remote-host compatibility |
| Human coaching review | Template supplied; no completed real reviews | Manager acceptance or sales improvement |

## Seed cases

| Case | Reference expectation | Purpose |
| --- | --- | --- |
| discovery | Speaker A has 3 fillers: `um` in u1, `uh` and `um` in u3; B has none | Basic attribution and evidence |
| followup | Speaker A has no recognized fillers; does not claim the unavailable integration exists | Continuity and future semantic review |
| casual | Not a sales call; live semantic provider should identify other/uncertain | Future category-abstention check; rules mode deliberately says uncertain |

These references are authored alongside fixtures and are development cases. They are not a held-out golden set. Timings are schematic, not phonetic annotations. Tests do not convert them into accuracy percentages.

## Obtaining real staged audio

Use `examples/staged-scripts.md`. Two consenting participants can record the dialogue naturally with their own voices. Do not publish the recording merely because the script is public. Save it outside Git under your permitted audio directory. Retain the original recording and create a human verbatim transcript independently of ASR output.

Create seven development and three held-out recordings when possible; vary call stages and conditions. Keep linked deal histories together in one split. Do not edit the held-out expectations after seeing output to inflate results. If an error informs a fix, use fresh examples for the next independent check.

## Human annotation card

Call ID; permission/source; date; rep/deal IDs; product facts; audio conditions; confirmed speaker labels; timestamped words/fillers; strong behaviors; missed opportunities; recommendation and uncertainty; actual outcome if known. Review content before revealing eventual win/loss. Have a second reviewer label a subset and retain disagreement.

## Metrics

- ASR: substitutions + deletions + insertions divided by reference words (WER); separately inspect product names, prices and fillers.
- Speaker attribution: mislabeled spans and unresolved coverage; for future biometrics, false matches and missed matches.
- Filler precision = correctly detected events / detected events; recall = correctly detected events / human-labeled events. Define timestamp tolerance before comparison.
- Coaching: supported claims, relevant recommendations and manager corrections, reporting counts/denominators. Use a rubric rather than an LLM judging its own output without calibration.
- Operations: end-to-end time, provider usage, cost per audio hour, failures and retries.
- Memory: correction/deletion propagation and retrieval of facts available before the call; prohibit future-outcome leakage.

Report no universal accuracy score. Confidence intervals and broader real-call sampling come after enough independent examples exist.

## Experiment template

```
ID/date:
Question and hypothesis:
Baseline and isolated change:
Dataset/split and permissions:
Model/provider versions and settings:
Rubric/code commit:
Metrics with counts/denominators:
Cost and latency:
Failure examples and regressions:
Decision and next question:
```
