import re
from .schemas import ChatRequest, SafetyStatus

EMERGENCY = re.compile(r"\b(chest pain|can't breathe|cannot breathe|severe bleeding|unconscious|suicid|stroke|seizure|worst headache|anaphyla)\b", re.I)
COMPLEX = re.compile(r"\b(cancer|kidney failure|heart failure|chemotherapy|transplant)\b", re.I)

def triage(req: ChatRequest) -> tuple[SafetyStatus, str | None]:
    c = req.context
    if EMERGENCY.search(req.message):
        return SafetyStatus.ESCALATE, "Possible emergency warning sign: contact local emergency services now."
    if c.pregnancy.value == "pregnant" or c.immunocompromised:
        return SafetyStatus.ESCALATE, "This risk context needs advice from a qualified clinician."
    if c.age is not None and (c.age < 18 or c.age >= 65):
        return SafetyStatus.ESCALATE, "This service supports lower-risk adults aged 18–64 only."
    if c.duration_days is not None and c.duration_days > 7:
        return SafetyStatus.ESCALATE, "Persistent symptoms need clinical assessment."
    if (c.severity or "").lower() == "severe" or COMPLEX.search(req.message):
        return SafetyStatus.ESCALATE, "Severe or complex concerns need prompt clinical assessment."
    return SafetyStatus.SUPPORTED, None
