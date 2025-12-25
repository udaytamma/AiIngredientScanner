# AI Ingredient Safety Analyzer

A multi-agent AI system for analyzing food and cosmetic ingredient safety. Features a Streamlit web interface, React Native mobile app, and RESTful API powered by Google Gemini 2.0 Flash and LangGraph orchestration.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![React Native](https://img.shields.io/badge/React%20Native-Expo-purple.svg)](https://expo.dev)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Overview

The AI Ingredient Safety Analyzer helps users understand product ingredient safety by:

- **Parsing ingredient lists** from any food or cosmetic product
- **Researching each ingredient** via vector database and Google Search
- **Generating personalized safety reports** based on user allergies and skin type
- **Providing actionable recommendations** (SAFE / CAUTION / AVOID)

## Features

### Core Capabilities
- Personalized safety analysis based on allergies and skin type
- Beginner/Expert explanation modes
- Allergen matching with prominent AVOID warnings
- Quality validation with automatic retry loop
- Session persistence across page refreshes

### Mobile App (Phase 2)
- Native camera integration for label scanning
- Multi-language OCR with auto-translation (9+ languages)
- Dark/Light theme toggle
- Expandable ingredient cards with detailed safety metrics
- Offline-ready architecture

### Authentication & User Management (Phase 3)
- Google Sign-In with Firebase Authentication
- User profile persistence with Firestore
- Personalized settings sync across devices
- Guest mode for anonymous usage
- GDPR-compliant account deletion

### Supported Languages (OCR)
English, French, Spanish, German, Italian, Korean, Japanese, Chinese, Portuguese

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for mobile app)
- Google Cloud API key (Gemini)
- Qdrant Cloud account

### Backend Setup

```bash
# Clone repository
git clone https://github.com/udaytamma/AiIngredientScanner.git
cd AiIngredientScanner

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Verify connections
python test_connections.py

# Run tests
pytest

# Launch Streamlit UI
streamlit run app.py

# Or launch REST API (for mobile)
uvicorn api:app --host 0.0.0.0 --port 8000
```

### Mobile App Setup

```bash
cd mobile
npm install

# Update API URL in src/services/api.ts
# Replace with your machine's IP address

npx expo start
# Scan QR code with Expo Go app
```

---

## Architecture

### Multi-Agent Workflow

```
User Input → Supervisor → Research Agent → Analysis Agent → Critic Agent → Output
                ↑                                              ↓
                └──────────── Retry Loop (max 2) ←─────────────┘
```

### Agent Responsibilities

| Agent | Purpose |
|-------|---------|
| **Supervisor** | Routes workflow based on current state |
| **Research** | Fetches ingredient data (Qdrant + Google Search fallback) |
| **Analysis** | Generates personalized safety reports using Gemini |
| **Critic** | Validates report quality with 5-gate LLM checks |

### API Communication Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Mobile App  │────▶│  FastAPI     │────▶│  LangGraph   │
│  (Expo)      │◀────│  Backend     │◀────│  Workflow    │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐    ┌──────────────┐
│   Camera /   │     │  Gemini OCR  │    │   Qdrant     │
│   Gallery    │     │  + Translate │    │   Vector DB  │
└──────────────┘     └──────────────┘    └──────────────┘
```

---

## Project Structure

```
AiIngredientScanner/
├── app.py                      # Streamlit web interface
├── api.py                      # FastAPI REST endpoints
├── graph.py                    # LangGraph workflow orchestration
│
├── agents/
│   ├── supervisor.py           # Workflow routing logic
│   ├── research.py             # Ingredient data retrieval
│   ├── analysis.py             # Safety report generation
│   └── critic.py               # Quality validation (5-gate)
│
├── tools/
│   ├── ingredient_lookup.py    # Qdrant vector search
│   ├── grounded_search.py      # Google Search grounding
│   ├── safety_scorer.py        # Risk calculation utilities
│   └── allergen_matcher.py     # Allergy detection
│
├── prompts/
│   ├── analysis_prompts.py     # LLM prompts for analysis
│   ├── critic_prompts.py       # Validation prompts
│   └── grounded_search_prompts.py
│
├── state/
│   └── schema.py               # TypedDict state definitions
│
├── config/
│   ├── settings.py             # Environment configuration
│   ├── logging_config.py       # Structured logging setup
│   └── gemini_logger.py        # LLM interaction logging
│
├── services/
│   └── session.py              # Redis session management
│
├── mobile/                     # React Native mobile app
│   ├── App.tsx                 # App entry point with auth flow
│   ├── src/
│   │   ├── components/         # UI components
│   │   ├── screens/            # App screens (Home, Login)
│   │   ├── context/            # Theme & Auth contexts
│   │   │   ├── ThemeContext.tsx    # Light/dark mode management
│   │   │   └── AuthContext.tsx     # Firebase auth state
│   │   ├── config/             # Firebase configuration
│   │   ├── services/           # API & OCR services
│   │   └── types/              # TypeScript definitions
│   └── assets/                 # App icons & images
│
├── tests/
│   ├── test_*.py               # Unit & integration tests
│   └── test_api.py             # API endpoint tests
│
└── docs/                       # Additional documentation
```

---

## API Reference

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/health` | GET | Service health status |
| `/ocr` | POST | Extract ingredients from image (with translation) |
| `/analyze` | POST | Analyze ingredients for safety |

