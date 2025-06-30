from src.documentation_rag.external_docs_engine import ExternalDocsEngine
import chromadb
from chromadb.config import Settings
from pathlib import Path

if __name__ == "__main__":
    # Use the same path logic as in ExternalDocsEngine
    libraries_path = Path("./Libraries").resolve()
    chroma_client = chromadb.PersistentClient(
        path=str(libraries_path.parent / ".chroma_index"),
        settings=Settings(anonymized_telemetry=False)
    )
    print("Deleting ChromaDB collection 'libraries_docs'...")
    chroma_client.delete_collection("libraries_docs")
    print("ChromaDB collection 'libraries_docs' deleted.")
