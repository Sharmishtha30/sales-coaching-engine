from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Word(Strict):
    text: str = Field(min_length=1, max_length=200)
    start: float = Field(ge=0)
    end: float = Field(ge=0)

    @model_validator(mode="after")
    def timing(self):
        if self.end < self.start:
            raise ValueError("Word end precedes start")
        return self


class Utterance(Strict):
    id: str = Field(min_length=1, max_length=80)
    speaker: str = Field(min_length=1, max_length=80)
    start: float = Field(ge=0)
    end: float = Field(ge=0)
    text: str = Field(min_length=1, max_length=30000)
    words: list[Word] = Field(default_factory=list, max_length=10000)

    @model_validator(mode="after")
    def timing(self):
        if self.end <= self.start:
            raise ValueError("Utterance must have positive duration")
        previous = self.start
        for word in self.words:
            if word.start < self.start or word.end > self.end + 0.01 or word.start < previous:
                raise ValueError("Invalid or unordered word timing")
            previous = word.start
        return self


class Transcript(Strict):
    source: Literal["staged_fixture", "deepgram"]
    utterances: list[Utterance] = Field(min_length=1, max_length=20000)
    provider_metadata: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def ids(self):
        if len({u.id for u in self.utterances}) != len(self.utterances):
            raise ValueError("Duplicate utterance IDs")
        if any(a.start > b.start for a, b in zip(self.utterances, self.utterances[1:])):
            raise ValueError("Utterances must be ordered by start time")
        return self


class CallContext(Strict):
    deal_id: str | None = Field(default=None, max_length=100)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    stage: Literal["unknown", "discovery", "demo", "negotiation", "closing"] = "unknown"
    product_context: str = Field(default="", max_length=20000)
    call_goal: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def timezone(self):
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must include a timezone")
        self.occurred_at = self.occurred_at.astimezone(timezone.utc)
        return self


class Confirmation(Strict):
    rep_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    rep_name: str = Field(min_length=1, max_length=100)
    speaker: str = Field(min_length=1, max_length=80)
    expected_revision: int = Field(ge=0)


class FindingDraft(Strict):
    dimension: Literal["discovery", "offering_fit", "objections", "next_steps", "delivery"]
    observation: str = Field(min_length=1, max_length=1200)
    recommendation: str = Field(min_length=1, max_length=1200)
    evidence_ids: list[str] = Field(min_length=1, max_length=6)
    uncertainty: str = Field(min_length=1, max_length=500)


class CoachingDraft(Strict):
    category: Literal["sales", "other", "uncertain"]
    stage: Literal["unknown", "discovery", "demo", "negotiation", "closing"]
    findings: list[FindingDraft] = Field(default_factory=list, max_length=6)
