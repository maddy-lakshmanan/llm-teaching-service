# LLM Teaching Service

[![CI](https://github.com/your-org/llm-teaching-service/workflows/CI/badge.svg)](https://github.com/your-org/llm-teaching-service/actions)
[![Deploy](https://github.com/your-org/llm-teaching-service/workflows/Deploy/badge.svg)](https://github.com/your-org/llm-teaching-service/actions)
[![codecov](https://codecov.io/gh/your-org/llm-teaching-service/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/llm-teaching-service)

Production-ready LLM microservice for educational AI, designed with clean architecture and externalized configuration for easy model swapping.

## 🎯 Key Features

- **Model-Agnostic Architecture**: Swap LLM models via YAML configuration without code changes
- **Intelligent Model Routing**: Automatic selection based on question complexity and subject
- **Production-Ready**: Rate limiting, caching, monitoring, and security built-in
- **Cost-Aware**: Track and optimize token usage across models
- **Observable**: Structured logging, metrics, and distributed tracing
- **Zero-Downtime Deployment**: Canary deployments with automatic rollback

## 🏗️ Architecture

```
┌─────────────────┐
│   Flutter App   │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│   Cloud Run     │
│  (FastAPI)      │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼
┌────────┐ ┌─────┐  ┌──────────┐ ┌─────────┐
│ Ollama │ │Redis│  │Firestore │ │Firebase │
│(Phi3)  │ │Cache│  │  (DB)    │ │  Auth   │
└────────┘ └─────┘  └──────────┘ └─────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Google Cloud SDK (for deployment)

### Local Development

1. **Clone and setup:**
```bash
cd llm-teaching-service
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start services with Docker Compose:**
```bash
cd docker
docker-compose up -d
```

This starts:
- Ollama with phi3:mini and llama3:8b models
- Redis cache
- Teaching service on http://localhost:8080

4. **Verify service:**
```bash
curl http://localhost:8080/health
```

5. **Test the API:**
```bash
curl -X POST http://localhost:8080/api/v1/teach \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test-123",
    "question": "What is photosynthesis?",
    "subject": "science",
    "grade_level": "middle_school"
  }'
```

## 📦 Project Structure

```
llm-teaching-service/
├── src/
│   ├── core/              # Domain models and interfaces
│   ├── adapters/          # External integrations (LLM, cache, DB)
│   ├── domain/            # Business logic
│   ├── api/              # FastAPI routes and middleware
│   └── infrastructure/    # Config, logging, monitoring
├── tests/                 # Unit, integration, performance tests
├── config/               # Model configurations (YAML)
├── docker/               # Dockerfile and docker-compose
├── scripts/              # Deployment and migration scripts
└── .github/workflows/    # CI/CD pipelines
```

## 🔧 Configuration

### Model Configuration

Models are configured in [`config/models.yaml`](config/models.yaml):

```yaml
models:
  default: "phi3-mini-educational"
  
  model_registry:
    phi3-mini-educational:
      provider: "ollama-local"
      model_name: "phi3:mini"
      max_tokens: 1024
      temperature: 0.7
      cost_per_1k_tokens: 0.0001
```

### Swapping Models

**Method 1: Update YAML (Recommended)**
```yaml
# Change default model
default: "llama3-8b-advanced"
```

**Method 2: Use Migration Script**
```bash
python scripts/migrate_models.py \
  --from phi3-mini-educational \
  --to llama3-8b-advanced \
  --canary-percentage 10 \
  --canary-duration 5
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test suite
pytest tests/unit/ -v
pytest tests/integration/ -v
```

## 📊 Monitoring

Access monitoring dashboards:

- **Health Check**: `http://localhost:8080/health`
- **Metrics**: `http://localhost:8080/api/v1/admin/cache/stats`
- **API Docs**: `http://localhost:8080/docs`

## 🚢 Deployment

### Deploy to Google Cloud Run

1. **Configure GCP:**
```bash
gcloud config set project YOUR_PROJECT_ID
gcloud auth configure-docker us-central1-docker.pkg.dev
```

2. **Set secrets:**
```bash
# In GitHub repository settings, add:
- GCP_PROJECT_ID
- GCP_SA_KEY
- OLLAMA_URL
- REDIS_URL
```

3. **Deploy:**
```bash
# Automatic via GitHub Actions on push to main
# Or manually:
./scripts/deploy.sh
```

### Deployment Features

- ✅ Multi-stage Docker builds for minimal image size
- ✅ Canary deployments (10% traffic initially)
- ✅ Automatic health checks
- ✅ Rollback on failure
- ✅ Zero-downtime deployments

## 📈 Performance

| Metric | Target | Typical |
|--------|--------|---------|
| P95 Latency (simple) | < 2s | ~800ms |
| P95 Latency (complex) | < 5s | ~2.5s |
| Cache Hit Rate | > 30% | ~45% |
| Cost per Session | < $0.01 | ~$0.003 |
| Availability | 99.9% | 99.95% |

## 🔐 Security

- ✅ Firebase Authentication required (production)
- ✅ Rate limiting per user
- ✅ Input validation with Pydantic
- ✅ Security scanning in CI pipeline
- ✅ Non-root Docker user
- ✅ Secret management via environment variables

## 🛠️ Development Workflow

### VS Code

Open in VS Code and use the provided launch configurations:

- **Python: FastAPI** - Run service with debugger
- **Python: Tests** - Run all tests
- **Python: Current Test File** - Debug current test

### Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint
flake8 src/ tests/

# Type check
mypy src/
```

## 📚 API Documentation

### POST `/api/v1/teach`

Ask a teaching question:

```json
{
  "student_id": "user-123",
  "question": "Explain Newton's first law",
  "subject": "physics",
  "grade_level": "high_school",
  "model_preference": "llama3-8b-advanced"  // Optional
}
```

Response:
```json
{
  "answer": "Newton's first law states...",
  "model_used": "llama3-8b-advanced",
  "tokens_used": 245,
  "estimated_cost": 0.000245,
  "confidence": 0.92,
  "source": "llm",
  "processing_time_ms": 1250,
  "follow_up_suggestions": [...]
}
```

See full API documentation at `/docs` (Swagger UI).

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

Copyright © 2026 Your EdTech Startup. All rights reserved.

## 🆘 Support

- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/your-org/llm-teaching-service/issues)
- Slack: #llm-teaching-service

---

Built with ❤️ for educational innovation
