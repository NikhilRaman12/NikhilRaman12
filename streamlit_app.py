import json, os, uuid
import httpx, streamlit as st
st.set_page_config(page_title="MedicoBuddy AI",page_icon="🩺",layout="wide")
st.markdown("""<style>
.stApp{background:#07111f;color:#e7eef8}.status{padding:.65rem 1rem;border-radius:10px;background:#111f31;border:1px solid #29415e}
:focus-visible{outline:3px solid #55c2ff!important;outline-offset:2px}.citation{color:#72d4ff}
@media(max-width:700px){.block-container{padding:1rem}.status{font-size:.9rem}}
</style>""",unsafe_allow_html=True)
API=os.getenv("API_URL","http://127.0.0.1:8000")
if "thread_id" not in st.session_state: st.session_state.thread_id=str(uuid.uuid4())
if "messages" not in st.session_state: st.session_state.messages=[]
st.title("🩺 MedicoBuddy AI")
st.caption("Evidence-grounded health & wellness education — not diagnosis or medical treatment")
try:
    health=httpx.get(f"{API}/health/ready",timeout=2).json(); ready=health.get("ready") is True
    badge="🟢 Evidence Service Online" if ready else "🟠 Evidence Service Not Ready"
    st.markdown(f'<div class="status">{badge} · {health.get("profile","unknown")}</div>',unsafe_allow_html=True)
except Exception: st.markdown('<div class="status">🔴 Evidence Service Unreachable</div>',unsafe_allow_html=True); health={}
with st.sidebar:
    st.header("Your context")
    language=st.selectbox("Language",["auto","English","हिन्दी","తెలుగు","தமிழ்","ಕನ್ನಡ","മലയാളം","বাংলা","मराठी","ગુજરાતી","ਪੰਜਾਬੀ","ଓଡ଼ିଆ","اردو","العربية"])
    pregnancy_label=st.selectbox("Pregnancy status",["Unknown / Not Pregnant","Pregnant","Unknown"])
    pregnancy={"Unknown / Not Pregnant":"not_pregnant","Pregnant":"pregnant","Unknown":"unknown"}[pregnancy_label]
    severe=st.checkbox("Symptoms are severe")
    with st.expander("Administrator diagnostics"):
        st.json(health)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])
prompt=st.chat_input("Describe a mild, short-duration health or wellness concern")
if prompt:
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"): st.markdown(prompt)
    payload={"message":prompt,"thread_id":st.session_state.thread_id,"language":language,"context":{"pregnancy":pregnancy,"severity":"severe" if severe else "mild"}}
    with st.chat_message("assistant"):
        placeholder=st.empty(); placeholder.info("Checking safety and retrieving evidence…")
        try:
            with httpx.stream("POST",f"{API}/v1/chat/stream",json=payload,timeout=40) as response:
                response.raise_for_status(); result=None
                for line in response.iter_lines():
                    if not line.startswith("data: "): continue
                    event=json.loads(line[6:])
                    if event["event"]=="triage": placeholder.info("Safety triage complete; validating evidence…")
                    if event["event"]=="completion": result=event["response"]
            if not result: raise RuntimeError("stream ended without completion")
            text=result["plain_language_summary"]
            if result.get("error"): text+=f"\n\n**Request ID:** `{result['request_id']}`"
            placeholder.markdown(text); st.session_state.messages.append({"role":"assistant","content":text})
            for c in result.get("citations",[]):
                target=c["filename_or_url"] if str(c["filename_or_url"]).startswith("http") else "#"
                st.markdown(f"[📄 {c['citation_id']} · {c['source_title']} · p.{c['page']}]({target})")
            for q in result.get("quick_actions",[]):
                if st.button(q["label"],key=f"{result['request_id']}-{q['label']}"): st.session_state.pending_query=q["standalone_query"]
        except Exception:
            placeholder.error("The service could not complete this request. Please try again; seek clinical help if symptoms are concerning.")
