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

## 🐳 Docker Environments

### Development Environment

**Start development environment:**
```powershell
docker compose up --build
```

**Services:**
- Frontend: http://localhost:3000 (with hot reload)
- Backend: http://localhost:8000 (with auto-reload)
- PostgreSQL: localhost:5433
- Redis: localhost:6380
- Qdrant: http://localhost:6335

**Useful commands:**
```powershell
# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Restart a service
docker compose restart backend

# Run database migrations
docker compose exec backend alembic upgrade head

# Access database
docker compose exec postgres psql -U postgres -d multi_bot_rag_dev

# Stop environment
docker compose down
```

### Testing Environment

**Run all tests:**
```powershell
.\scripts\test-runner.ps1 -TestType all -Coverage
```

**Run specific test types:**
```powershell
# Unit tests only
.\scripts\test-runner.ps1 -TestType unit

# Integration tests only
.\scripts\test-runner.ps1 -TestType integration

# Frontend tests only
.\scripts\test-runner.ps1 -TestType frontend

# End-to-end tests only
.\scripts\test-runner.ps1 -TestType e2e
```

**Manual test environment:**
```powershell
# Start test services
docker compose -f docker-compose.test.yml up --build

# Run specific tests
docker compose -f docker-compose.test.yml run --rm backend-unit-test
docker compose -f docker-compose.test.yml run --rm frontend-test

# Clean up
docker compose -f docker-compose.test.yml down --volumes
```

### Production Environment

**Setup production environment:**

1. **Create production configuration:**
   ```powershell
   copy .env.prod.example .env.prod
   # Edit .env.prod with your production settings
   ```

2. **Deploy to production:**
   ```powershell
   # Full deployment with build and migrations
   .\scripts\prod-deploy.ps1 -Build -Migrate -Scale -BackendReplicas 3 -FrontendReplicas 2

   # Quick deployment (existing images)
   .\scripts\prod-deploy.ps1

   # With monitoring enabled
   .\scripts\prod-deploy.ps1 -Monitor
   ```

**Production services:**
- Application: http://localhost (or your domain)
- API Documentation: http://localhost/api/docs

**Production management:**
```powershell
# View production logs
docker compose -f docker-compose.prod.yml logs -f

# Scale services
docker compose -f docker-compose.prod.yml up -d --scale backend=4 --scale frontend=3

# Update deployment
docker compose -f docker-compose.prod.yml up -d --build

# Stop production
docker compose -f docker-compose.prod.yml down
```

## 🔧 Configuration

### Environment Files

- **`.env.dev`** - Development configuration (auto-loaded)
- **`.env.test`** - Testing configuration (auto-loaded)
- **`.env.prod`** - Production configuration (create from `.env.prod.example`)

### Key Configuration Options

```bash
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Redis
REDIS_URL=redis://host:port
REDIS_PASSWORD=your_password

# Vector Database
QDRANT_URL=http://host:port

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
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for API endpoints
├── frontend/       # Frontend component and integration tests
└── e2e/           # End-to-end user workflow tests
```

### Running Tests

```powershell
# All tests with coverage
.\scripts\test-runner.ps1 -TestType all -Coverage -Verbose

# Quick unit tests
.\scripts\test-runner.ps1 -TestType unit

# Integration tests
.\scripts\test-runner.ps1 -TestType integration

# Frontend tests
.\scripts\test-runner.ps1 -TestType frontend

# End-to-end tests
.\scripts\test-runner.ps1 -TestType e2e
```

### Test Reports

Test results are available in:
- **Reports**: `test-reports/` (JUnit XML format)
- **Coverage**: `test-coverage/` (HTML reports)

## 📊 Monitoring & Logging

### Development Monitoring

```powershell
# View real-time logs
docker compose logs -f

# Monitor resource usage
docker stats

# Check service health
docker compose ps
```

### Production Monitoring

```powershell
# Production logs
docker compose -f docker-compose.prod.yml logs -f

# Service health check
docker compose -f docker-compose.prod.yml ps

# Resource monitoring
docker stats
```

### Log Locations

- **Backend logs**: `backend/logs/`
- **Frontend logs**: `frontend/logs/`
- **Nginx logs**: `nginx/logs/`
- **Database logs**: Available via `docker compose logs postgres`

## 🔒 Security

### Development Security

- Default passwords (change for production)
- CORS enabled for localhost
- Debug mode enabled
- Detailed error messages

### Production Security

- Strong passwords required
- CORS restricted to your domain
- Security headers enabled
- Rate limiting configured
- SSL/TLS support (configure certificates)

### Security Checklist

- [ ] Change all default passwords
- [ ] Configure strong SECRET_KEY
- [ ] Set up SSL certificates
- [ ] Configure CORS for your domain
- [ ] Enable rate limiting
- [ ] Review security headers
- [ ] Set up monitoring and alerting

## 🚀 Deployment

### Local Development

```powershell
# Start development environment
.\scripts\dev-setup.ps1

# Or manually
docker compose up --build
```

### Production Deployment

```powershell
# Full production deployment
.\scripts\prod-deploy.ps1 -Build -Migrate -Scale -BackendReplicas 3

# Quick update
.\scripts\prod-deploy.ps1 -Build
```

### Cloud Deployment

The Docker Compose files can be adapted for cloud deployment:

- **AWS**: Use ECS with the compose files
- **Azure**: Use Container Instances or AKS
- **Google Cloud**: Use Cloud Run or GKE
- **DigitalOcean**: Use App Platform or Droplets

## 🛠️ Development

### Project Structure

```
multi-bot-rag-platform/
├── backend/                 # FastAPI Python backend
├── frontend/               # React TypeScript frontend
├── nginx/                  # Nginx configuration
├── scripts/                # Deployment and utility scripts
├── docker-compose.yml      # Development environment
├── docker-compose.prod.yml # Production environment
├── docker-compose.test.yml # Testing environment
└── README.md              # This file
```

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