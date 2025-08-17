"""Chat routes with per-user limits and RAG pipeline.

- Request limits: 25 messages/day and 750 messages/month per user (by IP).
- Answer length is enforced in `openai_service.py` (~300 words).
# TEST COMMENT: Testing GitHub push functionality - this comment can be safely removed
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from app.services.openai_service import OpenAIService
from app.services.pinecone_service import PineconeService


router = APIRouter()

# In-memory usage tracking (replace with persistent storage in production)
USAGE: Dict[str, Dict[str, int]] = {}
LAST_RESET_DAY: str = datetime.utcnow().strftime("%Y-%m-%d")
LAST_RESET_MONTH: str = datetime.utcnow().strftime("%Y-%m")

# Limits
MAX_MESSAGES_PER_DAY = 25
MAX_MESSAGES_PER_MONTH = 750


def _reset_counters_if_needed() -> None:
    """Reset daily and monthly counters when a new day/month starts."""
    global LAST_RESET_DAY, LAST_RESET_MONTH, USAGE
    now_day = datetime.utcnow().strftime("%Y-%m-%d")
    now_month = datetime.utcnow().strftime("%Y-%m")

    if now_day != LAST_RESET_DAY:
        for counters in USAGE.values():
            counters["day"] = 0
        LAST_RESET_DAY = now_day

    if now_month != LAST_RESET_MONTH:
        for counters in USAGE.values():
            counters["month"] = 0
        LAST_RESET_MONTH = now_month


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


# Initialize services
openai_service = OpenAIService()
pinecone_service = PineconeService()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: Request, request: ChatRequest):
    """Chat endpoint implementing RAG with per-user daily/monthly limits."""
    try:
        _reset_counters_if_needed()
        user_key = _get_user_key(req)
        usage = USAGE.setdefault(user_key, {"day": 0, "month": 0})

        if usage["day"] >= MAX_MESSAGES_PER_DAY:
            raise HTTPException(status_code=429, detail=f"Daily limit of {MAX_MESSAGES_PER_DAY} messages exceeded. Try again tomorrow.")
        if usage["month"] >= MAX_MESSAGES_PER_MONTH:
            raise HTTPException(status_code=429, detail=f"Monthly limit of {MAX_MESSAGES_PER_MONTH} messages exceeded. Try again next month.")

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

        # Increment counters after success
        usage["day"] += 1
        usage["month"] += 1

        return ChatResponse(answer=answer, sources=sources, question=request.question)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ CHAT ERROR: {str(e)}")
        print(f"❌ FULL TRACEBACK: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")


@router.get("/usage")
async def get_usage(req: Request):
    """Return current user's usage counters and configured limits."""
    _reset_counters_if_needed()
    user_key = _get_user_key(req)
    usage = USAGE.get(user_key, {"day": 0, "month": 0})
    return {
        "usage_stats": {"daily_used": usage["day"], "monthly_used": usage["month"]},
        "limits": {
            "daily_limit": MAX_MESSAGES_PER_DAY,
            "monthly_limit": MAX_MESSAGES_PER_MONTH,
            "max_tokens_per_response": 500,
        },
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "chat"}