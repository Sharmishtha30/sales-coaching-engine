"""Authored transcripts. Timings are staged, not measured from audio."""
from .models import Transcript, Utterance, CallContext

SCRIPTS = {
    "discovery": [
        ("A", 0, 8, "Hello, um, I am Maya from FlowDesk. What is slowing your team down today?"),
        ("B", 8, 16, "We copy customer requests between email and spreadsheets. We lose about two hours every day."),
        ("A", 16, 24, "Uh, our product has dashboards and automation. Um, it costs eighty dollars per user."),
        ("B", 24, 30, "Does it connect to our existing helpdesk? We cannot replace that system."),
        ("A", 30, 38, "I need to check that integration. Could you tell me which helpdesk you use?"),
        ("B", 38, 44, "We use HelpBox. Can you send me the details?"),
        ("A", 44, 50, "Yes, I will check the integration and email you tomorrow.")
    ],
    "followup": [
        ("A", 0, 9, "Last time you mentioned two hours of copying requests each day. Is that still the main issue?"),
        ("B", 9, 15, "Yes, and our manager needs to see requests that have not been assigned."),
        ("A", 15, 25, "The assignment dashboard can show that. HelpBox integration is not available yet, so I cannot promise to remove the copying work."),
        ("B", 25, 32, "Then we should wait. The integration matters more than another dashboard."),
        ("A", 32, 41, "Understood. May I contact you if that integration becomes available? I will record this requirement for our product team."),
        ("B", 41, 44, "Yes, that would help.")
    ],
    "casual": [
        ("A", 0, 7, "Did you enjoy the walk yesterday? The weather was lovely."),
        ("B", 7, 13, "Yes. Let us meet at the park again on Sunday."),
        ("A", 13, 18, "Sounds good. I will bring some coffee.")
    ]
}


def fixture(name):
    if name not in SCRIPTS:
        raise ValueError("Unknown fixture; choose discovery, followup or casual")
    transcript = Transcript(source="staged_fixture", utterances=[
        Utterance(id=f"u{i+1}", speaker=s, start=a, end=b, text=t)
        for i, (s, a, b, t) in enumerate(SCRIPTS[name])],
        provider_metadata={"fixture": name, "timings": "authored utterance timings; no audio was transcribed"})
    day = 2 if name == "followup" else 1
    context = CallContext(deal_id="example-helpbox", occurred_at=f"2026-09-{day:02d}T10:00:00Z",
        stage="discovery" if name != "casual" else "unknown",
        call_goal="Understand the buyer's workflow and agree an appropriate next step.",
        product_context="Fictional FlowDesk: assignment dashboards, $80/user. HelpBox integration is not available. Do not promise it.")
    return transcript, context
