import asyncio
from src.documentation_rag.external_docs_engine import ExternalDocsEngine

async def main():
    engine = ExternalDocsEngine()
    print("Starting indexing of Libraries directory...")
    count = await engine.index_libraries(force_reindex=False)
    print(f"Indexing complete. Total documents indexed: {count}")

if __name__ == "__main__":
    asyncio.run(main())

