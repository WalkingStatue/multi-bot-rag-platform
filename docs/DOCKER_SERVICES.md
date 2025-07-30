# Docker Services Guide

## Overview

This project uses Docker Compose to orchestrate multiple services for the Multi-Bot RAG Platform. All services are containerized and can be run with a single command.

## Services Architecture

### Core Application Services
- **Backend** (Port 8000): FastAPI Python application
- **Frontend** (Port 3000): React TypeScript application with Vite

### Infrastructure Services
- **PostgreSQL** (Port 5432): Primary database for user data, bots, conversations
- **Redis** (Port 6379): Caching and session storage
- **Qdrant** (Port 6333): Vector database for embeddings and similarity search

### Production Services
- **Nginx** (Port 80/443): Reverse proxy and load balancer (production only)

## Quick Start Commands

### For WSL/Linux Environment

```bash
# Navigate to project directory
cd multi-bot-rag-platform

# Start all services (first time)
docker compose up --build

# Start in background
docker compose up -d --build

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Stop all services
docker compose down

# Rebuild specific service
docker compose build backend
docker compose up backend
```

### Service Health Checks

All services include health checks that can be verified:

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend (after build)
curl http://localhost:3000

# Check PostgreSQL
docker compose exec postgres pg_isready -U postgres

# Check Redis
docker compose exec redis redis-cli ping

# Check Qdrant
curl http://localhost:6333/health
```

## Development Workflow

### 1. Initial Setup
```bash
# Copy environment file
cp .env.example .env

# Edit environment variables as needed
nano .env

# Start all services
docker compose up --build
```

### 2. Development Commands
```bash
# View real-time logs
docker compose logs -f

# Access container shell
docker compose exec backend bash
docker compose exec frontend sh

# Run tests
docker compose exec backend pytest
docker compose exec frontend npm test

# Database migrations
docker compose exec backend alembic upgrade head
```

### 3. Troubleshooting
```bash
# Restart specific service
docker compose restart backend

# Rebuild without cache
docker compose build --no-cache backend

# Clean up everything
docker compose down -v
docker system prune -a
```

## Production Deployment

### Using Production Compose File
```bash
# Set production environment variables
cp .env.example .env.prod
# Edit .env.prod with production values

# Deploy with production configuration
docker compose -f docker-compose.prod.yml up -d --build

# Scale services
docker compose -f docker-compose.prod.yml up -d --scale backend=3 --scale frontend=2

# View production logs
docker compose -f docker-compose.prod.yml logs -f
```

## Port Mapping

| Service | Internal Port | External Port | Description |
|---------|---------------|---------------|-------------|
| Frontend | 3000 | 3000 | React development server |
| Backend | 8000 | 8000 | FastAPI application |
| PostgreSQL | 5432 | 5433 | Database connection |
| Redis | 6379 | 6380 | Cache and sessions |
| Qdrant | 6333 | 6335 | Vector database API |
| Qdrant gRPC | 6334 | 6336 | Vector database gRPC |
| Nginx | 80/443 | 80/443 | Reverse proxy (prod only) |

## Volume Mounts

### Development Volumes
- `./backend:/app` - Backend code hot-reload
- `./frontend:/app` - Frontend code hot-reload
- `postgres_data` - Database persistence
- `redis_data` - Redis persistence
- `qdrant_data` - Vector database persistence
- `backend_uploads` - File uploads storage

### Production Volumes
- `postgres_data` - Database persistence
- `redis_data` - Redis persistence
- `qdrant_data` - Vector database persistence
- `backend_uploads` - File uploads storage

## Environment Variables

### Required Variables
```env
DATABASE_URL=postgresql://postgres:password@postgres:5432/multi_bot_rag
REDIS_URL=redis://redis:6379
QDRANT_URL=http://qdrant:6333
SECRET_KEY=your-secret-key-here
FRONTEND_URL=http://localhost:3000
```

### Frontend Variables
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Network Configuration

All services communicate through a custom Docker network (`app-network`) which provides:
- Service discovery by name (e.g., `backend`, `postgres`, `redis`)
- Isolation from other Docker networks
- Internal DNS resolution

## Data Persistence

### Development
- Database data persists between container restarts
- Redis data persists between container restarts
- Vector database data persists between container restarts
- Uploaded files persist in named volume

### Production
- All data volumes are persistent
- Regular backups should be configured
- Consider using external storage for uploads

## Security Considerations

### Development
- Default passwords are used (change for production)
- All ports are exposed for debugging
- Debug mode enabled

### Production
- Strong passwords required
- Only necessary ports exposed through Nginx
- Security headers configured
- Rate limiting enabled

## Monitoring and Logs

### Log Locations
```bash
# Application logs
docker compose logs backend
docker compose logs frontend

# Infrastructure logs
docker compose logs postgres
docker compose logs redis
docker compose logs qdrant
```

### Health Monitoring
All services include health checks that report status:
- Backend: HTTP health endpoint
- Frontend: HTTP availability check
- PostgreSQL: Connection test
- Redis: Ping command
- Qdrant: Health endpoint

## Common Issues and Solutions

### Port Conflicts
If ports are already in use:
```bash
# Check what's using the port
netstat -tulpn | grep :8000

# Stop conflicting services or change ports in docker-compose.yml
```

### Permission Issues
If you encounter permission issues:
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Or run with sudo (not recommended)
sudo docker compose up
```

### Build Failures
If builds fail:
```bash
# Clear Docker cache
docker system prune -a

# Rebuild from scratch
docker compose build --no-cache
```

### Database Connection Issues
If backend can't connect to database:
```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Check database logs
docker compose logs postgres

# Verify connection string in .env file
```

This Docker setup provides a complete development and production environment that can be run with minimal setup on any system with Docker installed.