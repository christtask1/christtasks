# Deploying to Render

This guide will help you deploy your Christian Apologetics RAG Chatbot to Render.

## Prerequisites

1. **GitHub Repository**: Your code must be in a GitHub repository
2. **Render Account**: Sign up at [render.com](https://render.com)
3. **API Keys**: You'll need:
   - OpenAI API Key
   - Pinecone API Key
   - Pinecone Environment (e.g., `us-east-1`)

## Step 1: Prepare Your Repository

Ensure your repository has these files (already created):
- `render.yaml` - Render service configuration
- `start.py` - Production startup script
- `requirements.txt` - Python dependencies

## Step 2: Deploy to Render

### Option A: Using Render Dashboard (Recommended)

1. **Connect Repository**:
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your `ChristTask1` repository

2. **Configure Service**:
   - **Name**: `christian-apologetics-chatbot`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python start.py`
   - **Plan**: Free (for testing) or Starter ($7/month)

3. **Set Environment Variables**:
   Click "Environment" and add these variables:
   ```
   OPENAI_API_KEY=your_actual_openai_api_key
   PINECONE_API_KEY=your_actual_pinecone_api_key
   PINECONE_ENVIRONMENT=your_pinecone_environment
   PINECONE_INDEX_NAME=christian-apologetics
   MODEL_NAME=gpt-3.5-turbo
   EMBEDDING_MODEL=text-embedding-ada-002
   MAX_TOKENS=400
   TEMPERATURE=0.7
   TOP_K=5
   CHUNK_SIZE=1000
   CHUNK_OVERLAP=200
   ```

4. **Deploy**:
   - Click "Create Web Service"
   - Render will automatically build and deploy your app
   - Monitor the logs for any errors

### Option B: Using render.yaml (Infrastructure as Code)

1. **Fork/Clone Repository**: Ensure your code is in GitHub

2. **Deploy from render.yaml**:
   - In Render Dashboard, click "New +" → "Blueprint"
   - Connect your repository
   - Render will read the `render.yaml` file automatically

3. **Set Required Environment Variables**:
   After deployment starts, go to your service settings and add:
   - `OPENAI_API_KEY`
   - `PINECONE_API_KEY`
   - `PINECONE_ENVIRONMENT`

## Step 3: Embed Documents in Production

After your app is deployed, you need to populate your Pinecone vector database:

### Method 1: Run Script Locally (Recommended)

1. **Set up local environment**:
   ```bash
   # Create .env file with your API keys
   cp env_example.txt .env
   # Edit .env with your actual API keys
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Run embedding script**:
   ```bash
   python scripts/embed_documents.py --input-dir ./documents --source-name "apologetics-library"
   ```

### Method 2: One-time Deploy Script (Advanced)

Create a separate Render service just for running the embedding script once.

## Step 4: Test Your Deployment

1. **Check Health Endpoint**:
   ```bash
   curl https://your-app-name.onrender.com/health
   ```

2. **Test Chat API**:
   ```bash
   curl -X POST https://your-app-name.onrender.com/api/v1/chat \
     -H "Content-Type: application/json" \
     -d '{
       "question": "What is the evidence for the resurrection of Jesus?",
       "conversation_history": []
     }'
   ```

3. **Access API Documentation**:
   - Swagger UI: `https://your-app-name.onrender.com/docs`
   - ReDoc: `https://your-app-name.onrender.com/redoc`

## Step 5: Configure CORS for Frontend

If you have a frontend application, update the CORS settings in `app/main.py`:

```python
allowed_origins = [
    "https://your-frontend-domain.com",  # Your actual frontend domain
    "http://localhost:3000",  # For local development
]
```

## Monitoring and Logs

1. **View Logs**: In Render Dashboard → Your Service → Logs
2. **Monitor Health**: Use the `/health` endpoint
3. **Service Metrics**: Available in Render Dashboard

## Troubleshooting

### Common Issues

1. **Build Failures**:
   - Check that `requirements.txt` is present
   - Ensure all dependencies are compatible

2. **Environment Variable Errors**:
   - Verify all required env vars are set in Render
   - Check for typos in variable names

3. **API Errors**:
   - Verify your OpenAI and Pinecone API keys are valid
   - Check API quotas and billing status

4. **Service Won't Start**:
   - Check logs for specific error messages
   - Ensure `start.py` is executable

### Getting Help

1. **Render Logs**: Most issues will be visible in the service logs
2. **Health Checks**: The `/health` endpoint helps diagnose service status
3. **Render Support**: Free tier includes community support

## Cost Optimization

1. **Free Tier Limitations**:
   - Service sleeps after 15 minutes of inactivity
   - 750 hours/month limit across all services
   - No custom domains

2. **Starter Plan Benefits** ($7/month):
   - No sleeping
   - Unlimited hours
   - Custom domains
   - Better performance

## Security Best Practices

1. **Environment Variables**: Never commit API keys to your repository
2. **CORS Configuration**: Use specific domain origins in production
3. **Rate Limiting**: Consider implementing rate limiting for production use
4. **API Key Rotation**: Regularly rotate your API keys

## Next Steps

After successful deployment:
1. Set up monitoring and alerting
2. Configure a custom domain (Starter plan)
3. Set up CI/CD for automatic deployments
4. Consider implementing caching for better performance
5. Add rate limiting and authentication if needed

Your RAG chatbot is now live and accessible to the world! 🎉

