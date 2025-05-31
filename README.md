# Cost Architect: Backend for AI cost optimization

Cost Architect is an enterprise-grade AI cost optimization platform that helps organizations analyze, compare, and optimize their AI model usage costs. Through a sophisticated multi-agent workflow, it provides data-driven recommendations for switching between AI models to maximize ROI while meeting performance requirements.

## Features

- **Multi-Agent Workflow**: Orchestrates 6 specialized agents for comprehensive cost analysis
- **Model Comparison**: Evaluates models across cost, latency, and context window constraints
- **ROI Analysis**: Calculates savings potential, ROI percentage, and payback periods
- **Solution Architecture**: Automatically designs AI solutions from business requirements
- **REST API**: Easy integration with existing systems via FastAPI
- **Extensible**: Support for custom model catalogs and providers

## Architecture

The system follows a STEP 0-5 workflow:

1. **Solution Architect** - Extracts requirements and designs AI solutions
2. **Intake & Clarifier** - Validates and structures workload parameters
3. **Cost Engine** - Calculates monthly costs across model catalog
4. **Model Scorer** - Ranks models by composite cost/latency score
5. **ROI Calculator** - Computes financial impact and payback timeline
6. **Recommendation Synthesizer** - Generates executive-ready recommendations

## Setup

### Prerequisites

- Python 3.11+
- pip or pipenv

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cost_architect
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   # OR using make
   make install
   ```

4. **Environment setup**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

   Required environment variables:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   MODEL_TIMEOUT_S=30
   ```

## Quick Start

### Development Server

```bash
# Using make
make dev

# OR directly with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

- **API Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/healthz`

### Docker

```bash
# Build image
make docker-build

# Run container
make docker-run
```

## API Usage

### Example Request

```bash
curl -X POST "http://localhost:8000/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "I need to optimize costs for processing 1000 customer support tickets per day. Each ticket has about 500 words of context and I need 200-word summaries. Response time should be under 2 seconds."
      }
    ]
  }'
```

### Example Response

```json
{
  "answer": "Switch from gpt-4o to gpt-3.5-turbo; save ₹36000 / month (ROI 80%, payback 4 weeks).\n\n| Model | Monthly Cost | Latency (ms) | Score |\n|-------|-------------|-------------|-------|\n| *gpt-3.5-turbo* | ₹9000 | 350 | 1.0 |\n| gpt-4o | ₹45000 | 500 | 5.6 |\n\n• Cost driver: output tokens"
}
```

### Direct Workload JSON

For advanced usage, you can provide structured workload data:

```bash
curl -X POST "http://localhost:8000/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user", 
        "content": "{\"calls_per_day\": 1000, \"avg_input_tokens\": 400, \"avg_output_tokens\": 150, \"latency_sla_ms\": 2000, \"region\": \"us-east-1\", \"compliance_constraints\": [], \"current_model\": \"gpt-4o\"}"
      }
    ]
  }'
```

## Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_cost_math.py -v
```

## Development

```bash
# Code formatting
make format

# Linting
make lint

# Clean up
make clean
```

## Extending the System

### Adding Models to Cost Catalog

Edit `cost_catalog.csv` to add new models:

```csv
model_name,price_per_1k_tokens,latency_ms,context_window_tokens
claude-3-sonnet,15.0,400,200000
gemini-pro,7.0,600,32000
```

### Swapping Model Providers

1. **Create new adapter** in `app/adapters/`:
   ```python
   # app/adapters/anthropic_client.py
   async def chat(prompt: str, model: str, temperature: float, top_p: float, timeout_s: int) -> str:
       # Implement Anthropic API calls
       pass
   ```

2. **Update agent configs** in `app/agents/configs.py`:
   ```python
   INTAKE_CLARIFIER = {
       # ... existing config ...
       "provider_id": "Anthropic",
       "model": "claude-3-sonnet",
       # ...
   }
   ```

3. **Modify agents** to use new adapter:
   ```python
   # app/agents/intake.py
   from app.adapters import anthropic_client  # instead of openai_client
   ```

### Custom Agent Implementation

Create new agents by subclassing `BaseAgent`:

```python
from app.agents.base import BaseAgent

class CustomAgent(BaseAgent):
    async def run(self, message: Any) -> Any:
        # Your custom logic here
        return result
```

## Configuration

Key configuration files:

- `app/config.py` - Environment variables and settings
- `app/agents/configs.py` - Agent prompts and model configurations
- `cost_catalog.csv` - Model pricing and performance data
- `requirements.txt` - Python dependencies

## Deployment

### Docker Production

```bash
docker build -t cost-architect:prod .
docker run -p 8000:8000 --env-file .env cost-architect:prod
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `MODEL_TIMEOUT_S` | Request timeout in seconds | 30 |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run `make lint` and `make test`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the API documentation at `/docs`
- Review test cases for usage examples

---

**Cost Architect** - Optimize your AI costs with data-driven insights. 