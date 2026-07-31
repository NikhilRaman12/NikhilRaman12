import hashlib, json, re
from pathlib import Path
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def normalize(text: str) -> str: return re.sub(r"\s+", " ", text).strip()
def ingest(root: Path, report_path: Path) -> dict:
    pdfs=sorted(root.rglob("*.pdf")); documents=[]; total_pages=total_chunks=chars=errors=0; seen_pages=set(); seen_chunks=set()
    splitter=RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=550,chunk_overlap=75)
    for path in pdfs:
        raw=path.read_bytes(); item={"filename":str(path),"checksum":hashlib.sha256(raw).hexdigest(),"pages":0,"characters":0,"chunks":0,"errors":[]}
        try:
            reader=PdfReader(path)
            for page_no,page in enumerate(reader.pages,1):
                text=normalize(page.extract_text() or "")
                if not text: item["errors"].append(f"page {page_no}: unreadable; OCR unavailable"); errors+=1; continue
                digest=hashlib.sha256(text.encode()).hexdigest()
                if digest in seen_pages: continue
                seen_pages.add(digest); item["pages"]+=1; item["characters"]+=len(text)
                for chunk in splitter.split_text(text):
                    cid=hashlib.sha256(f"{item['checksum']}:{page_no}:{chunk}".encode()).hexdigest()
                    if cid not in seen_chunks: seen_chunks.add(cid); item["chunks"]+=1
            if item["pages"]==0 or item["chunks"]==0: item["errors"].append("document produced zero pages or chunks"); errors+=1
        except Exception as exc: item["errors"].append(type(exc).__name__); errors+=1
        total_pages+=item["pages"]; total_chunks+=item["chunks"]; chars+=item["characters"]; documents.append(item)
    report={"pdfs_discovered":len(pdfs),"documents_parsed":sum(not d["errors"] for d in documents),"pages":total_pages,"characters":chars,"chunks":total_chunks,"error_count":errors,"ready":bool(pdfs) and not errors and all(d["chunks"] for d in documents),"documents":documents}
    report_path.write_text(json.dumps(report,indent=2)); return report
if __name__=="__main__": ingest(Path("data"),Path("ingestion_report.json"))
