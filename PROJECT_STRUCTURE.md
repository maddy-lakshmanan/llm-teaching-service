# Project Structure

```
llm-teaching-service/
├── .github/
│   └── workflows/
│       ├── ci.yml                    # CI pipeline (test, lint, security)
│       └── deploy.yml                # CD pipeline (Cloud Run deployment)
│
├── .vscode/
│   ├── launch.json                   # Debug configurations
│   └── settings.json                 # VS Code settings
│
├── config/
│   ├── models.yaml                   # LLM model configurations
│   └── feature_flags.yaml            # Feature flag definitions
│
├── docker/
│   ├── Dockerfile                    # Multi-stage production Dockerfile
│   └── docker-compose.yml            # Local development environment
│
├── scripts/
│   ├── migrate_models.py             # Safe model migration script
│   └── deploy.sh                     # Cloud Run deployment script
│
├── src/
│   ├── __init__.py
│   │
│   ├── core/                         # Domain models and interfaces
│   │   ├── __init__.py
│   │   ├── models.py                 # Pydantic models
│   │   └── ports.py                  # Abstract interfaces (ports)
│   │
│   ├── adapters/                     # External integrations
│   │   ├── __init__.py
│   │   ├── llm/                      # LLM provider implementations
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Base provider class
│   │   │   ├── ollama.py             # Ollama implementation
│   │   │   └── factory.py            # Provider factory
│   │   ├── cache/                    # Cache implementations
│   │   │   ├── __init__.py
│   │   │   └── redis_cache.py        # Redis + in-memory cache
│   │   ├── database/                 # Database implementations
│   │   │   ├── __init__.py
│   │   │   └── firestore_db.py       # Firestore + in-memory DB
│   │   └── auth/                     # Authentication
│   │       ├── __init__.py
│   │       └── firebase_auth.py      # Firebase Auth
│   │
│   ├── domain/                       # Business logic
│   │   ├── __init__.py
│   │   ├── teaching/                 # Teaching service domain
│   │   │   ├── __init__.py
│   │   │   └── service.py            # Core teaching logic
│   │   └── rate_limit/               # Rate limiting
│   │       ├── __init__.py
│   │       └── rate_limiter.py       # Rate limit implementation
│   │
│   ├── api/                          # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app entry point
│   │   ├── routes/                   # API routes
│   │   │   ├── __init__.py
│   │   │   ├── teaching.py           # Teaching endpoints
│   │   │   ├── health.py             # Health check endpoints
│   │   │   └── admin.py              # Admin endpoints
│   │   ├── middleware/               # Custom middleware
│   │   │   ├── __init__.py
│   │   │   ├── auth_middleware.py    # Authentication middleware
│   │   │   └── logging_middleware.py # Structured logging
│   │   └── dependencies/             # Dependency injection
│   │       ├── __init__.py
│   │       ├── container.py          # DI container
│   │       └── services.py           # Service providers
│   │
│   └── infrastructure/               # Cross-cutting concerns
│       ├── __init__.py
│       ├── config.py                 # Configuration management
│       ├── logging.py                # Structured logging setup
│       └── metrics.py                # Monitoring & observability
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                   # Pytest fixtures
│   ├── unit/                         # Unit tests
│   │   ├── __init__.py
│   │   ├── test_models.py
│   │   ├── test_llm_factory.py
│   │   ├── test_cache.py
│   │   └── test_rate_limiter.py
│   ├── integration/                  # Integration tests
│   │   ├── __init__.py
│   │   └── test_api.py
│   └── performance/                  # Performance tests
│       ├── __init__.py
│       └── test_performance.py
│
├── .env.example                      # Environment template
├── .gitignore                        # Git ignore rules
├── README.md                         # Main documentation
├── QUICKSTART.md                     # Quick start guide
└── requirements.txt                  # Python dependencies
```

## 📊 Key Metrics

- **Total Files**: 60+
- **Lines of Code**: ~5,000+
- **Test Coverage**: Unit, Integration, Performance
- **Architecture**: Hexagonal (Ports & Adapters)
- **API Endpoints**: 10+
- **CI/CD Pipelines**: 2 (CI + CD)

## 🎯 Key Features Implemented

### Architecture & Design
- ✅ Hexagonal architecture (Ports & Adapters)
- ✅ Dependency injection container
- ✅ Abstract interfaces for all external dependencies
- ✅ Domain-driven design principles

### LLM Integration
- ✅ Model-agnostic provider interface
- ✅ Ollama implementation (local models)
- ✅ Extensible to OpenAI, Anthropic, etc.
- ✅ Factory pattern for provider management
- ✅ Intelligent model routing based on complexity

### Configuration Management
- ✅ Externalized YAML configuration
- ✅ Hot-swappable model configs
- ✅ Environment variable substitution
- ✅ Feature flags support
- ✅ Zero-code model migration

### Caching & Performance
- ✅ Redis-based response caching
- ✅ In-memory fallback for development
- ✅ Configurable TTL
- ✅ Cache invalidation patterns
- ✅ Hit rate tracking

### Storage & Persistence
- ✅ Firestore for conversation history
- ✅ Usage metrics tracking
- ✅ In-memory adapter for testing
- ✅ Cost tracking and analytics

