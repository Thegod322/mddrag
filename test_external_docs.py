#!/usr/bin/env python3
"""
Test External Documentation Management
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from documentation_rag.external_docs_engine import ExternalDocsEngine


async def main():
    """Test external documentation functionality."""
    print("External Documentation Management Test")
    print("=" * 50)
    
    # Initialize engine
    print("Initializing external docs engine...")
    engine = ExternalDocsEngine()
    
    # Show current stats
    stats = engine.get_stats()
    print(f"\nCurrent state:")
    print(f"Total documents: {stats['total_documents']}")
    
    # List loaded docs
    docs_info = engine.list_indexed_docs()
    if docs_info["indexed_docs"]:
        print("\nCurrently loaded documentation:")
        for key, info in docs_info["indexed_docs"].items():
            print(f"  - {info['name']} v{info['version']} ({info['document_count']} chunks)")
    else:
        print("\nNo documentation loaded yet.")
    
    # Interactive menu
    while True:
        print("\n" + "=" * 50)
        print("Options:")
        print("1. Load documentation from file/directory")
        print("2. Search in documentation")
        print("3. List loaded documentation")
        print("4. Remove documentation")
        print("5. Show statistics")
        print("6. Exit")
        
        choice = input("\nChoice (1-6): ").strip()
        
        if choice == "1":
            # Load documentation
            doc_path = input("Path to documentation file or directory: ").strip()
            if not doc_path:
                continue
                
            doc_name = input("Documentation name (e.g., 'React', 'NumPy'): ").strip()
            if not doc_name:
                continue
            
            print("\nDocument types: libraries, frameworks, tools, general")
            doc_type = input("Type (default: general): ").strip() or "general"
            
            version = input("Version (default: latest): ").strip() or "latest"
            
            print("\nLoading documentation...")
            try:
                result = await engine.index_documentation(
                    doc_path=doc_path,
                    doc_name=doc_name,
                    doc_type=doc_type,
                    version=version
                )
                
                if "error" in result:
                    print(f"Error: {result['error']}")
                elif result["status"] == "already_indexed":
                    print(f"Already indexed. Use option 4 to remove first if you want to re-index.")
                else:
                    print(f"Success! Indexed {result['indexed_count']} document chunks.")
                    
            except Exception as e:
                print(f"Error: {e}")
        
        elif choice == "2":
            # Search
            query = input("Search query: ").strip()
            if not query:
                continue
            
            # Optional filters
            filter_by_type = input("Filter by type (leave empty for all): ").strip()
            filter_by_name = input("Filter by doc name (leave empty for all): ").strip()
            
            doc_types = [filter_by_type] if filter_by_type else None
            doc_names = [filter_by_name] if filter_by_name else None
            
            print("\nSearching...")
            try:
                results = await engine.search(
                    query=query,
                    doc_types=doc_types,
                    doc_names=doc_names,
                    limit=5
                )
                
                if not results:
                    print("No results found.")
                else:
                    print(f"\nFound {len(results)} results:\n")
                    for i, result in enumerate(results, 1):
                        print(f"Result {i} (Score: {result['score']:.3f})")
                        print(f"  From: {result['doc_name']} v{result['version']} ({result['doc_type']})")
                        print(f"  File: {result['source']}")
                        print(f"  Content: {result['content'][:200]}...")
                        print()
                        
            except Exception as e:
                print(f"Error searching: {e}")
        
        elif choice == "3":
            # List docs
            docs_info = engine.list_indexed_docs()
            
            if not docs_info["indexed_docs"]:
                print("No documentation loaded.")
            else:
                print(f"\nTotal documents: {docs_info['total_documents']}")
                print(f"Last updated: {docs_info['last_updated'] or 'Never'}")
                print("\nLoaded documentation:")
                
                for key, info in docs_info["indexed_docs"].items():
                    print(f"\n- {info['name']} v{info['version']}")
                    print(f"  Type: {info['type']}")
                    print(f"  Documents: {info['document_count']}")
                    print(f"  Indexed: {info['indexed_at']}")
                    print(f"  Source: {info['source_path']}")
        
        elif choice == "4":
            # Remove docs
            docs_info = engine.list_indexed_docs()
            if not docs_info["indexed_docs"]:
                print("No documentation to remove.")
                continue
            
            print("\nAvailable documentation:")
            for key, info in docs_info["indexed_docs"].items():
                print(f"  - {info['name']} v{info['version']}")
            
            doc_name = input("\nDocumentation name to remove: ").strip()
            version = input("Version (default: latest): ").strip() or "latest"
            
            if doc_name:
                success = engine.remove_documentation(doc_name, version)
                if success:
                    print(f"Removed '{doc_name}' v{version}")
                else:
                    print(f"Not found: '{doc_name}' v{version}")
        
        elif choice == "5":
            # Stats
            stats = engine.get_stats()
            print(f"\nTotal indexed documents: {stats['total_documents']}")
            print("\nCollections:")
            
            for coll_name, coll_info in stats["collections"].items():
                print(f"\n{coll_name.upper()}:")
                print(f"  Document chunks: {coll_info['document_count']}")
                if coll_info['docs']:
                    print("  Contains:")
                    for doc in coll_info['docs']:
                        print(f"    - {doc}")
        
        elif choice == "6":
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())
