import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.chat import router as chat_router
from app.models.user_usage import create_tables

app = FastAPI(
    title="Christian Apologetics RAG Chatbot",
    description="A RAG chatbot for Christian apologetics using OpenAI and Pinecone",
    version="1.0.0"
)

# Create database tables on startup
create_tables()

# CORS middleware - more restrictive for production
# You can customize allowed_origins based on your frontend domain
allowed_origins = [
    "http://localhost:3000",  # React dev server
    "http://localhost:8080",  # Vue dev server
    "http://localhost:5173",  # Vite dev server
    "https://christtask-arm06hrp1-christtasks-projects.vercel.app",  # Your production frontend
]

# In development, allow all origins
if os.getenv("ENVIRONMENT") == "development":
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Christian Apologetics RAG Chatbot API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 