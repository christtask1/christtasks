from pinecone import Pinecone
from typing import List, Dict, Any, Optional
from app.config import settings

class PineconeService:
    def __init__(self):
        self.api_key = settings.pinecone_api_key
        self.index_name = settings.pinecone_index_name
        self.pc = None
        self.index = None
        self._initialized = False
    
    def _initialize_pinecone(self):
        """Initialize Pinecone connection"""
        if not self._initialized:
            self.pc = Pinecone(api_key=self.api_key)
            # Fast path: try to attach to the index directly without an
            # expensive list-indexes call. If that fails (e.g., index not
            # created yet), fall back to ensuring it exists.
            try:
                self.index = self.pc.Index(self.index_name)
            except Exception:
                self._ensure_index_exists()
            self._initialized = True
    
    def _ensure_index_exists(self):
        """Ensure the Pinecone index exists, create if it doesn't"""
        try:
            # Avoid list_indexes() when possible; create_index will no-op if exists
            try:
                self.index = self.pc.Index(self.index_name)
                _ = self.index.describe_index_stats()
                return
            except Exception:
                pass

            # Create the index if it doesn't exist
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,  # OpenAI ada-002 embedding dimension
                metric="cosine"
            )
            self.index = self.pc.Index(self.index_name)
        except Exception as e:
            raise Exception(f"Error initializing Pinecone: {str(e)}")
    
    async def upsert_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Upsert documents to Pinecone index"""
        try:
            self._initialize_pinecone()
            vectors = []
            for doc in documents:
                vector = {
                    "id": doc["id"],
                    "values": doc["embedding"],
                    "metadata": {
                        "text": doc["text"],
                        "source": doc.get("source", "unknown"),
                        "chunk_index": doc.get("chunk_index", 0)
                    }
                }
                vectors.append(vector)
            
            self.index.upsert(vectors=vectors)
            return True
        except Exception as e:
            raise Exception(f"Error upserting documents: {str(e)}")
    
    async def search_similar(self, query_embedding: List[float], top_k: int = None) -> List[Dict[str, Any]]:
        """Search for similar documents in Pinecone"""
        if top_k is None:
            top_k = settings.top_k
        
        try:
            self._initialize_pinecone()
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            documents = []
            for match in results.matches:
                documents.append({
                    "id": match.id,
                    "score": match.score,
                    "text": match.metadata.get("text", ""),
                    "source": match.metadata.get("source", "unknown")
                })
            
            return documents
        except Exception as e:
            raise Exception(f"Error searching Pinecone: {str(e)}")
    
    async def delete_documents(self, document_ids: List[str]) -> bool:
        """Delete documents from Pinecone index"""
        try:
            self.index.delete(ids=document_ids)
            return True
        except Exception as e:
            raise Exception(f"Error deleting documents: {str(e)}")
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the Pinecone index"""
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness
            }
        except Exception as e:
            raise Exception(f"Error getting index stats: {str(e)}") 