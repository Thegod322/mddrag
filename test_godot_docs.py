#!/usr/bin/env python3
"""
Test Documentation RAG with sample Godot documentation
"""

import json
import tempfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from documentation_rag.rag_engine import RAGEngine


def create_sample_data():
    """Create sample documentation chunks based on provided data."""
    sample_chunks = [
        {
            "file": "index.rst.txt",
            "section": "Godot Docs – *4.4* branch",
            "text": """Expand the "Read the Docs" panel at the bottom of the sidebar to see
            the list.

            <https://docs.godotengine.org/en/stable>`_ by community members
            on `Weblate <https://hosted.weblate.org/projects/godot-engine/godot-docs>`_.

            Depending on the translation effort's completion level, you may
            find paragraphs or whole pages which are still in English. You can
            help the community by providing new translations or reviewing existing
            ones on Weblate.

            For the time being, localized translations are only available for
            the "stable" branch. You can still view the English documentation for
            other engine versions using the "Read the Docs" panel at the bottom
            of the sidebar.

Welcome to the official documentation of `Godot Engine <https://godotengine.org>`__,
the free and open source community-driven 2D and 3D game engine! If you are new
to this documentation, we recommend that you read the
`introduction page <doc_about_intro>` to get an overview of what this
documentation has to offer.

The table of contents in the sidebar should let you easily access the documentation
for your topic of interest. You can also use the search function in the top-left corner.""",
            "lang": "en"
        },
        {
            "file": "index.rst.txt",
            "section": "Get involved",
            "text": """Godot Engine is an open source project developed by a community of volunteers.
The documentation team can always use your feedback and help to improve the
tutorials and class reference. If you don't understand something, or cannot find
what you are looking for in the docs, help us make the documentation better
by letting us know!

Submit an issue or pull request on the `GitHub repository <https://github.com/godotengine/godot-docs/issues>`_,
help us `translate the documentation <https://hosted.weblate.org/engage/godot-engine/>`_
into your language, or talk to us on the ``#documentation`` channel on the
`Godot Contributors Chat <https://chat.godotengine.org/>`_!""",
            "lang": "en"
        },
        {
            "file": "index.rst.txt",
            "section": "Offline documentation",
            "text": """To browse the documentation offline, you can download an HTML copy (updated every Monday): `stable <https://nightly.link/godotengine/godot-docs/workflows/build_offline_docs/master/godot-docs-html-stable.zip>`__, `latest <https://nightly.link/godotengine/godot-docs/workflows/build_offline_docs/master/godot-docs-html-master.zip>`__, `3.6 <https://nightly.link/godotengine/godot-docs/workflows/build_offline_docs/master/godot-docs-html-3.6.zip>`__. Extract the ZIP archive then open
the top-level ``index.html`` in a web browser.

For mobile devices or e-readers, you can also download an ePub copy (updated every Monday): `stable <https://nightly.link/godotengine/godot-docs/workflows/build_offline_docs/master/godot-docs-epub-stable.zip>`__, `latest <https://nightly.link/godotengine/godot-docs/workflows/build_offline_docs/master/godot-docs-epub-master.zip>`__, `3.6 <https://nightly.link/godotengine/godot-docs/workflows/build_offline_docs/master/godot-docs-epub-3.6.zip>`__. Extract the ZIP archive then open
the ``GodotEngine.epub`` file in an e-book reader application.""",
            "lang": "en"
        }
    ]
    
    return sample_chunks


async def test_with_sample_data():
    """Test RAG functionality with sample documentation."""
    print("Testing Documentation RAG with Sample Data")
    print("=" * 50)
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create sample files
        print("Creating sample documentation files...")
        docs_dir = temp_path / "docs"
        docs_dir.mkdir()
        
        # Write sample chunks as separate files
        sample_chunks = create_sample_data()
        for i, chunk in enumerate(sample_chunks):
            file_path = docs_dir / f"godot_doc_{i}.md"
            content = f"# {chunk['section']}\n\n{chunk['text']}"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"Created {len(sample_chunks)} sample documentation files")
        
        # Initialize RAG engine
        print("\nInitializing RAG engine...")
        rag_engine = RAGEngine(str(temp_path))
        
        # Index documents
        print("Indexing documents...")
        indexed_count = await rag_engine.index_vault(force_reindex=True)
        print(f"Indexed {indexed_count} document chunks")
        
        # Test searches
        test_queries = [
            "How to contribute to Godot documentation?",
            "What is Godot Engine?",
            "How to download offline documentation?",
            "translate documentation to other languages",
            "2D and 3D game engine"
        ]
        
        print("\n" + "=" * 50)
        print("Testing searches:\n")
        
        for query in test_queries:
            print(f"Query: '{query}'")
            results = await rag_engine.search(query, limit=2)
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"  Result {i} (Score: {result['score']:.3f})")
                    print(f"    Source: {result['source']}")
                    print(f"    Content: {result['content'][:100]}...")
            else:
                print("  No results found")
            print()
        
        # Show collection stats
        stats = rag_engine.get_collection_stats()
        print("Collection Statistics:")
        print(f"  Total documents: {stats['total_documents']}")
        if 'document_types' in stats:
            print("  Document types:")
            for doc_type, count in stats['document_types'].items():
                print(f"    {doc_type}: {count}")
    
    print("\n" + "=" * 50)
    print("Test completed successfully!")


async def main():
    """Main test function."""
    try:
        await test_with_sample_data()
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
