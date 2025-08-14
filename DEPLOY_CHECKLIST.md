# 🚀 Render Deployment Checklist

## Pre-Deployment ✅

- [ ] Code is pushed to GitHub repository
- [ ] Have OpenAI API key ready
- [ ] Have Pinecone API key and environment ready
- [ ] Documents are prepared in `/documents` folder

## Deployment Steps 🔧

### 1. Create Render Web Service
- [ ] Go to [Render Dashboard](https://dashboard.render.com)
- [ ] Click "New +" → "Web Service"
- [ ] Connect your GitHub repository
- [ ] Select your repository

### 2. Configure Service Settings
- [ ] **Name**: `christian-apologetics-chatbot` (or your preferred name)
- [ ] **Runtime**: `Python 3`
- [ ] **Build Command**: `pip install -r requirements.txt`
- [ ] **Start Command**: `python start.py`
- [ ] **Plan**: Free (for testing) or Starter ($7/month)

### 3. Set Environment Variables
Add these in Render → Environment tab:
- [ ] `OPENAI_API_KEY` = your_actual_openai_api_key
- [ ] `PINECONE_API_KEY` = your_actual_pinecone_api_key  
- [ ] `PINECONE_ENVIRONMENT` = your_pinecone_environment (e.g., us-east-1)
- [ ] `PINECONE_INDEX_NAME` = christian-apologetics
- [ ] `MODEL_NAME` = gpt-3.5-turbo
- [ ] `EMBEDDING_MODEL` = text-embedding-ada-002
- [ ] `MAX_TOKENS` = 400
- [ ] `TEMPERATURE` = 0.7

### 4. Deploy
- [ ] Click "Create Web Service"
- [ ] Wait for build to complete (5-10 minutes)
- [ ] Check logs for any errors

## Post-Deployment ✅

### 5. Embed Documents
Run locally to populate Pinecone:
```bash
# Set up local .env file with same API keys
cp env_example.txt .env
# Edit .env with your API keys

# Install dependencies
pip install -r requirements.txt

# Run embedding script
python scripts/embed_documents.py --input-dir ./documents --source-name "apologetics-library"
```

### 6. Test Deployment
- [ ] Test health endpoint: `https://your-app.onrender.com/health`
- [ ] Test chat API with a sample question
- [ ] Check API documentation: `https://your-app.onrender.com/docs`

### 7. Update CORS (if you have a frontend)
- [ ] Update `allowed_origins` in `app/main.py` with your frontend domain
- [ ] Redeploy if CORS changes were made

## Quick Test Commands 🧪

```bash
# Health check
curl https://your-app-name.onrender.com/health

# Test chat
curl -X POST https://your-app-name.onrender.com/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the evidence for the resurrection of Jesus?",
    "conversation_history": []
  }'
```

## Your App URLs 🌐

After deployment, your app will be available at:
- **API Base URL**: `https://your-app-name.onrender.com`
- **Health Check**: `https://your-app-name.onrender.com/health`
- **Chat Endpoint**: `https://your-app-name.onrender.com/api/v1/chat`
- **API Docs**: `https://your-app-name.onrender.com/docs`

## Troubleshooting 🔍

If something goes wrong:
1. Check Render service logs
2. Verify all environment variables are set correctly
3. Ensure API keys are valid and have sufficient credits
4. Check that documents were embedded successfully in Pinecone

## Success! 🎉

When everything is working:
- [ ] RAG chatbot is live and responding to questions
- [ ] API documentation is accessible
- [ ] Health checks are passing
- [ ] Documents are searchable through the chat interface

Your Christian Apologetics RAG Chatbot is now deployed and ready to serve users worldwide!

