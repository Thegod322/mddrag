#!/usr/bin/env python3
"""
Test ChromaDB functionality with sentence-transformers
"""

import chromadb
from sentence_transformers import SentenceTransformer
import json

def test_chromadb():
    """Test ChromaDB with embeddings."""
    print("Testing ChromaDB with Sentence Transformers")
    print("=" * 50)
    
    try:
        # Initialize embedding model
        print("Loading embedding model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("[OK] Model loaded successfully")
        
        # Initialize ChromaDB
        print("\nInitializing ChromaDB...")
        client = chromadb.Client()
        collection = client.create_collection(name="test_collection")
        print("[OK] ChromaDB initialized")
        
        # Test documents
        documents = [
            "Godot Engine is a free and open source game engine",
            "The documentation includes tutorials and class references",
            "You can create 2D and 3D games with Godot",
            "ChromaDB is a vector database for semantic search"
        ]
        
        # Generate embeddings
        print("\nGenerating embeddings...")
        embeddings = model.encode(documents).tolist()
        print(f"[OK] Generated {len(embeddings)} embeddings")
        
        # Add to collection
        print("\nAdding documents to collection...")
        collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=[f"doc_{i}" for i in range(len(documents))],
            metadatas=[{"source": f"test_{i}"} for i in range(len(documents))]
        )
        print(f"[OK] Added {len(documents)} documents")
        
        # Test search
        print("\nTesting search...")
        query = "How to make games with Godot?"
        query_embedding = model.encode(query).tolist()
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=2
        )
        
        print(f"\nQuery: '{query}'")
        print("\nResults:")
        for i, (doc, distance) in enumerate(zip(results['documents'][0], results['distances'][0])):
            score = 1 - distance  # Convert distance to similarity
            print(f"{i+1}. Score: {score:.3f}")
            print(f"   Content: {doc}")
        
        print("\n[OK] Search functionality works!")
        
        # Cleanup
        client.delete_collection(name="test_collection")
        print("\n[OK] Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("ChromaDB Integration Test")
    print("========================\n")
    
    success = test_chromadb()
    
    print("\n" + "=" * 50)
    if success:
        print("SUCCESS: ChromaDB integration works properly!")
        print("\nYour system supports:")
        print("- Sentence Transformers embeddings")
        print("- ChromaDB vector storage")
        print("- Semantic search functionality")
    else:
        print("FAILED: ChromaDB integration has issues")
        print("\nPlease check:")
        print("- pip install chromadb")
        print("- pip install sentence-transformers")

if __name__ == "__main__":
    main()
