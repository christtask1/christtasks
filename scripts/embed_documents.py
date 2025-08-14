#!/usr/bin/env python3
"""
Script to embed and upload Christian apologetics documents to Pinecone.
Usage: python scripts/embed_documents.py --input-dir ./documents --source-name "apologetics-library"
"""

import os
import sys
import argparse
import uuid
from pathlib import Path
from typing import List, Dict, Any

# Add the parent directory to the path so we can import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.services.openai_service import OpenAIService
from app.services.pinecone_service import PineconeService
from app.config import settings

class DocumentEmbedder:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.pinecone_service = PineconeService()
    
    def read_text_file(self, file_path: str) -> str:
        """Read text content from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {str(e)}")
            return ""
    
    async def process_document(self, file_path: str, source_name: str) -> List[Dict[str, Any]]:
        """Process a single document and return chunks with embeddings"""
        print(f"Processing: {file_path}")
        
        # Read the document
        content = self.read_text_file(file_path)
        if not content:
            return []
        
        # Split into chunks
        chunks = self.openai_service.chunk_text(content)
        print(f"  Created {len(chunks)} chunks")
        
        # Generate embeddings for all chunks
        embeddings = await self.openai_service.get_embeddings(chunks)
        
        # Prepare documents for Pinecone
        documents = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            doc_id = f"{source_name}_{os.path.basename(file_path)}_{i}_{uuid.uuid4().hex[:8]}"
            
            documents.append({
                "id": doc_id,
                "text": chunk,
                "embedding": embedding,
                "source": source_name,
                "chunk_index": i,
                "file_path": file_path
            })
        
        return documents
    
    async def process_directory(self, input_dir: str, source_name: str) -> List[Dict[str, Any]]:
        """Process all text files in a directory"""
        all_documents = []
        input_path = Path(input_dir)
        
        if not input_path.exists():
            print(f"Error: Directory {input_dir} does not exist")
            return []
        
        # Find all text files
        text_extensions = {'.txt', '.md', '.rst', '.tex'}
        text_files = []
        
        for ext in text_extensions:
            text_files.extend(input_path.rglob(f"*{ext}"))
        
        print(f"Found {len(text_files)} text files to process")
        
        for file_path in text_files:
            documents = await self.process_document(str(file_path), source_name)
            all_documents.extend(documents)
        
        return all_documents
    
    async def upload_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Upload documents to Pinecone"""
        if not documents:
            print("No documents to upload")
            return False
        
        print(f"Uploading {len(documents)} documents to Pinecone...")
        
        try:
            # Upload in batches to avoid rate limits
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                await self.pinecone_service.upsert_documents(batch)
                print(f"  Uploaded batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}")
            
            print("Upload completed successfully!")
            return True
        except Exception as e:
            print(f"Error uploading documents: {str(e)}")
            return False
    
    async def get_index_stats(self):
        """Get and display Pinecone index statistics"""
        try:
            stats = await self.pinecone_service.get_index_stats()
            print(f"\nPinecone Index Statistics:")
            print(f"  Total vectors: {stats['total_vector_count']}")
            print(f"  Dimension: {stats['dimension']}")
            print(f"  Index fullness: {stats['index_fullness']:.2%}")
        except Exception as e:
            print(f"Error getting index stats: {str(e)}")

async def main():
    parser = argparse.ArgumentParser(description="Embed and upload documents to Pinecone")
    parser.add_argument("--input-dir", required=True, help="Directory containing text files to process")
    parser.add_argument("--source-name", required=True, help="Source name for the documents")
    parser.add_argument("--dry-run", action="store_true", help="Process documents but don't upload to Pinecone")
    
    args = parser.parse_args()
    
    # Validate environment variables
    if not settings.openai_api_key:
        print("Error: OPENAI_API_KEY not set in environment")
        sys.exit(1)
    
    if not settings.pinecone_api_key:
        print("Error: PINECONE_API_KEY not set in environment")
        sys.exit(1)
    
    if not settings.pinecone_environment:
        print("Error: PINECONE_ENVIRONMENT not set in environment")
        sys.exit(1)
    
    embedder = DocumentEmbedder()
    
    # Process documents
    documents = await embedder.process_directory(args.input_dir, args.source_name)
    
    if not documents:
        print("No documents to process")
        sys.exit(1)
    
    print(f"\nProcessed {len(documents)} document chunks")
    
    if args.dry_run:
        print("Dry run mode - documents not uploaded to Pinecone")
        return
    
    # Upload to Pinecone
    success = await embedder.upload_documents(documents)
    
    if success:
        await embedder.get_index_stats()
    else:
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 