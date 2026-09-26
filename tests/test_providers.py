import json
import httpx
import pytest
from sales_coach.providers import Deepgram, ClaudeCoach, ProviderError
from sales_coach.fixtures import fixture


def test_deepgram_contract(settings, tmp_path):
    settings.deepgram_key = "test-only"
    path = tmp_path / "test.wav"
    path.write_bytes(b"RIFF-not-a-real-recording")
    def handle(request):
        assert request.headers["Authorization"] == "Token test-only"
        assert request.url.params["filler_words"] == "true"
        assert request.url.params["diarize_model"] == "latest"
        assert request.read() == path.read_bytes()
        return httpx.Response(200, json={"metadata": {"request_id": "test", "duration": 2},
            "results": {"utterances": [{"speaker": 0, "start": 0, "end": 2, "transcript": "Um hello.",
            "words": [{"word": "um", "start": 0, "end": 0.3}, {"word": "hello", "start": 0.5, "end": 2}]}]}})
    result = Deepgram(settings, httpx.MockTransport(handle)).transcribe(path)
    assert result.source == "deepgram" and result.utterances[0].speaker == "0"
    assert len(result.utterances[0].words) == 2


@pytest.mark.parametrize("evidence,valid", [(["u1"], True), (["fake"], False), (["u2"], False)])
def test_model_evidence_validation(settings, evidence, valid):
    settings.anthropic_key, settings.anthropic_model = "test-only", "configured-model"
    t, c = fixture("discovery")
    def handle(request):
        body = json.loads(request.content)
        assert "untrusted" in body["system"] and body["model"] == "configured-model"
        draft = {"category": "sales", "stage": "discovery", "findings": [{
            "dimension": "discovery", "observation": "An opening question was asked.",
            "recommendation": "Follow up on the time cost.", "evidence_ids": evidence,
            "uncertainty": "Only one call."}]}
        return httpx.Response(200, json={"stop_reason": "end_turn", "content": [{"type": "text", "text": json.dumps(draft)}]})
    coach = ClaudeCoach(settings, httpx.MockTransport(handle))
    if valid:
        result = coach.coach(t, c.model_dump(mode="json"), {"speaker": "A"})
        assert result["findings"][0]["evidence"][0]["quote"] == t.utterances[0].text
    else:
        with pytest.raises(ProviderError):
            coach.coach(t, c.model_dump(mode="json"), {"speaker": "A"})


def test_empty_audio_response_fails(settings, tmp_path):
    settings.deepgram_key = "test"
    path = tmp_path / "test.wav"
    path.write_bytes(b"RIFF")
    provider = Deepgram(settings, httpx.MockTransport(lambda _: httpx.Response(200, json={"results": {}})))
    with pytest.raises(ProviderError, match="no_speech"):
        provider.transcribe(path)
