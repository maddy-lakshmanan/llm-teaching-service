# 🚀 Quick Start Guide

Get the LLM Teaching Service running in 5 minutes!

## Prerequisites

- Python 3.11+
- Docker Desktop
- 4GB+ RAM available

## Step 1: Start Infrastructure (2 minutes)

```bash
cd llm-teaching-service/docker
docker-compose up -d
```

This starts:
- ✅ Ollama (pulls phi3:mini and llama3:8b models - ~10GB)
- ✅ Redis cache
- ✅ Teaching service API

**Note**: First-time model download takes ~5-10 minutes depending on your connection.

## Step 2: Verify Services (30 seconds)

```bash
# Check all services are healthy
docker-compose ps

# Test the API
curl http://localhost:8080/health
```

Expected output:
```json
{
  "status": "healthy",
  "service": "llm-teaching-service",
  "version": "1.0.0"
}
```

## Step 3: Make Your First Request (30 seconds)

```bash
curl -X POST http://localhost:8080/api/v1/teach \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "demo-student",
    "question": "What is photosynthesis?",
    "subject": "science",
    "grade_level": "middle_school"
  }'
```

You should get an educational response like:
```json
{
  "answer": "Photosynthesis is the process...",
  "model_used": "phi3-mini-educational",
  "tokens_used": 245,
  "estimated_cost": 0.0000245,
  "confidence": 0.85,
  "source": "llm",
  "processing_time_ms": 1250,
  "follow_up_suggestions": [...]
}
```

## Step 4: Explore the API (1 minute)

Open your browser to:
- **API Documentation**: http://localhost:8080/docs
- **Alternative Docs**: http://localhost:8080/redoc

Try these endpoints:
```bash
# List available models
curl http://localhost:8080/api/v1/admin/models

# Check cache statistics
curl http://localhost:8080/api/v1/admin/cache/stats

# Get conversation history
curl http://localhost:8080/api/v1/history/demo-student

# Get usage metrics
curl http://localhost:8080/api/v1/usage/demo-student
```

## Step 5: Test Model Swapping (2 minutes)

Edit `config/models.yaml` and change the default model:

```yaml
models:
  default: "llama3-8b-advanced"  # Changed from phi3-mini-educational
```

Restart the service:
```bash
docker-compose restart app
```

Make another request - it now uses llama3:8b!

## 🎯 Next Steps

### For Development

1. **Set up Python environment:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. **Run tests:**
```bash
pytest tests/ -v --cov=src
```

3. **Debug in VS Code:**
   - Open the project in VS Code
   - Press F5 or use "Run and Debug" panel
   - Select "Python: FastAPI"

### For Production Deployment

1. **Set up GCP:**
```bash
gcloud config set project YOUR_PROJECT_ID
```

2. **Configure secrets in GitHub:**
   - `GCP_PROJECT_ID`
   - `GCP_SA_KEY`
   - `OLLAMA_URL`
   - `REDIS_URL`

3. **Push to main branch:**
```bash
git push origin main
```

GitHub Actions automatically deploys to Cloud Run!

## 📊 Monitor Your Service

### Local Monitoring
```bash
# View logs
docker-compose logs -f app

# Monitor Ollama
docker-compose logs -f ollama

# Redis stats
docker-compose exec redis redis-cli INFO stats
```

### Check Health
```bash
# Basic health
curl http://localhost:8080/health

# Detailed readiness
curl http://localhost:8080/health/ready

# Liveness
curl http://localhost:8080/health/live
```

## 🔧 Troubleshooting

### Service won't start
```bash
# Check Docker is running
docker ps

# View service logs
docker-compose logs app

# Restart services
docker-compose restart
```

### Ollama models not loading
```bash
# Check Ollama logs
docker-compose logs ollama

# Manually pull models
docker-compose exec ollama ollama pull phi3:mini
docker-compose exec ollama ollama pull llama3:8b
```

### Port conflicts
If port 8080 is in use, edit `docker-compose.yml`:
```yaml
ports:
  - "8090:8080"  # Change left side to any free port
```

## 🧪 Example Requests

### Simple Math Question
```bash
curl -X POST http://localhost:8080/api/v1/teach \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student-1",
    "question": "What is 15 * 12?",
    "subject": "math",
    "grade_level": "elementary"
  }'
```

### Advanced Physics Question
```bash
curl -X POST http://localhost:8080/api/v1/teach \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student-2",
    "question": "Explain Newton'\''s second law with examples",
    "subject": "physics",
    "grade_level": "high_school",
    "model_preference": "llama3-8b-advanced"
  }'
```

### With Conversation History
```bash
curl -X POST http://localhost:8080/api/v1/teach \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student-3",
    "question": "Can you explain more about that?",
    "subject": "science",
    "grade_level": "middle_school",
    "conversation_history": [
      {
        "role": "user",
        "content": "What is DNA?"
      },
      {
        "role": "assistant",
        "content": "DNA is the molecule that carries genetic information..."
      }
    ]
  }'
```

## 📚 Learn More

- [README.md](README.md) - Full documentation
- [Architecture Overview](docs/architecture.md)
- [API Reference](http://localhost:8080/docs)
- [Configuration Guide](docs/configuration.md)
- [Deployment Guide](docs/deployment.md)

## 🆘 Get Help

- Issues: https://github.com/your-org/llm-teaching-service/issues
- Slack: #llm-teaching-service
- Email: team@yourcompany.com

---

**Ready to build amazing educational AI experiences!** 🎓✨
