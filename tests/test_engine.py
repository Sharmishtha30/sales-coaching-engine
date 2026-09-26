import io
import time
import wave
import pytest
from sales_coach.engine import Engine
from sales_coach.models import Confirmation, Transcript, Utterance, CallContext
from sales_coach.analysis import delivery
from sales_coach.store import Conflict
from sales_coach.fixtures import fixture


def confirm(engine, call, rep_id="maya", speaker="A"):
    return engine.confirm(call["id"], Confirmation(rep_id=rep_id, rep_name=rep_id,
        speaker=speaker, expected_revision=call["revision"]), background=False)


def wait(engine, call_id):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        call = engine.get(call_id)
        if call["status"] not in {"queued", "transcribing", "analyzing"}:
            return call
        time.sleep(0.01)
    raise AssertionError("Timed out")


def wav_bytes():
    output = io.BytesIO()
    with wave.open(output, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(8000)
        out.writeframes(b"\x00\x00" * 800)
    return output.getvalue()


def test_staged_counts_and_truthfulness(engine):
    call = engine.submit_fixture("discovery")
    assert call["status"] == "needs_confirmation" and call["result"] is None
    assert call["identity"] is None
    done = confirm(engine, call)
    assert done["status"] == "completed"
    assert done["result"]["delivery"]["recognized_filler_count"] == 3
    assert done["result"]["category"] == "uncertain"
    assert done["result"]["coaching_mode"] == "staged_rules_only"
    assert done["result"]["findings"][0]["evidence"][0]["quote"] == call["transcript"]["utterances"][0]["text"]


def test_history_corrections_deletion_and_chronology(engine):
    first = confirm(engine, engine.submit_fixture("discovery"))
    second = confirm(engine, engine.submit_fixture("followup"))
    assert [c["call_id"] for c in second["prior_calls"]] == [first["id"]]
    assert not engine.get(first["id"])["prior_calls"]
    reassigned = confirm(engine, first, rep_id="someone-else", speaker="B")
    assert reassigned["result"]["delivery"]["recognized_filler_count"] == 0
    assert len(engine.history("maya")) == 1
    assert engine.get(second["id"])["prior_calls"] == []
    engine.delete(second["id"])
    assert engine.history("maya") == []
    with pytest.raises(KeyError):
        engine.get(second["id"])


def test_revision_and_speaker_checks(engine):
    call = engine.submit_fixture("discovery")
    with pytest.raises(ValueError, match="does not exist"):
        confirm(engine, call, speaker="invented")
    confirm(engine, call)
    with pytest.raises(Conflict):
        confirm(engine, call)


def test_unknown_fixture_and_path_escape(engine, tmp_path):
    with pytest.raises(ValueError):
        engine.submit_fixture("../../etc/passwd")
    private = tmp_path / "private.wav"
    private.write_bytes(wav_bytes())
    with pytest.raises(ValueError, match="COACH_AUDIO_ROOT"):
        engine.submit_path(str(private), CallContext())
    engine.settings.audio_root.mkdir()
    (engine.settings.audio_root / "escape.wav").symlink_to(private)
    with pytest.raises(ValueError, match="COACH_AUDIO_ROOT"):
        engine.submit_path(str(engine.settings.audio_root / "escape.wav"), CallContext())


def test_missing_key_invalid_media_and_size(engine):
    with pytest.raises(ValueError, match="DEEPGRAM_API_KEY"):
        engine.submit_audio(wav_bytes(), "call.wav", CallContext())
    engine.settings.deepgram_key = "fake"
    with pytest.raises(ValueError, match="Unsupported"):
        engine.submit_audio(b"not audio", "call.wav", CallContext())
    engine.settings.max_upload_bytes = 10
    with pytest.raises(ValueError, match="byte limit"):
        engine.submit_audio(wav_bytes(), "call.wav", CallContext())


def test_audio_job_and_deletion(engine):
    engine.settings.deepgram_key = "fake"
    class Stub:
        def transcribe(self, path):
            transcript, _ = fixture("discovery")
            return transcript.model_copy(update={"source": "deepgram"})
    engine.transcriber = Stub()
    created = engine.submit_audio(wav_bytes(), "call.wav", CallContext())
    call = wait(engine, created["id"])
    assert call["status"] == "needs_confirmation"
    done = confirm(engine, call)
    assert done["result"]["coaching_mode"] == "rules_only"
    path, _ = engine.media(call["id"])
    assert path.exists()
    engine.delete(call["id"])
    assert not path.exists()


def test_errors_do_not_leak_and_explicit_retry(engine):
    engine.settings.deepgram_key = "fake"
    class Bad:
        def transcribe(self, path):
            raise RuntimeError("secret credential and transcript must not leak")
    engine.transcriber = Bad()
    created = engine.submit_audio(wav_bytes(), "call.wav", CallContext())
    call = wait(engine, created["id"])
    assert call["status"] == "failed" and call["error"] == "processing_failed"
    assert "secret credential" not in str(call)
    retried = engine.retry(call["id"], call["revision"])
    assert retried["status"] == "queued"
    assert wait(engine, call["id"])["status"] == "failed"


def test_persistence_and_restart(settings):
    a = Engine(settings)
    call = a.submit_fixture("discovery")
    record = a.store.get(call["id"])
    record["status"] = "analyzing"
    a.store.save(record)
    with pytest.raises(RuntimeError, match="Another engine"):
        Engine(settings)
    a.close()
    b = Engine(settings)
    try:
        assert b.get(call["id"])["error"] == "interrupted_restart_explicit_retry_required"
    finally:
        b.close()


def test_overlapping_spans_and_no_like_false_positives():
    t = Transcript(source="staged_fixture", utterances=[
        Utterance(id="1", speaker="A", start=0, end=10, text="I like this so much"),
        Utterance(id="2", speaker="A", start=5, end=15, text="um yes")])
    d = delivery(t, "A")
    assert d["rep_utterance_span_seconds"] == 15
    assert d["recognized_filler_count"] == 1
    assert d["fillers_per_utterance_minute"] == 4


def test_bad_timing_rejected():
    with pytest.raises(ValueError):
        Utterance(id="1", speaker="A", start=5, end=2, text="wrong")
    with pytest.raises(ValueError):
        CallContext(occurred_at="2026-09-01T12:00:00")


def test_live_semantic_path_and_non_sales_abstention(engine):
    engine.settings.anthropic_key = "fake"
    engine.settings.anthropic_model = "test-model"
    class Coach:
        calls = 0
        def coach(self, transcript, context, identity):
            self.calls += 1
            return {"category": "other", "stage": "unknown", "findings": [], "model": "test-model", "usage": {}}
    engine.coach = Coach()
    staged = engine.submit_fixture("discovery")
    confirm(engine, staged)
    assert engine.coach.calls == 0  # demo must not spend even if keys exist
    live = engine.submit_fixture("discovery")
    record = engine.store.get(live["id"])
    record["transcript"]["source"] = "deepgram"
    saved = engine.store.save(record)
    result = confirm(engine, saved)
    assert engine.coach.calls == 1
    assert result["result"]["category"] == "other"
    assert result["result"]["findings"] == []
    assert result["prior_calls"] == []  # real and staged histories cannot mix


def test_coaching_limit_explicitly_skips_without_truncation(engine):
    engine.settings.anthropic_key = "fake"
    engine.settings.anthropic_model = "test"
    engine.settings.max_coaching_chars = 10
    call = engine.submit_fixture("discovery")
    record = engine.store.get(call["id"])
    record["transcript"]["source"] = "deepgram"
    record = engine.store.save(record)
    result = confirm(engine, record)
    assert result["result"]["coaching_mode"] == "rules_only_context_limit"
    assert len(result["transcript"]["utterances"]) == 7


def test_active_job_capacity(engine):
    engine.settings.max_active_jobs = 1
    call = engine.submit_fixture("discovery")
    active = engine.store.get(call["id"])
    active["status"] = "analyzing"
    engine.store.save(active)
    other = engine.submit_fixture("discovery")
    with pytest.raises(Conflict, match="limit"):
        confirm(engine, other)


def test_invalid_coach_result_fails_without_stale_report(engine):
    engine.settings.anthropic_key = "fake"
    engine.settings.anthropic_model = "test"
    call = confirm(engine, engine.submit_fixture("discovery"))
    record = engine.store.get(call["id"])
    record["transcript"]["source"] = "deepgram"
    record = engine.store.save(record)
    class Bad:
        def coach(self, *args):
            from sales_coach.providers import ProviderError
            raise ProviderError("coaching_invalid_evidence")
    engine.coach = Bad()
    result = confirm(engine, record)
    assert result["status"] == "failed"
    assert result["result"] is None
    assert engine.history("maya") == []
