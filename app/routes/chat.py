"""Chat routes with per-user limits and RAG pipeline.

- Request limits: 25 messages/day and 750 messages/month per user (by IP).
- Answer length is enforced in `openai_service.py` (~300 words).
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from app.services.openai_service import OpenAIService
from app.services.pinecone_service import PineconeService
from app.services.rate_limiting_service import RateLimitingService
from app.models.user_usage import get_db
from sqlalchemy.orm import Session


router = APIRouter()

# Initialize services
openai_service = OpenAIService()
pinecone_service = PineconeService()
rate_limiting_service = RateLimitingService()


def _get_user_key(req: Request) -> str:
    """Use client IP (or X-Forwarded-For) as a lightweight user key."""
    ip = req.headers.get("x-forwarded-for") or req.client.host or "unknown"
    return ip.split(",")[0].strip()


class ChatRequest(BaseModel):
    question: str
    conversation_history: Optional[List[dict]] = []


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    question: str


@router.post("/chat", response_model=ChatResponse)
async def chat(req: Request, request: ChatRequest, db: Session = Depends(get_db)):
    """Chat endpoint implementing RAG with per-user daily/monthly limits."""
    try:
        user_key = _get_user_key(req)
        
        # Check rate limits using database system
        is_allowed, message, usage_info = rate_limiting_service.check_rate_limit(user_key, db)
        if not is_allowed:
            raise HTTPException(status_code=429, detail=message)

        # Generate embedding for the question
        question_embedding = await openai_service.get_embeddings([request.question])

        # Retrieve relevant documents; tolerate transient vector store errors
        try:
            relevant_docs = await pinecone_service.search_similar(question_embedding[0])
        except Exception:
            relevant_docs = []

        # Build context and sources
        context = ""
        sources: List[dict] = []
        if relevant_docs:
            parts: List[str] = []
            for doc in relevant_docs:
                parts.append(doc["text"])
                sources.append({
                    "text": doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"],
                    "source": doc["source"],
                    "score": doc["score"],
                })
            context = "\n\n".join(parts)
        else:
            context = (
                "This is a Christian apologetics chatbot. You can ask questions "
                "about Christian faith, apologetics, and biblical topics."
            )

        # Conversation messages
        messages: List[Dict[str, str]] = []
        if request.conversation_history:
            messages.extend(request.conversation_history)
        messages.append({"role": "user", "content": request.question})

        # Generate answer (~300 words enforced in service)
        answer = await openai_service.get_chat_completion(messages, context)

        # Increment usage counters after successful response
        rate_limiting_service.increment_usage(user_key, db)

        return ChatResponse(answer=answer, sources=sources, question=request.question)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ CHAT ERROR: {str(e)}")
        print(f"❌ FULL TRACEBACK: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")


@router.get("/usage")
async def get_usage(req: Request, db: Session = Depends(get_db)):
    """Return current user's usage counters and configured limits."""
    user_key = _get_user_key(req)
    usage_stats = rate_limiting_service.get_usage_stats(user_key, db)
    return {
        "usage_stats": {
            "daily_used": usage_stats["daily_used"],
            "daily_remaining": usage_stats["daily_remaining"],
            "monthly_used": usage_stats["monthly_used"],
            "monthly_remaining": usage_stats["monthly_remaining"]
        },
        "limits": {
            "daily_limit": usage_stats["daily_limit"],
            "monthly_limit": usage_stats["monthly_limit"],
            "max_tokens_per_response": 500,
        },
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "chat"}