# Multi-Bot RAG Platform

A comprehensive full-stack multi-bot assistant platform that enables users to create, manage, and collaborate on AI-powered chatbots with document-based knowledge retrieval (RAG). The platform supports multiple LLM providers, role-based access control, and real-time collaboration features.

## Features

- **Multi-LLM Support**: Configure different LLM providers (OpenAI, Anthropic, OpenRouter, Gemini) for each bot
- **Complete Data Isolation**: Each bot operates with isolated data including conversations, documents, and vector embeddings
- **Role-Based Collaboration**: Sophisticated permission system (Owner, Admin, Editor, Viewer) for secure bot sharing
- **Comprehensive Tracking**: All conversations are logged and searchable across all bots with analytics
- **Document-Enhanced AI**: Upload PDFs/TXT files to enhance bot knowledge through RAG

## Prerequisites

**Required Software:**
1. **Docker Desktop**: Download from [docker.com](https://www.docker.com/products/docker-desktop/)
2. **Git**: Download from [git-scm.com](https://git-scm.com/downloads)
3. **VS Code** (Optional): With Docker and Remote-Containers extensions

That's it! No need to install Python, Node.js, PostgreSQL, or Redis locally.

## Quick Start

1. **Clone the repository**:
```bash
git clone <repository-url>
cd multi-bot-rag-platform
```

2. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env file with your configuration
```

3. **Start the entire application**:
```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

4. **Access your application**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- PostgreSQL: localhost:5433
- Redis: localhost:6380
- Qdrant: http://localhost:6335

## Development Commands

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop all services
docker-compose down

# Rebuild specific service
docker-compose build backend
docker-compose up backend

# Run tests
docker-compose exec backend pytest
docker-compose exec frontend npm test

# Access container shell
docker-compose exec backend bash
docker-compose exec frontend sh
```

## Production Deployment

```bash
# Production build and deploy
docker-compose -f docker-compose.prod.yml up -d --build

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale backend=3 --scale frontend=2
```

## Architecture

### Services

- **Frontend**: React + TypeScript with Vite
- **Backend**: FastAPI + Python with async support
- **Database**: PostgreSQL 15 with JSONB support
- **Cache**: Redis for session storage and rate limiting
- **Vector Store**: Qdrant for embeddings and similarity search
- **Reverse Proxy**: Nginx (production only)

### Project Structure

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
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Docker configuration
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Page-level components
│   │   ├── services/       # API and external services
│   │   └── utils/          # Utility functions
│   ├── package.json        # Node.js dependencies
│   └── Dockerfile         # Docker configuration
├── docker-compose.yml      # Development environment
├── docker-compose.prod.yml # Production environment
└── .env.example           # Environment variables template
```

## Environment Variables

Key environment variables (see `.env.example` for complete list):

```env
# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/multi_bot_rag

# Redis
REDIS_URL=redis://redis:6379

# Vector Store
QDRANT_URL=http://qdrant:6333

# Security
SECRET_KEY=your-secret-key-here

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## API Key Configuration

Users configure their own API keys through the application:

- **OpenAI**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Anthropic**: [console.anthropic.com](https://console.anthropic.com/)
- **Google Gemini**: [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
- **OpenRouter**: [openrouter.ai/keys](https://openrouter.ai/keys)

## Health Checks

All services include health checks:

- Backend: `curl http://localhost:8000/health`
- Frontend: `curl http://localhost:3000`
- PostgreSQL: `pg_isready -U postgres`
- Redis: `redis-cli ping`
- Qdrant: `curl http://localhost:6333/health`

## Troubleshooting

### Common Issues

1. **Port conflicts**: Make sure ports 3000, 8000, 5432, 6379, and 6333 are available
2. **Docker issues**: Restart Docker Desktop and try again
3. **Build failures**: Clear Docker cache with `docker system prune -a`

### Logs

Check service logs for debugging:
```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `docker-compose exec backend pytest`
5. Submit a pull request

## License

This project is licensed under the MIT License.