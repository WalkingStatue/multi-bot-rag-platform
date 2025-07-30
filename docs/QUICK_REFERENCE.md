# Quick Reference Guide

## Essential Commands

### Start/Stop Development Environment

```bash
# Start all services
docker-compose up -d

# Start with logs visible
docker-compose up

# Stop all services
docker-compose down

# Stop and remove volumes (reset everything)
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Rebuild Services

```bash
# Rebuild all services
docker-compose up --build

# Rebuild specific service
docker-compose build backend
docker-compose up backend
```

### Database Operations

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Access database
docker-compose exec postgres psql -U postgres -d multi_bot_rag

# Reset database
docker-compose down -v && docker-compose up --build
```

### Testing

```bash
# Backend tests
docker-compose exec backend pytest

# Frontend tests
docker-compose exec frontend npm test

# Tests with coverage
docker-compose exec backend pytest --cov=app
```

### Container Access

```bash
# Backend shell
docker-compose exec backend bash

# Frontend shell
docker-compose exec frontend sh

# Database shell
docker-compose exec postgres bash
```

## Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | React application |
| Backend API | http://localhost:8000 | FastAPI server |
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| PostgreSQL | localhost:5433 | Database (external access) |
| Redis | localhost:6380 | Cache (external access) |
| Qdrant | http://localhost:6335 | Vector database |

## File Structure Quick Reference

```
multi-bot-rag-platform/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── models/       # Database models
│   │   ├── services/     # Business logic
│   │   └── core/         # Configuration
│   ├── tests/            # Backend tests
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API calls
│   │   └── stores/       # State management
│   └── package.json      # Node dependencies
├── docker-compose.yml    # Development environment
└── .env                  # Environment variables
```

## Environment Variables

```env
# Core settings
DATABASE_URL=postgresql://postgres:password@postgres:5432/multi_bot_rag
REDIS_URL=redis://redis:6379
QDRANT_URL=http://qdrant:6333
SECRET_KEY=your-secret-key

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Common Issues & Solutions

### Port Conflicts
```bash
# Check what's using a port
netstat -tulpn | grep :8000

# Change ports in docker-compose.yml if needed
```

### Docker Issues
```bash
# Clear Docker cache
docker system prune -a

# Remove all containers and volumes
docker-compose down -v
docker system prune -a --volumes
```

### Permission Issues (Linux/macOS)
```bash
# Fix ownership
sudo chown -R $USER:$USER .
```

### Database Connection Issues
```bash
# Check PostgreSQL status
docker-compose ps postgres

# Reset database
docker-compose down -v
docker-compose up --build
```

## Development Workflow

1. **Start services**: `docker-compose up -d`
2. **Make changes** to code (auto-reloads)
3. **Check logs**: `docker-compose logs -f [service]`
4. **Run tests**: `docker-compose exec backend pytest`
5. **Stop services**: `docker-compose down`

## API Testing

```bash
# Health check
curl http://localhost:8000/health

# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

## Useful Docker Commands

```bash
# See running containers
docker ps

# See all containers
docker ps -a

# Remove stopped containers
docker container prune

# See images
docker images

# Remove unused images
docker image prune -a

# See volumes
docker volume ls

# Remove unused volumes
docker volume prune
```

## VS Code Tips

- Install Docker extension for container management
- Use Remote-Containers extension to develop inside containers
- Install Python and TypeScript extensions for better IntelliSense
- Use integrated terminal for Docker commands

## Performance Tips

1. **Allocate more resources to Docker**:
   - RAM: 4-6GB minimum
   - CPU: 4+ cores

2. **Use volume mounts** (already configured):
   - Faster file system operations
   - Persistent node_modules

3. **Restart specific services** instead of everything:
   ```bash
   docker-compose restart backend
   ```

## Debugging

### Backend (Python)
```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use logging
import logging
logging.info("Debug message")
```

### Frontend (React)
- Use browser DevTools
- Install React DevTools extension
- Check console for errors
- Use `console.log()` for debugging

## Production Checklist

Before deploying to production:

- [ ] Change `SECRET_KEY` in environment
- [ ] Update database credentials
- [ ] Configure proper CORS settings
- [ ] Set up SSL certificates
- [ ] Configure reverse proxy (Nginx)
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy

## Getting Help

1. Check service logs: `docker-compose logs [service]`
2. Verify all containers are running: `docker-compose ps`
3. Check the main README.md for detailed information
4. Review API documentation at http://localhost:8000/docs
5. Check GitHub issues or create a new one