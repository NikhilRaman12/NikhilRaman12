import json, logging, time, uuid
from collections.abc import AsyncIterator
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from .config import get_settings
from .retrieval import HybridRetriever, RetrievalUnavailable
from .safety import triage
from .schemas import ChatRequest, ChatResponse, ImplementationPlan, Metrics, SafetyStatus

log = logging.getLogger("medicobuddy")
app = FastAPI(title="MedicoBuddy AI", version="1.0.0", docs_url="/docs")

def dependencies():
    s=get_settings(); r=HybridRetriever(s)
    deps={
      "groq":{"configured":bool(s.groq_api_key),"status":"CONFIGURED" if s.groq_api_key else "NOT CONFIGURED"},
      "vector":{"backend":s.vector_backend,"configured":r.configured(),"status":"CONFIGURED" if r.configured() else "NOT CONFIGURED"},
      "neo4j":{"configured":bool(s.neo4j_uri),"status":"CONFIGURED" if s.neo4j_uri else "NOT CONFIGURED"},
    }
    mandatory=[deps["groq"]["configured"],deps["vector"]["configured"]]
    if s.deployment_profile.value=="FULL_STACK": mandatory.append(deps["neo4j"]["configured"])
    return deps, all(mandatory)

def empty_response(req, rid, status, summary, error=None, started=None):
    s=get_settings(); deps,_=dependencies()
    return ChatResponse(request_id=rid,detected_language=req.language if req.language!="auto" else "en",
      safety_status=status,applies_to="Adults aged 18–64 with mild, short-duration concerns",
      plain_language_summary=summary,action_table=[],implementation_plan=ImplementationPlan(now=[],next_6_12_hours=[],next_24_48_hours=[]),
      things_to_avoid=[],warning_signs=["Seek urgent help for trouble breathing, chest pain, fainting, severe bleeding, or sudden neurological symptoms."],
      follow_up_question="",quick_actions=[],citations=[],graph_paths=[],evidence_strength="insufficient",
      error=error,metrics=Metrics(vector_backend=s.vector_backend,graph_backend="neo4j" if s.neo4j_uri else "not_configured",
      groq_configured=deps["groq"]["configured"],groq_invoked=False,latency_ms=(time.perf_counter()-(started or time.perf_counter()))*1000,
      deployment_profile=s.deployment_profile.value))

async def execute(req: ChatRequest) -> ChatResponse:
    started=time.perf_counter(); rid=str(uuid.uuid4()); status,reason=triage(req)
    if status != SafetyStatus.SUPPORTED:
        return empty_response(req,rid,status,reason or "Clinical assessment is recommended.",started=started)
    s=get_settings()
    try: evidence=HybridRetriever(s).retrieve(req.message)
    except RetrievalUnavailable as exc:
        log.warning(json.dumps({"event":"retrieval_unavailable","request_id":rid,"backend":s.vector_backend}))
        return empty_response(req,rid,SafetyStatus.GENERATION_ERROR,
          "I cannot provide topic-specific guidance because validated evidence retrieval is unavailable.",str(exc),started)
    if not evidence:
        return empty_response(req,rid,SafetyStatus.GENERATION_ERROR,"No relevant supporting evidence was found.","empty_retrieval",started)
    # Generation is deliberately unreachable without a verified retrieval adapter; never fabricate an answer.
    return empty_response(req,rid,SafetyStatus.GENERATION_ERROR,"Validated generation is unavailable.","generation_unavailable",started)

@app.get("/health/live")
def live(): return {"live":True}
@app.get("/health/dependencies")
def dependency_health():
    deps,ready=dependencies(); return {"profile":get_settings().deployment_profile.value,"ready":ready,"dependencies":deps}
@app.get("/health/ready")
def ready():
    deps,is_ready=dependencies(); return {"ready":is_ready,"profile":get_settings().deployment_profile.value,"dependencies":deps}
@app.post("/v1/chat",response_model=ChatResponse)
async def chat(req: ChatRequest): return await execute(req)
@app.post("/v1/chat/stream")
async def stream(req: ChatRequest):
    async def events() -> AsyncIterator[str]:
        rid=str(uuid.uuid4())
        yield f"data: {json.dumps({'event':'triage','request_id':rid})}\n\n"
        result=await execute(req)
        yield f"data: {json.dumps({'event':'evidence_validation','request_id':result.request_id,'valid':result.metrics.citations_valid})}\n\n"
        yield f"data: {json.dumps({'event':'completion','request_id':result.request_id,'response':result.model_dump(mode='json')})}\n\n"
    return StreamingResponse(events(),media_type="text/event-stream",headers={"Cache-Control":"no-cache"})
