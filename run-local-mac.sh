#!/bin/bash
set -e

echo "🚀 Starting LLM Teaching Service (Mac Native Setup)"

# 1. Install Ollama for Mac
if ! command -v ollama &> /dev/null; then
    echo "📦 Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "✅ Ollama CLI already installed"
fi

# 2. Check if Ollama service is running
echo "🔍 Checking Ollama service..."
if curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "✅ Ollama service already running"
    OLLAMA_PID=""
else
    echo "🦙 Starting Ollama service..."
    ollama serve > /tmp/ollama.log 2>&1 &
    OLLAMA_PID=$!
    echo "   PID: $OLLAMA_PID"
    sleep 5
    
    # Verify it started
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo "✅ Ollama service started successfully"
    else
        echo "❌ Failed to start Ollama service"
        cat /tmp/ollama.log
        exit 1
    fi
fi

# 3. Check and pull models if needed
check_and_pull_model() {
    local model_name=$1
    echo "🔍 Checking for model: $model_name"
    
    # List installed models and check if our model exists
    if ollama list | grep -q "^${model_name}"; then
        echo "✅ Model $model_name already downloaded"
        return 0
    else
        echo "📥 Downloading $model_name (this may take a few minutes)..."
        ollama pull "$model_name"
        echo "✅ Model $model_name downloaded"
        return 0
    fi
}

check_and_pull_model "phi3:mini"
# Uncomment to also download llama3:8b
# check_and_pull_model "llama3:8b"

# 4. Check Redis installation and status
echo "🔍 Checking Redis..."
if ! command -v redis-server &> /dev/null; then
    echo "📦 Installing Redis via Homebrew..."
    brew install redis
else
    echo "✅ Redis already installed"
fi

# Check if Redis is running
if redis-cli ping &> /dev/null; then
    echo "✅ Redis already running"
else
    echo "🗄️ Starting Redis..."
    redis-server --daemonize yes --appendonly yes
    sleep 2
    
    # Verify it started
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis started successfully"
    else
        echo "❌ Failed to start Redis"
        exit 1
    fi
fi

# 5. Set up Python environment
echo "🐍 Setting up Python environment..."
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
else
    echo "✅ Virtual environment already exists"
fi

source .venv/bin/activate

# Check if requirements are already installed
echo "🔍 Checking Python dependencies..."
if pip freeze | grep -q "fastapi"; then
    echo "✅ Dependencies already installed"
    echo "💡 To reinstall, run: pip install -r requirements.txt"
else
    echo "📦 Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# 6. Verify all services are ready
echo ""
echo "🔍 Verifying all services..."

# Check Ollama
if curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "✅ Ollama service: Ready"
else
    echo "❌ Ollama service: Not responding"
    exit 1
fi

# Check Redis
if redis-cli ping &> /dev/null; then
    echo "✅ Redis service: Ready"
else
    echo "❌ Redis service: Not responding"
    exit 1
fi

# Check if models are available
MODELS=$(ollama list | tail -n +2 | awk '{print $1}')
echo "✅ Available models:"
echo "$MODELS" | sed 's/^/   - /'

# 7. Start the service
echo ""
echo "✅ All services ready!"
echo "🌐 Starting Teaching Service on http://localhost:8080"
echo "📚 API Docs: http://localhost:8080/docs"
echo "📊 Health Check: http://localhost:8080/health"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

export OLLAMA_URL=http://localhost:11434
export REDIS_HOST=localhost
export REDIS_PORT=6379
export ENVIRONMENT=development

uvicorn src.api.main:app --host 0.0.0.0 --port 8080 --reload

# Cleanup on exit
cleanup() {
    echo ""
    echo "🧹 Cleaning up..."
    if [ ! -z "$OLLAMA_PID" ]; then
        echo "   Stopping Ollama (PID: $OLLAMA_PID)..."
        kill $OLLAMA_PID 2>/dev/null || true
    fi
    # Note: We don't stop Redis as it was likely running before
    echo "✅ Cleanup complete"
}

trap cleanup EXIT