### Security & Authentication
- ✅ Firebase Authentication integration
- ✅ JWT token validation
- ✅ Rate limiting per user
- ✅ Sliding window rate limiter
- ✅ Security scanning in CI

### Observability
- ✅ Structured JSON logging
- ✅ OpenTelemetry integration
- ✅ Distributed tracing support
- ✅ Metrics collection (tokens, cost, latency)
- ✅ Request ID tracking

### API & Middleware
- ✅ RESTful API with FastAPI
- ✅ Automatic OpenAPI documentation
- ✅ Authentication middleware
- ✅ Logging middleware
- ✅ CORS configuration
- ✅ Global error handling

### DevOps & Deployment
- ✅ Multi-stage Dockerfile
- ✅ Docker Compose for local dev
- ✅ GitHub Actions CI pipeline
  - Linting (black, isort, flake8)
  - Type checking (mypy)
  - Security scanning (bandit, safety)
  - Unit tests with coverage
  - Integration tests
  - Docker build test
- ✅ GitHub Actions CD pipeline
  - Canary deployments (10% traffic)
  - Health checks
  - Automatic rollback
  - Cloud Run deployment
- ✅ Zero-downtime deployments

### Testing
- ✅ Unit tests for core components
- ✅ Integration tests for API
- ✅ Performance tests
- ✅ Pytest fixtures and configuration
- ✅ Mock implementations for testing

### Documentation
- ✅ Comprehensive README
- ✅ Quick start guide
- ✅ API documentation (auto-generated)
- ✅ Architecture documentation (this file)
- ✅ Inline code comments
- ✅ VS Code debug configurations

## 🔧 Technology Stack

### Core
- Python 3.11+
- FastAPI (web framework)
- Pydantic (data validation)
- HTTPX (async HTTP client)

### LLM Integration
- Ollama (local model hosting)
- Phi-3 Mini (primary model)
- Llama 3 8B (advanced model)

### Storage
- Redis (caching)
- Firestore (persistence)
- Firebase Auth (authentication)

### Observability
- OpenTelemetry (tracing & metrics)
- Google Cloud Trace
- Structured logging

### Development
- Docker & Docker Compose
- pytest (testing)
- black, isort, flake8 (code quality)
- mypy (type checking)
- bandit, safety (security)

### CI/CD
- GitHub Actions
- Google Cloud Run
- Artifact Registry

## 🚀 Deployment Strategies

### Development
- Docker Compose with hot reload
- In-memory adapters (cache, DB)
- Mock authentication
- Debug logging

### Staging
- Cloud Run (single instance)
- Redis cache
- Firestore database
- Firebase Auth
- Canary testing

### Production
- Cloud Run (auto-scaling 1-10 instances)
- Managed Redis
- Firestore production database
- Firebase Auth with multi-region
- Blue-green deployments with canary
- Comprehensive monitoring

## 📈 Performance Targets

| Metric | Target | Implementation |
|--------|--------|----------------|
| P95 Latency | < 2s | Response caching, efficient models |
| Cache Hit Rate | > 30% | Redis with 1hr TTL |
| Availability | 99.9% | Auto-scaling, health checks |
| Cost per Session | < $0.01 | Local models, intelligent routing |
| Concurrent Users | 100+ | Async architecture, auto-scaling |

## 🔐 Security Features

- ✅ Non-root Docker user
- ✅ Secret management via environment variables
- ✅ Input validation with Pydantic
- ✅ Rate limiting per user
- ✅ Authentication middleware
- ✅ Security scanning in CI
- ✅ Dependency vulnerability checks
- ✅ CORS protection
- ✅ Request size limits

## 🎓 Educational Optimizations

- ✅ Grade-level appropriate responses
- ✅ Subject-specific context handling
- ✅ Socratic questioning prompts
- ✅ Follow-up suggestions
- ✅ Learning resource recommendations
- ✅ Confidence scoring
- ✅ Conversation history tracking

## 📊 Cost Optimization

- ✅ Local model hosting (Ollama)
- ✅ Response caching (30%+ hit rate)
- ✅ Intelligent model routing
- ✅ Token usage tracking
- ✅ Cost per request monitoring
- ✅ Configurable model fallbacks
- ✅ Usage quotas per tier

## 🔄 Model Management

- ✅ YAML-based configuration
- ✅ Hot-swappable models
- ✅ Canary migration script
- ✅ A/B testing support
- ✅ Model health monitoring
- ✅ Automatic fallback
- ✅ Provider abstraction

## 🛠️ Extensibility

### Adding New LLM Providers
1. Implement `AbstractLLMProvider` interface
2. Add provider config to `models.yaml`
3. Register in factory

### Adding New Cache Backends
1. Implement `AbstractCacheService` interface
2. Register in dependency container

### Adding New Databases
1. Implement `AbstractDatabaseService` interface
2. Register in dependency container

### Adding New Features
1. Add feature flag to `feature_flags.yaml`
2. Implement feature
3. Toggle via configuration

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Ollama Documentation](https://ollama.ai/docs)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)

---

**Built with ❤️ for educational innovation**
