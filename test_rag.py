#!/usr/bin/env python3
"""
Test script for Documentation RAG functionality

This script allows you to test the Canvas parsing and RAG functionality
without setting up the full MCP server.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path for local testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from documentation_rag.canvas_parser import CanvasParser
from documentation_rag.rag_engine import RAGEngine


async def test_canvas_parsing():
    """Test Canvas file parsing."""
    print("=== Testing Canvas Parsing ===")
    
    # Get vault path from user
    vault_path = input("Enter path to your Obsidian vault: ").strip()
    if not vault_path:
        print("No vault path provided")
        return
    
    vault_path = Path(vault_path)
    if not vault_path.exists():
        print(f"Vault path does not exist: {vault_path}")
        return
    
    # Find Canvas files
    canvas_files = list(vault_path.glob("**/*.canvas"))
    if not canvas_files:
        print("No Canvas files found in vault")
        return
    
    print(f"Found {len(canvas_files)} Canvas files:")
    for i, canvas_file in enumerate(canvas_files):
        rel_path = canvas_file.relative_to(vault_path)
        print(f"  {i+1}. {rel_path}")
    
    # Let user choose a Canvas file
    try:
        choice = int(input("Choose a Canvas file (number): ")) - 1
        if choice < 0 or choice >= len(canvas_files):
            print("Invalid choice")
            return
    except ValueError:
        print("Invalid input")
        return
    
    chosen_canvas = canvas_files[choice]
    rel_path = chosen_canvas.relative_to(vault_path)
    
    # Parse the Canvas file
    try:
        parser = CanvasParser(str(vault_path))
        canvas_data = parser.parse_canvas_file(str(rel_path))
        
        print(f"\n=== Canvas Analysis: {rel_path} ===")
        print(f"Total nodes: {canvas_data['metadata']['total_nodes']}")
        print(f"Total edges: {canvas_data['metadata']['total_edges']}")
        
        print("\nNode types:")
        for node_type, count in canvas_data['metadata']['node_types'].items():
            print(f"  {node_type}: {count}")
        
        print("\nColor distribution:")
        color_legend = canvas_data['color_legend']
        for color, count in canvas_data['metadata']['color_distribution'].items():
            meaning = color_legend.get(color, "Unknown")
            print(f"  {meaning}: {count}")
        
        print("\nFirst few nodes:")
        for node in canvas_data['nodes'][:5]:
            node_type = color_legend.get(node.get('color', '0'), 'Reference')
            if 'text' in node:
                print(f"  - {node['text']} ({node_type})")
            elif 'file' in node:
                print(f"  - [File: {node['file']}] ({node_type})")
        
        # Show referenced files
        file_nodes = parser.get_file_nodes(canvas_data)
        if file_nodes:
            print(f"\nReferenced files ({len(file_nodes)}):")
            for node in file_nodes:
                print(f"  - {node['file']}")
        
        # Save parsed data for inspection
        output_file = vault_path / f"{chosen_canvas.stem}_parsed.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f, indent=2, ensure_ascii=False)
        print(f"\nParsed data saved to: {output_file}")
        
    except Exception as e:
        print(f"Error parsing Canvas file: {e}")
        import traceback
        traceback.print_exc()


async def test_rag_functionality():
    """Test RAG indexing and search."""
    print("\n=== Testing RAG Functionality ===")
    
    # Get vault path from user
    vault_path = input("Enter path to your Obsidian vault: ").strip()
    if not vault_path:
        print("No vault path provided")
        return
    
    vault_path = Path(vault_path)
    if not vault_path.exists():
        print(f"Vault path does not exist: {vault_path}")
        return
    
    try:
        # Initialize RAG engine
        print("Initializing RAG engine...")
        rag_engine = RAGEngine(str(vault_path))
        
        # Check if index exists
        stats = rag_engine.get_collection_stats()
        print(f"Current index contains {stats['total_documents']} documents")
        
        if stats['total_documents'] == 0:
            print("No existing index found. Creating new index...")
            indexed_count = await rag_engine.index_vault()
            print(f"Indexed {indexed_count} documents")
        else:
            reindex = input("Index exists. Re-index? (y/N): ").strip().lower()
            if reindex == 'y':
                indexed_count = await rag_engine.index_vault(force_reindex=True)
                print(f"Re-indexed {indexed_count} documents")
        
        # Show collection stats
        stats = rag_engine.get_collection_stats()
        print(f"\nCollection statistics:")
        print(f"Total documents: {stats['total_documents']}")
        
        if 'document_types' in stats:
            print("Document types:")
            for doc_type, count in stats['document_types'].items():
                print(f"  {doc_type}: {count}")
        
        # Interactive search
        print("\n=== Interactive Search ===")
        print("Enter search queries (empty line to quit):")
        
        while True:
            query = input("\nSearch: ").strip()
            if not query:
                break
            
            print("Searching...")
            results = await rag_engine.search(query, limit=3)
            
            if not results:
                print("No results found")
                continue
            
            print(f"\nFound {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"\n--- Result {i} (Score: {result['score']:.3f}) ---")
                print(f"Source: {result['source']}")
                print(f"Type: {result['type']}")
                print(f"Content: {result['content'][:200]}...")
                if len(result['content']) > 200:
                    print("[Content truncated]")
    
    except Exception as e:
        print(f"Error in RAG functionality: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    print("Documentation RAG Test Script")
    print("============================")
    
    while True:
        print("\nOptions:")
        print("1. Test Canvas parsing")
        print("2. Test RAG functionality")
        print("3. Exit")
        
        choice = input("Choose option (1-3): ").strip()
        
        if choice == "1":
            await test_canvas_parsing()
        elif choice == "2":
            await test_rag_functionality()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())
