from fastapi.testclient import TestClient
from medicobuddy.api import app
client=TestClient(app)
def payload(message="mild headache"):
    return {"message":message,"thread_id":"thread-123456","context":{"pregnancy":"not_pregnant"}}
def test_liveness_is_not_readiness():
    assert client.get("/health/live").json()=={"live":True}
    body=client.get("/health/ready").json(); assert body["ready"] is False; assert body["dependencies"]["vector"]["status"]=="NOT CONFIGURED"
def test_fails_closed_without_evidence():
    body=client.post("/v1/chat",json=payload()).json()
    assert body["safety_status"]=="generation_error"; assert body["action_table"]==[]; assert body["citations"]==[]
def test_emergency_precedes_retrieval():
    body=client.post("/v1/chat",json=payload("I have chest pain and cannot breathe")).json()
    assert body["safety_status"]=="escalate"; assert "emergency" in body["plain_language_summary"].lower()
def test_pregnancy_exact_enum():
    safe=client.post("/v1/chat",json=payload()).json(); assert safe["safety_status"]!="escalate"
    p=payload(); p["context"]["pregnancy"]="pregnant"
    assert client.post("/v1/chat",json=p).json()["safety_status"]=="escalate"
def test_stream_has_measured_completion():
    text=client.post("/v1/chat/stream",json=payload()).text
    assert '"event": "triage"' in text and '"event": "completion"' in text and "request_id" in text
