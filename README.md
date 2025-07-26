# Multi-Bot RAG Platform

A comprehensive full-stack multi-bot assistant platform that enables users to create, manage, and collaborate on AI-powered chatbots with document-based knowledge retrieval (RAG). The platform supports multiple LLM providers, role-based access control, and real-time collaboration features.

## Features

- **Multi-LLM Support**: Configure different LLM providers (OpenAI, Anthropic, OpenRouter, Gemini) for each bot with your own API keys
- **Complete Data Isolation**: Each bot operates with isolated data including conversations, documents, and vector embeddings
- **Role-Based Collaboration**: Sophisticated permission system (Owner, Admin, Editor, Viewer) for secure bot sharing
- **Comprehensive Tracking**: All conversations are logged and searchable across all bots with analytics
- **Document-Enhanced AI**: Upload PDFs/TXT files to enhance bot knowledge through RAG
- **Real-time Collaboration**: Live conversation updates via WebSockets

## Architecture

- **Frontend**: React + TypeScript with modern UI components
- **Backend**: FastAPI + Python for high-performance async API endpoints
- **Database**: PostgreSQL for relational data with JSONB support
- **Vector Store**: Qdrant for embeddings and similarity search
- **Cache**: Redis for session management and rate limiting
- **Real-time**: WebSocket connections for live updates

## Prerequisites

**Required Software:**
1. **Docker Desktop**: Download from [docker.com](https://www.docker.com/products/docker-desktop/)
2. **Git**: Download from [git-scm.com](https://git-scm.com/downloads)
3. **VS Code** (Optional): With Docker and Remote-Containers extensions

**That's it!** No need to install Python, Node.js, PostgreSQL, or Redis locally.

## Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd multi-bot-rag-platform
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services**:
   ```bash
   docker-compose up --build
   ```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Development Commands

```bash
# Start all services (first time)
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop all services
docker-compose down

# Rebuild specific service
docker-compose build backend
docker-compose up backend

# Database migrations
docker-compose exec backend alembic upgrade head

# Run tests
docker-compose exec backend pytest
docker-compose exec frontend npm test
```

## Project Structure

```
multi-bot-rag-platform/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── api/            # API route handlers
│   │   ├── core/           # Core application logic
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── services/       # Business logic services
│   │   └── utils/          # Utility functions
│   ├── tests/              # Test files
│   └── requirements.txt    # Python dependencies
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Page-level components
│   │   ├── services/       # API and external services
│   │   ├── stores/         # Zustand state management
│   │   └── utils/          # Utility functions
│   └── package.json        # Node.js dependencies
├── docker-compose.yml      # Development environment
├── docker-compose.prod.yml # Production environment
└── README.md              # This file
```

## API Key Configuration

Users configure their own API keys through the application:
- **OpenAI**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Anthropic**: [console.anthropic.com](https://console.anthropic.com/)
- **Google Gemini**: [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
- **OpenRouter**: [openrouter.ai/keys](https://openrouter.ai/keys)

Keys are encrypted using industry-standard encryption before database storage.

## Security Features

- JWT tokens with proper expiration and refresh
- API key encryption using Fernet encryption
- Input validation and sanitization
- Rate limiting and CORS configuration
- File upload security with type validation
- Role-based access control (RBAC)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue in the GitHub repository.