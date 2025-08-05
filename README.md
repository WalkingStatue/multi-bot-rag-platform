# Multi-Bot RAG Platform

A comprehensive full-stack multi-bot assistant platform that enables users to create, manage, and collaborate on AI-powered chatbots with document-based knowledge retrieval (RAG).

## 🚀 Quick Start (Windows)

### Prerequisites

- **Docker Desktop** - [Download here](https://www.docker.com/products/docker-desktop)
- **Git** - [Download here](https://git-scm.com/download/win)
- **PowerShell 5.1+** (included with Windows 10/11)

### Development Setup

1. **Clone the repository**
   ```powershell
   git clone <repository-url>
   cd multi-bot-rag-platform
   ```

2. **Run the setup script**
   ```powershell
   # Using PowerShell (recommended)
   .\scripts\dev-setup.ps1
   
   # Or using batch file
   .\scripts\dev-setup.bat
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 🏗️ Architecture

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | React + TypeScript + Vite | Modern UI with real-time updates |
| **Backend** | FastAPI + Python | RESTful API with async support |
| **Database** | PostgreSQL 15 | Relational data with JSONB support |
| **Cache** | Redis 7 | Session cache and rate limiting |
| **Vector DB** | Qdrant | Embeddings and similarity search |
| **Reverse Proxy** | Nginx | Load balancing and SSL termination |

### Key Features

- 🤖 **Multi-LLM Support** - OpenAI, Anthropic, OpenRouter, Gemini
- 🔒 **Complete Data Isolation** - Each bot operates with isolated data
- 👥 **Role-Based Collaboration** - Owner, Admin, Editor, Viewer permissions
- 📊 **Comprehensive Tracking** - All conversations logged and searchable
- 📄 **Document-Enhanced AI** - Upload PDFs/TXT for RAG functionality
- ⚡ **Real-time Updates** - WebSocket-based live collaboration

## 🐳 Single Docker Environment

**Quick start:**
```powershell
.\scripts\dev-setup.ps1
```

**With database setup:**
```powershell
.\scripts\dev-setup.ps1 -Build -Migrate -Seed
```

**Services:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000  
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- Qdrant: http://localhost:6333

**Useful commands:**
```powershell
# View logs
docker compose logs -f

# Restart a service
docker compose restart backend

# Run database migrations
docker compose exec backend alembic upgrade head

# Stop environment
docker compose down
```

## 🔧 Configuration

### Environment File

Single `.env` file for all environments:
- Copy from `config/.env.example`
- Modify values as needed

### Key Configuration Options

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/multi_bot_rag

# Redis
REDIS_URL=redis://redis:6379

# Vector Database
QDRANT_URL=http://qdrant:6333

# Security
SECRET_KEY=your-very-long-secret-key

# File Storage
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=10485760

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## 🧪 Testing

### Test Structure

```
tests/
├── integration/    # Integration tests for API endpoints
backend/tests/      # Backend unit tests
```

### Running Tests

```powershell
# All tests
.\scripts\test-runner.ps1

# Backend only
.\scripts\test-runner.ps1 -TestType backend

# Frontend only
.\scripts\test-runner.ps1 -TestType frontend

# With coverage
.\scripts\test-runner.ps1 -Coverage
```

### Test Reports

Coverage reports are available in `test-coverage/` when using the `-Coverage` flag.

## 📊 Monitoring

```powershell
# View logs
docker compose logs -f

# Monitor resource usage
docker stats

# Check service health
docker compose ps
```

## 🚀 Deployment

The single Docker Compose setup works for all environments. For production:

1. Update `.env` with production values
2. Run `docker compose up -d --build`
3. Configure reverse proxy/SSL as needed

## 🛠️ Development

### Project Structure

```
multi-bot-rag-platform/
├── backend/                # FastAPI Python backend
├── frontend/              # React TypeScript frontend
├── tests/                 # Integration tests
├── docs/                  # Documentation
├── scripts/               # Setup and utility scripts
├── tools/                 # Development tools
├── config/                # Configuration templates
├── docker-compose.yml     # Single Docker setup
└── README.md             # This file
```

See `docs/PROJECT_STRUCTURE.md` for detailed organization.

### Adding New Features

1. **Backend**: Add to `backend/app/`
2. **Frontend**: Add to `frontend/src/`
3. **Tests**: Add to appropriate test directories
4. **Documentation**: Update README and API docs

### Database Migrations

```powershell
# Create new migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker compose exec backend alembic upgrade head

# Rollback migration
docker compose exec backend alembic downgrade -1
```

## 📚 API Documentation

- **Development**: http://localhost:8000/docs
- **Production**: http://yourdomain.com/api/docs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `.\scripts\test-runner.ps1 -TestType all`
5. Submit a pull request

## 📄 License

[Your License Here]

## 🆘 Troubleshooting

### Common Issues

**Docker Desktop not running:**
```powershell
# Start Docker Desktop and wait for it to be ready
# Check with: docker --version
```

**Port conflicts:**
```powershell
# Check what's using the ports
netstat -an | findstr :3000
netstat -an | findstr :8000

# Stop conflicting services or change ports in docker-compose.yml
```

**Database connection issues:**
```powershell
# Reset database
docker compose down -v
docker compose up --build
```

**Permission issues:**
```powershell
# Run PowerShell as Administrator
# Or check Docker Desktop settings for file sharing
```

### Getting Help

- Check the logs: `docker compose logs -f [service]`
- Verify service health: `docker compose ps`
- Reset environment: `docker compose down -v && docker compose up --build`

For more help, please open an issue in the repository.