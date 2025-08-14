# Christian Apologetics RAG Chatbot

A FastAPI-based RAG (Retrieval-Augmented Generation) chatbot for Christian apologetics that uses OpenAI for embeddings and GPT-4 for answering questions, with Pinecone as the vector store.

## Features

- **RAG Chatbot**: Retrieves relevant Christian apologetics documents and generates biblically-based answers
- **OpenAI Integration**: Uses GPT-3.5 Turbo for chat completions and text-embedding-ada-002 for embeddings
- **Pinecone Vector Store**: Efficient similarity search for document retrieval
- **Document Upload Script**: Automated script to embed and upload text documents to Pinecone
- **Environment Configuration**: Secure API key management via environment variables
- **Modular Architecture**: Separated concerns with dedicated services for OpenAI and Pinecone

## Project Structure

```
ChristTask1/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Environment configuration
│   ├── routes/
│   │   ├── __init__.py
│   │   └── chat.py         # Chat endpoint
│   └── services/
│       ├── __init__.py
│       ├── openai_service.py    # OpenAI integration
│       └── pinecone_service.py  # Pinecone vector store
├── scripts/
│   ├── __init__.py
│   └── embed_documents.py  # Document embedding script
├── requirements.txt
├── env_example.txt         # Environment variables template
└── README.md
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file and configure your API keys:

```bash
cp env_example.txt .env
```

Edit `.env` with your actual API keys:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment_here
PINECONE_INDEX_NAME=christian-apologetics

# Application Configuration
MODEL_NAME=gpt-3.5-turbo
EMBEDDING_MODEL=text-embedding-ada-002
MAX_TOKENS=1000
TEMPERATURE=0.7
```

### 3. Prepare Documents

Create a directory for your Christian apologetics documents:

```bash
mkdir documents
```

Add your text files (`.txt`, `.md`, `.rst`, `.tex`) to the `documents/` directory.

### 4. Upload Documents to Pinecone

Run the embedding script to process and upload your documents:

```bash
python scripts/embed_documents.py --input-dir ./documents --source-name "apologetics-library"
```

### 5. Start the FastAPI Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Usage

### Chat Endpoint

**POST** `/api/v1/chat`

Request body:
```json
{
  "question": "What is the evidence for the resurrection of Jesus?",
  "conversation_history": []
}
```

Response:
```json
{
  "answer": "**Evidence for the Resurrection of Jesus Christ**\n\nThe resurrection of Jesus Christ is the cornerstone of the Christian faith, and there is substantial historical evidence supporting this miraculous event...",
  "sources": [
    {
      "text": "The resurrection of Jesus Christ is the most well-attested event in ancient history...",
      "source": "apologetics-library",
      "score": 0.95
    }
  ],
  "question": "What is the evidence for the resurrection of Jesus?"
}
```

### Health Check

**GET** `/health` - Check API health status

**GET** `/api/v1/health` - Check chat service health

## API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Script Usage

### Document Embedding Script

```bash
# Process and upload documents
python scripts/embed_documents.py --input-dir ./documents --source-name "apologetics-library"

# Dry run (process without uploading)
python scripts/embed_documents.py --input-dir ./documents --source-name "apologetics-library" --dry-run
```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `PINECONE_API_KEY` | Your Pinecone API key | Required |
| `PINECONE_ENVIRONMENT` | Your Pinecone environment | Required |
| `PINECONE_INDEX_NAME` | Pinecone index name | `christian-apologetics` |
| `MODEL_NAME` | OpenAI model for chat | `gpt-3.5-turbo` |
| `EMBEDDING_MODEL` | OpenAI model for embeddings | `text-embedding-ada-002` |
| `MAX_TOKENS` | Maximum tokens for responses | `1000` |
| `TEMPERATURE` | Response creativity (0-1) | `0.7` |
| `TOP_K` | Number of similar documents to retrieve | `5` |
| `CHUNK_SIZE` | Document chunk size | `1000` |
| `CHUNK_OVERLAP` | Overlap between chunks | `200` |

## Features

### RAG Implementation

The chatbot implements a complete RAG pipeline:

1. **Question Embedding**: Converts user questions to vector embeddings
2. **Document Retrieval**: Searches Pinecone for similar document chunks
3. **Context Assembly**: Combines retrieved documents as context
4. **Answer Generation**: Uses GPT-3.5 Turbo to generate biblically-based answers

### Christian Apologetics Focus

The system is specifically designed for Christian apologetics with:

- Biblical verse integration
- Warm, encouraging tone
- Gospel-centered responses
- Apologetics-focused context

### Scalable Architecture

- **Modular Design**: Separate services for OpenAI and Pinecone
- **Async Support**: Full async/await implementation
- **Error Handling**: Comprehensive error handling and logging
- **Configuration Management**: Centralized environment configuration

## Development

### Running in Development Mode

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing the API

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the evidence for God\'s existence?", "conversation_history": []}'
```

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure all environment variables are set correctly
2. **Pinecone Index**: The script will create the index automatically if it doesn't exist
3. **Document Processing**: Check file encoding (UTF-8 recommended)
4. **Rate Limits**: The script includes batch processing to handle API rate limits

### Logs

Check the console output for detailed error messages and processing status.

## License

This project is designed for Christian apologetics and educational purposes. 