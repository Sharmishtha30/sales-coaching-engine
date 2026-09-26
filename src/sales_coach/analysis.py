import re

FILLERS = {"um", "umm", "uh", "uhh", "erm", "er", "hmm"}


def normalized(text):
    return re.sub(r"[^a-z]", "", text.lower())


def span_duration(utterances):
    intervals = sorted((u.start, u.end) for u in utterances)
    merged = []
    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(end, merged[-1][1])
        else:
            merged.append([start, end])
    return sum(end - start for start, end in merged)


def delivery(transcript, speaker):
    turns = [u for u in transcript.utterances if u.speaker == speaker]
    seconds = span_duration(turns)
    word_count = sum(len(u.words) if u.words else len(u.text.split()) for u in turns)
    events = []
    for turn in turns:
        if turn.words:
            for word in turn.words:
                if normalized(word.text) in FILLERS:
                    events.append({"utterance_id": turn.id, "start": word.start, "end": word.end,
                                   "token": word.text, "timing_precision": "word"})
        else:
            for token in turn.text.split():
                if normalized(token) in FILLERS:
                    events.append({"utterance_id": turn.id, "start": turn.start, "end": turn.end,
                                   "token": token, "timing_precision": "utterance_only"})
    return {"rep_utterance_span_seconds": round(seconds, 3), "recognized_word_count": word_count,
            "recognized_filler_count": len(events), "filler_events": events,
            "fillers_per_utterance_minute": round(len(events) * 60 / seconds, 3) if seconds else None,
            "words_per_utterance_minute": round(word_count * 60 / seconds, 3) if seconds else None,
            "denominator": "union of rep utterance spans; includes internal pauses, not phonated time"}


def rule_findings(transcript, metrics):
    if not metrics["filler_events"]:
        return []
    index = {u.id: u for u in transcript.utterances}
    ids = list(dict.fromkeys(e["utterance_id"] for e in metrics["filler_events"]))[:3]
    return [{"dimension": "delivery",
        "observation": f"The transcript contains {metrics['recognized_filler_count']} recognized filler tokens in the confirmed rep's turns.",
        "recommendation": "Listen to these excerpts. If fillers disrupt the explanation, rehearse it aloud with deliberate pauses, then try an unscripted objection. Compare a later call with the same objective.",
        "uncertainty": "Recognized fillers are not proof of low confidence or poor selling. Verify against the audio; ASR can omit or invent words.",
        "evidence": [{"utterance_id": uid, "start": index[uid].start, "end": index[uid].end,
                      "speaker": index[uid].speaker, "quote": index[uid].text} for uid in ids]}]


def report(call):
    result = call.get("result")
    if result is None:
        return f"Call {call['id']} — {call['status']}. Confirm speakers or inspect the error before requesting a report."
    lines = [f"# Sales coaching — {call['identity']['rep_name']}",
        f"Call: {call['id']} | Source: {call['transcript']['source']} | Mode: {result['coaching_mode']}",
        f"Recognized fillers: {result['delivery']['recognized_filler_count']}",
        ""]
    for finding in result["findings"]:
        lines.extend([f"## {finding['dimension']}", finding["observation"], finding["recommendation"],
                      f"Uncertainty: {finding['uncertainty']}"])
        for e in finding["evidence"]:
            lines.append(f"- [{e['start']:.2f}–{e['end']:.2f}s] {e['quote']}")
    lines.extend(["", "## Limitations", *[f"- {x}" for x in result["limitations"]]])
    return "\n".join(lines)
