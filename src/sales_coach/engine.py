import json
import mimetypes
import threading
import uuid
import fcntl
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import httpx
from pydantic import ValidationError
from . import __version__
from .analysis import delivery, rule_findings, report
from .config import Settings
from .fixtures import fixture
from .models import Transcript, CallContext, Confirmation
from .providers import Deepgram, ClaudeCoach, ProviderError
from .store import Store, Conflict

ACTIVE = {"queued", "transcribing", "analyzing"}
SUFFIXES = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm", ".mp4"}


def audio_signature(data):
    return (data.startswith((b"RIFF", b"ID3", b"OggS", b"fLaC", b"\x1aE\xdf\xa3"))
            or (len(data) > 8 and data[4:8] == b"ftyp")
            or (len(data) > 2 and data[0] == 0xff and data[1] & 0xe0 == 0xe0))


class Engine:
    def __init__(self, settings=None, transcriber=None, coach=None):
        self.settings = settings or Settings()
        self.settings.data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._lease = (self.settings.data_dir / ".process.lock").open("a")
        try:
            fcntl.flock(self._lease.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self._lease.close()
            raise RuntimeError("Another engine is using this data directory; use a separate directory") from None
        self.uploads = self.settings.data_dir / "uploads"
        self.uploads.mkdir(exist_ok=True, mode=0o700)
        self.store = Store(self.settings.data_dir / "calls.sqlite3")
        self.transcriber = transcriber or Deepgram(self.settings)
        self.coach = coach or ClaudeCoach(self.settings)
        self.lock = threading.RLock()
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="coach")
        # One engine process per data directory is the supported deployment.
        for call in self.store.all():
            if call["status"] in ACTIVE:
                call.update(status="failed", error="interrupted_restart_explicit_retry_required", result=None)
                self.store.save(call)

    def close(self):
        self.pool.shutdown(wait=True, cancel_futures=False)
        if not self._lease.closed:
            fcntl.flock(self._lease.fileno(), fcntl.LOCK_UN)
            self._lease.close()

    def _capacity(self):
        if sum(c["status"] in ACTIVE for c in self.store.all()) >= self.settings.max_active_jobs:
            raise Conflict("Active job limit reached; retry after existing jobs finish")

    def _new(self, context, transcript=None, audio_path=None):
        call = {"id": str(uuid.uuid4()), "revision": 0,
            "created_at": datetime.now(timezone.utc).isoformat(), "context": context.model_dump(mode="json"),
            "status": "needs_confirmation" if transcript else "queued", "identity": None,
            "transcript": transcript.model_dump() if transcript else None,
            "audio_path": str(audio_path) if audio_path else None, "result": None, "error": None}
        self.store.create(call)
        return call

    def submit_fixture(self, name):
        transcript, context = fixture(name)
        return self.public(self._new(context, transcript))

    def submit_audio(self, data: bytes, filename: str, context: CallContext):
        if not self.settings.deepgram_key:
            raise ValueError("Set DEEPGRAM_API_KEY before submitting live audio")
        suffix = Path(filename).suffix.lower()
        if suffix not in SUFFIXES or not data or not audio_signature(data):
            raise ValueError("Unsupported or empty media; supported: WAV, MP3, M4A, OGG, FLAC, WebM, MP4")
        if len(data) > self.settings.max_upload_bytes:
            raise ValueError("Upload exceeds configured byte limit; increase COACH_MAX_UPLOAD_MB if appropriate")
        path = self.uploads / (uuid.uuid4().hex + suffix)
        with path.open("xb") as out:
            out.write(data)
        path.chmod(0o600)
        try:
            with self.lock:
                self._capacity()
                call = self._new(context, audio_path=path)
        except Exception:
            path.unlink(missing_ok=True)
            raise
        self.pool.submit(self._transcribe, call["id"])
        return self.public(call)

    def submit_path(self, path: str, context: CallContext):
        resolved = Path(path).expanduser().resolve()
        if not resolved.is_relative_to(self.settings.audio_root) or not resolved.is_file():
            raise ValueError("Audio must be a regular file inside COACH_AUDIO_ROOT")
        with resolved.open("rb") as audio:
            data = audio.read(self.settings.max_upload_bytes + 1)
        return self.submit_audio(data, resolved.name, context)

    def _transcribe(self, call_id):
        try:
            with self.lock:
                call = self.store.get(call_id)
                call.update(status="transcribing", error=None)
                call = self.store.save(call)
            transcript = self.transcriber.transcribe(Path(call["audio_path"]))
            with self.lock:
                call.update(transcript=transcript.model_dump(), status="needs_confirmation")
                self.store.save(call)
        except Exception as exc:
            self._fail(call_id, exc)

    def _fail(self, call_id, exc):
        # Never persist provider response bodies/headers or arbitrary exception messages.
        if isinstance(exc, ProviderError):
            code = str(exc)
        elif isinstance(exc, httpx.HTTPStatusError):
            code = f"provider_http_{exc.response.status_code}"
        elif isinstance(exc, httpx.TimeoutException):
            code = "provider_timeout_no_automatic_retry"
        elif isinstance(exc, (ValidationError, json.JSONDecodeError)):
            code = "provider_invalid_response"
        else:
            code = "processing_failed"
        with self.lock:
            try:
                call = self.store.get(call_id)
                call.update(status="failed", error=code, result=None)
                self.store.save(call)
            except (KeyError, Conflict):
                pass

    def confirm(self, call_id, confirmation: Confirmation, background=True):
        with self.lock:
            call = self.store.get(call_id)
            if call["revision"] != confirmation.expected_revision:
                raise Conflict("Stale revision: fetch the latest call before confirming")
            if call["status"] in ACTIVE or not call["transcript"]:
                raise Conflict("Wait for transcription or analysis to finish")
            self._capacity()
            labels = {u["speaker"] for u in call["transcript"]["utterances"]}
            if confirmation.speaker not in labels:
                raise ValueError("Speaker label does not exist in this transcript")
            call["identity"] = confirmation.model_dump(exclude={"expected_revision"})
            call.update(status="analyzing", result=None, error=None)
            call = self.store.save(call)
        if background:
            self.pool.submit(self._analyze, call_id)
        else:
            self._analyze(call_id)
        return self.get(call_id)

    def _analyze(self, call_id):
        try:
            call = self.store.get(call_id)
            transcript = Transcript.model_validate(call["transcript"])
            metrics = delivery(transcript, call["identity"]["speaker"])
            semantic = None
            limitations = ["Filler counts depend on transcription and are not a confidence score.",
                "Rates use utterance spans, not measured vocal activity. No acoustic emotion inference.",
                "History compares observations; it does not demonstrate causal improvement.",
                "Voiceprints and automatic cross-call voice recognition are not implemented."]
            if transcript.source == "staged_fixture":
                mode = "staged_rules_only"
                limitations.append("Staged transcript and timings: no speech recognition or acoustic accuracy was tested.")
            elif self.settings.anthropic_key or self.settings.anthropic_model:
                if len(json.dumps({"transcript": call["transcript"], "context": call["context"]})) > self.settings.max_coaching_chars:
                    mode = "rules_only_context_limit"
                    limitations.append("Semantic coaching skipped: input exceeds COACH_MAX_COACHING_CHARS. Audio/transcript not truncated.")
                else:
                    semantic = self.coach.coach(transcript, call["context"], call["identity"])
                    mode = "claude_with_rules"
            else:
                mode = "rules_only"
                limitations.append("No language model configured: category, sales fit and objections were not assessed.")
            call["result"] = {"schema_version": "1", "engine_version": __version__,
                "coaching_mode": mode, "category": semantic["category"] if semantic else "uncertain",
                "stage": semantic["stage"] if semantic else call["context"]["stage"],
                "stage_source": "model_inference" if semantic else "provided_context",
                "delivery": metrics,
                "findings": ([] if semantic and semantic["category"] != "sales" else
                    rule_findings(transcript, metrics) + (semantic["findings"] if semantic else [])),
                "semantic_provider": {k: semantic[k] for k in ("model", "usage")} if semantic else None,
                "limitations": limitations}
            call.update(status="completed", error=None)
            with self.lock:
                self.store.save(call)
        except Exception as exc:
            self._fail(call_id, exc)

    def retry(self, call_id, expected_revision):
        with self.lock:
            call = self.store.get(call_id)
            if call["revision"] != expected_revision or call["status"] != "failed":
                raise Conflict("Retry requires the current revision of a failed call")
            self._capacity()
            if call["transcript"] and call["identity"]:
                call.update(status="analyzing", error=None)
                work = self._analyze
            elif call["audio_path"]:
                call.update(status="queued", error=None)
                work = self._transcribe
            else:
                raise Conflict("No retryable input")
            call = self.store.save(call)
        self.pool.submit(work, call_id)
        return self.public(call)

    def history(self, rep_id):
        calls = [c for c in self.store.all() if c["status"] == "completed" and c["identity"]
                 and c["identity"]["rep_id"] == rep_id]
        calls.sort(key=lambda c: (c["context"]["occurred_at"], c["created_at"]))
        return [{"call_id": c["id"], "occurred_at": c["context"]["occurred_at"],
                 "deal_id": c["context"]["deal_id"], "stage": c["context"]["stage"],
                 "source": c["transcript"]["source"], "delivery": c["result"]["delivery"]} for c in calls]

    def get(self, call_id):
        call = self.store.get(call_id)
        result = self.public(call)
        if call["status"] == "completed":
            result["prior_calls"] = [h for h in self.history(call["identity"]["rep_id"])
                if h["call_id"] != call_id and h["occurred_at"] < call["context"]["occurred_at"]
                and h["source"] == call["transcript"]["source"]]
        return result

    @staticmethod
    def public(call):
        return {k: v for k, v in call.items() if k != "audio_path"}

    def report(self, call_id):
        return report(self.store.get(call_id))

    def media(self, call_id):
        call = self.store.get(call_id)
        if not call["audio_path"]:
            raise ValueError("Staged transcript has no recorded audio")
        path = Path(call["audio_path"])
        return path, mimetypes.guess_type(path.name)[0] or "application/octet-stream"

    def delete(self, call_id):
        with self.lock:
            call = self.store.get(call_id)
            if call["status"] in ACTIVE:
                raise Conflict("Wait for active processing before deleting")
            call = self.store.delete(call_id)
            if call["audio_path"]:
                Path(call["audio_path"]).unlink(missing_ok=True)
        return {"deleted": call_id, "scope": "local record and media only; provider retention is separate"}
