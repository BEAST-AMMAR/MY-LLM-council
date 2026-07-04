import os
import base64
import chromadb
from chromadb.config import Settings
import tempfile

# Initialize ChromaDB for Long-Term Memory
DB_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
os.makedirs(DB_DIR, exist_ok=True)
chroma_client = chromadb.PersistentClient(path=DB_DIR)

# Get or create a collection for precedents
try:
    precedents_collection = chroma_client.get_or_create_collection(name="judge_precedents")
except Exception as e:
    print(f"Failed to initialize Chroma collection: {e}")
    precedents_collection = None

def save_precedent(topic: str, verdict: str, history_id: int):
    if precedents_collection is None:
        return
    
    document = f"Topic: {topic}\nVerdict: {verdict}"
    metadata = {"history_id": history_id, "topic": topic}
    
    try:
        precedents_collection.add(
            documents=[document],
            metadatas=[metadata],
            ids=[str(history_id)]
        )
        print(f"Saved precedent for history_id {history_id}")
    except Exception as e:
        print(f"Error saving precedent: {e}")

def get_precedents(current_topic: str, n_results: int = 1) -> str:
    if precedents_collection is None:
        return ""
    
    # Check if we have any precedents
    try:
        if precedents_collection.count() == 0:
            return ""
        
        results = precedents_collection.query(
            query_texts=[current_topic],
            n_results=n_results
        )
        
        if results and results["documents"] and len(results["documents"][0]) > 0:
            precedents = "\n\n".join(results["documents"][0])
            return f"\n\n[LONG-TERM MEMORY - RELEVANT PAST PRECEDENTS]:\n{precedents}\n"
    except Exception as e:
        print(f"Error retrieving precedents: {e}")
    
    return ""

def parse_base64_file(filename: str, b64_content: str) -> str:
    """Extract text from base64 data URL depending on file type"""
    try:
        if not b64_content.startswith("data:"):
            return "Invalid file format."
        
        header, encoded = b64_content.split(",", 1)
        mime_type = header.split(";")[0].split(":")[1]
        
        decoded = base64.b64decode(encoded)
        
        if mime_type.startswith("text/"):
            return decoded.decode("utf-8")
        elif mime_type == "application/json":
            return decoded.decode("utf-8")
        elif mime_type == "application/pdf":
            # For simplicity in this demo, if it's a PDF, we might need PyPDF2, 
            # but we can try to extract basic strings or just return a placeholder 
            # if we don't have PyPDF2 installed. Let's do a basic decode attempt 
            # or just rely on a library if added. 
            # To keep it robust without extra deps, we'll try to extract ascii strings.
            import string
            printable = set(string.printable)
            extracted = "".join(filter(lambda x: x in printable, decoded.decode("ascii", "ignore")))
            # A very rudimentary extraction for PDFs without PyPDF2
            if len(extracted) > 1000:
                extracted = extracted[:1000] + "... (truncated)"
            return f"[PDF Data Extracted]:\n{extracted}"
        else:
            return f"[File type {mime_type} not natively parsable for text context.]"
    except Exception as e:
        return f"[Failed to parse {filename}: {e}]"
