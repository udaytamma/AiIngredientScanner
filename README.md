# AI Ingredient Safety Analyzer

Multi-agent AI system for analyzing food and cosmetic ingredient safety, built with LangGraph and deployed on Google Cloud.

## Quick Start

```bash
# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Verify connections
python test_connections.py

# Run tests
pytest

# Launch UI
streamlit run app.py
```

## Architecture

```
User Input → Supervisor → Research Agent → Analysis Agent → Critic Agent → Output
                ↑                                              ↓
                └──────────── Retry Loop (max 2) ←─────────────┘
```

**Agents:**
- **Supervisor**: Routes workflow based on state
- **Research**: Fetches ingredient data (Qdrant + Google Search fallback)
- **Analysis**: Generates personalized safety reports
- **Critic**: Validates quality with LLM-based checks

## Project Structure

```
ingredient-analyzer/
├── app.py                  # Streamlit entry point
├── graph.py                # LangGraph workflow
├── agents/
│   ├── supervisor.py       # Routing logic
│   ├── research.py         # Qdrant + Grounding
│   ├── analysis.py         # Report generation
│   └── critic.py           # Validation
├── tools/
│   ├── ingredient_lookup.py
│   ├── grounded_search.py
│   ├── safety_scorer.py
│   └── allergen_matcher.py
├── services/
│   └── session.py          # Redis session management
├── state/
│   └── schema.py           # State definitions
├── config/
│   ├── settings.py         # Configuration
│   └── logging_config.py   # Structured logging
└── tests/
    └── test_*.py           # 92 tests, 75% coverage
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLOUD_PROJECT` | GCP project ID |
| `QDRANT_URL` | Qdrant Cloud cluster URL |
| `QDRANT_API_KEY` | Qdrant API key |
| `REDIS_URL` | Redis connection string |
| `LANGCHAIN_API_KEY` | LangSmith API key |

## Tech Stack

- **LLM**: Gemini 2.0 Flash via Vertex AI
- **Orchestration**: LangGraph
- **Vector DB**: Qdrant Cloud
- **Session**: Redis Cloud
- **Tracing**: LangSmith
- **UI**: Streamlit
- **Deployment**: Google Cloud Run

## Features

- Personalized safety analysis based on allergies and skin type
- Beginner/Expert explanation modes
- Allergen matching with prominent AVOID warnings
- Quality validation with automatic retry loop
- Session persistence across page refreshes
