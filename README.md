# MedicoBuddy AI

MedicoBuddy is a **health and wellness education** application for lower-risk adults with mild, short-duration concerns. It does not diagnose, prescribe, recommend medicine doses, alter treatment, or replace a clinician. Ayurveda content must be identified as traditional practice, emerging evidence, or established evidence and may only be returned when supported by retrieved evidence.

> **Release status: `NO_GO`.** This checkout contained no medical PDFs and no external service configuration. The application deliberately fails closed rather than returning template advice. See [`release_gate_report.json`](release_gate_report.json).

## Implemented request boundary

`Streamlit → FastAPI → deterministic safety triage → configured retrieval adapter → evidence validation → generation boundary → citation validation → streamed completion`

The API will not generate topic-specific content when retrieval is absent. The typed response includes the authoritative request ID, citations, graph paths, per-request metrics, and a safe error. Emergency/risk escalation happens before retrieval.

### Profiles

| Profile | Active architecture | Honest limitation |
|---|---|---|
| `HF_SPACE` | FastAPI and Streamlit in one Docker container | With only `GROQ_API_KEY`, pgvector, Milvus, and Neo4j are `NOT CONFIGURED`; readiness is false. |
| `FULL_STACK` | Compose definitions for API/UI, PostgreSQL/pgvector, Milvus, and Neo4j Community | Services must become reachable and evidence must be ingested before readiness or answers are possible. |

No HIPAA, medical-device, diagnostic, or clinical-validation claim is made.

## Run

```bash
cp .env.example .env
pip install '.[test]'
uvicorn medicobuddy.api:app --port 8000
streamlit run streamlit_app.py --server.port 7860
```

Or run the full topology with `docker compose up --build`. Re-index documents placed under `data/` using `python -m medicobuddy.ingest`. The report fails readiness for unreadable or zero-chunk documents. Persistent database volumes are defined in Compose.

Health endpoints are `/health/live`, `/health/ready`, and `/health/dependencies`; chat endpoints are `/v1/chat` and `/v1/chat/stream`. A `200` response from readiness is not itself success—the UI reads the JSON `ready` field.

## Security and operations

Secrets are environment-only and `.env.example` contains no values. Logs use request IDs and never log prompts or keys. Inputs are bounded by Pydantic. Production operators should rotate credentials, put TLS/auth/rate limiting at an ingress, back up database volumes, run `pip-audit`, and validate licensed authoritative sources before enabling readiness.

Rollback: deploy the preceding immutable image/commit, restore compatible database-volume snapshots, run readiness checks, then shift traffic. Never roll back an index independently of its application/schema version.

## Missing launch gates

The original MedicoBuddy repository and its claimed 15 PDFs were not present and GitHub access was blocked in this environment. Consequently Qwen embedding execution, real database upserts, Neo4j provenance paths, Groq invocation, multilingual generation, browser validation, and three evidence proof bundles could not truthfully be completed. These are recorded as unavailable—not passed.
