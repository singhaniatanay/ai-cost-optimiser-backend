# Cost Architect AI Backend

A FastAPI-based cost optimization system for enterprise AI workloads. Helps enterprises make data-driven decisions about AI model selection through automated analysis and recommendations.

## 🚀 Features

### Core Functionality
- **Automated Cost Analysis**: Calculates monthly costs across multiple AI models
- **Model Scoring**: Filters and ranks models by latency, context window, and composite scores
- **ROI Analysis**: Shows savings, ROI percentage, and payback periods
- **Business Context Understanding**: Processes natural language automation requests

### 🎛️ **NEW: Interactive Mode with Real-time Parameter Adjustment**
- **Structured Data API**: Returns all intermediate calculations for UI integration
- **Real-time Updates**: Modify parameters via sliders and get instant recalculations
- **Smart Restart Logic**: Only recalculates affected downstream components
- **Debounced Updates**: Optimized for smooth slider interactions

## 📊 Architecture

The system uses a 6-agent pipeline:

1. **Solution Architect** - Extracts automation requirements from natural language
2. **Intake & Clarifier** - Validates workload parameters  
3. **Cost Engine** - Calculates monthly costs across all models
4. **Model Scorer** - Filters by constraints and ranks by composite score
5. **ROI Calculator** - Compares current vs recommended model costs
6. **Recommendation Synthesizer** - Generates executive-ready markdown reports

## 🔌 API Endpoints

### Standard Chat Mode
```http
POST /v1/chat
Content-Type: application/json

{
  "messages": [
    {
      "role": "user", 
      "content": "We process 500 support emails daily, need AI to tag priority and draft replies"
    }
  ]
}
```

**Response**: Plain text recommendation

### 🎛️ Interactive Mode
```http
POST /v1/chat/interactive
Content-Type: application/json

{
  "messages": [
    {
      "role": "user",
      "content": "We process 500 support emails daily, need AI to tag priority and draft replies"  
    }
  ]
}
```

**Response**: Structured data with all intermediate outputs
```json
{
  "structured_data": {
    "solution_architect": {
      "opt_task": "Email automation system",
      "architecture": ["1 - Email ingestion", "2 - Priority classification", "3 - Response generation"],
      "workload": {...}
    },
    "workload_params": {
      "calls_per_day": 500,
      "avg_input_tokens": 300,
      "avg_output_tokens": 150,
      "latency_sla_ms": 120000,
      "region": "US",
      "compliance_constraints": [],
      "current_model": ""
    },
    "cost_table": [
      {
        "model_name": "gpt-3.5-turbo",
        "monthly_cost": 13500.0,
        "p90_latency_ms": 350,
        "context_window_tokens": 16385
      }
    ],
    "ranked_models": [
      {
        "model_name": "gpt-3.5-turbo", 
        "monthly_cost": 13500.0,
        "p90_latency_ms": 350,
        "composite_score": 1.0
      }
    ],
    "roi_analysis": {
      "current_model": "",
      "best_model": "gpt-3.5-turbo",
      "savings_per_month": 0.0,
      "roi_percent": 0.0,
      "payback_weeks": 4
    },
    "final_recommendation": "Implement gpt-3.5-turbo; projected cost ₹13,500 / month...",
    "editable_fields": ["calls_per_day", "avg_input_tokens", "avg_output_tokens", "latency_sla_ms", "region"]
  }
}
```

### 🔄 Parameter Updates
```http
POST /v1/chat/update-params
Content-Type: application/json

{
  "modified_workload": {
    "calls_per_day": 1000,
    "avg_input_tokens": 300,
    "avg_output_tokens": 150,
    "latency_sla_ms": 120000,
    "region": "US",
    "compliance_constraints": [],
    "current_model": ""
  },
  "original_data": {
    // Previous structured_data response
  }
}
```

**Response**: Updated structured data with recalculated costs and recommendations

## 🎛️ Interactive UI Integration

The interactive mode is designed for slider-based UIs:

### UI Flow
1. **Initial Analysis**: User describes automation need → Get structured data
2. **Parameter Adjustment**: User moves sliders → Real-time cost updates
3. **Visual Feedback**: Instant ROI recalculation and model re-ranking

### Key UI Elements
- **Volume Slider**: `calls_per_day` (100-5000)
- **Input Tokens Slider**: `avg_input_tokens` (50-2000)  
- **Output Tokens Slider**: `avg_output_tokens` (50-1000)
- **Latency SLA Slider**: `latency_sla_ms` (1000ms-5min)
- **Region Dropdown**: `region` (US, EU, APAC)

### Optimization Features
- **500ms Debouncing**: Prevents excessive API calls during slider movement
- **Smart Restart**: Only recalculates from Cost Engine onwards (skips Solution Architect)
- **Instant Visual Updates**: Slider values update immediately before API call

## 🧪 Demo & Testing

### Run Interactive Demo
```bash
# Start the API server
cd cost_architect
python -m uvicorn app.main:app --reload --port 8000

# Open the HTML demo
open demo_ui.html

# Or run the Python simulation
python example_ui_interaction.py
```

### Test Interactive Functionality
```bash
python test_interactive.py
```

## 🏗️ Development

### Setup
```bash
cd cost_architect
pip install -r requirements.txt
cp .env.example .env  # Add your OpenAI API key
```

### Run Server
```bash
python -m uvicorn app.main:app --reload --port 8000
```

### Available Make Commands  
```bash
make dev     # Start development server
make test    # Run tests
make lint    # Check code quality
make docker-build  # Build Docker image
```

## 🔧 Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Agent Configuration
All agent prompts and settings are in `app/agents/configs.py`. Key settings:
- **Temperature**: Set to 0.2 for consistent outputs
- **Models**: All agents use `gpt-4o` for quality
- **Response Format**: Structured JSON for machine processing

## 📈 Use Cases

### Business Scenarios
- **Customer Support**: Email/chat automation with priority tagging
- **Document Processing**: Contract analysis, compliance review
- **Sales Analytics**: Call summarization, lead scoring  
- **Content Creation**: Blog posts, marketing copy generation
- **Data Analysis**: Survey insights, report generation

### Cost Optimization Benefits
- **Multi-Model Comparison**: OpenAI, Anthropic, AWS Bedrock models
- **Real-time What-if Analysis**: Adjust volume/requirements instantly
- **ROI Visibility**: Clear payback periods and savings projections
- **Constraint-aware Recommendations**: Respects latency and compliance needs

## 🐳 Docker Deployment

```bash
# Build image
docker build -t cost-architect .

# Run container
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key cost-architect
```

## 📝 API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/healthz

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and test with `make test`
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open Pull Request

## 📄 License

This project is licensed under the MIT License. 