### OCR Endpoint

**Request:**
```json
POST /ocr
{
  "image": "<base64_encoded_image>"
}
```

**Response:**
```json
{
  "success": true,
  "text": "Water, Glycerin, Sodium Lauryl Sulfate...",
  "error": null
}
```

### Analyze Endpoint

**Request:**
```json
POST /analyze
{
  "product_name": "CeraVe Moisturizer",
  "ingredients": "Water, Glycerin, Cetearyl Alcohol...",
  "allergies": ["Fragrance", "Parabens"],
  "skin_type": "sensitive",
  "expertise": "beginner"
}
```

**Response:**
```json
{
  "success": true,
  "product_name": "CeraVe Moisturizer",
  "overall_risk": "low",
  "average_safety_score": 8,
  "summary": "...",
  "allergen_warnings": [],
  "ingredients": [...],
  "execution_time": 12.5
}
```

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google Gemini API key | Yes |
| `QDRANT_URL` | Qdrant Cloud cluster URL | Yes |
| `QDRANT_API_KEY` | Qdrant API key | Yes |
| `REDIS_URL` | Redis connection string | Optional |
| `LANGCHAIN_API_KEY` | LangSmith API key (tracing) | Optional |

### Firebase Configuration (Mobile App)

Firebase credentials are configured in `mobile/src/config/firebase.ts`. Required for:
- Google Sign-In authentication
- Firestore user profile storage
- Firebase Analytics

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **LLM** | Google Gemini 2.0 Flash |
| **Orchestration** | LangGraph |
| **Vector DB** | Qdrant Cloud |
| **Session Cache** | Redis Cloud |
| **Tracing** | LangSmith |
| **Web UI** | Streamlit |
| **Mobile App** | React Native + Expo |
| **Authentication** | Firebase Auth (Google Sign-In) |
| **User Data** | Firestore |
| **REST API** | FastAPI |
| **Deployment** | Railway (API), Cloudflare Pages (Web) |

---

## Development

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test file
pytest tests/test_api.py -v
```

### Code Quality

```bash
# Type checking
mypy .

# Linting
ruff check .

# Formatting
black .
```

---

## Version History

| Version | Description |
|---------|-------------|
| v3.0.0 | Firebase Authentication, user profiles, premium login UI |
| v2.0.0 | Mobile app, REST API, multi-language OCR |
| v1.0.0 | Initial release with Streamlit web interface |

---

## Documentation

- [Phase 1 PRD](../Documentation/AI_Ingredient_Scanner_PRD.md) - Web application
- [Phase 2 PRD](../Documentation/AI_Ingredient_Scanner_Phase2_PRD.md) - Mobile application
- [Mobile App README](mobile/README.md) - Mobile setup guide

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Google Gemini for LLM capabilities
- Qdrant for vector database
- LangGraph for workflow orchestration
- Expo for cross-platform mobile development
