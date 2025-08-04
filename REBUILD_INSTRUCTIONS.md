# Docker Container Rebuild Instructions

## Complete System Rebuild

Follow these steps to rebuild the entire multi-bot RAG platform with all the latest chat system improvements.

### 1. Stop and Clean Current Containers

```bash
# Navigate to project directory
cd multi-bot-rag-platform

# Stop all running containers
docker-compose down

# Remove all containers, networks, and volumes (CAUTION: This will delete all data)
docker-compose down -v --remove-orphans

# Clean up Docker system (optional - removes unused images, containers, networks)
docker system prune -f

# Remove specific images to force rebuild (optional)
docker rmi multi-bot-rag-platform_backend multi-bot-rag-platform_frontend
```

### 2. Rebuild and Start All Services

```bash
# Build and start all services (this will take several minutes)
docker-compose up --build

# Alternative: Build and run in background
docker-compose up --build -d
```

### 3. Monitor the Build Process

```bash
# Watch logs for all services
docker-compose logs -f

# Watch specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f qdrant
```

### 4. Verify Services are Running

```bash
# Check container status
docker-compose ps

# Expected output should show all services as "Up"
#     Name                    Command               State           Ports
# postgres_container    docker-entrypoint.sh postgres   Up      0.0.0.0:5432->5432/tcp
# redis_container       docker-entrypoint.sh redis ...  Up      0.0.0.0:6379->6379/tcp
# qdrant_container      ./entrypoint.sh                  Up      0.0.0.0:6333->6333/tcp
# backend_container     uvicorn main:app --host ...     Up      0.0.0.0:8000->8000/tcp
# frontend_container    npm run dev                      Up      0.0.0.0:3000->3000/tcp
```

### 5. Initialize Database (First Time Setup)

```bash
# Run database migrations
docker-compose exec backend alembic upgrade head

# Verify database is working
docker-compose exec backend python -c "
from app.core.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database connection successful:', result.fetchone())
"
```

### 6. Test the Application

```bash
# Test backend health
curl http://localhost:8000/health

# Expected response: {"status":"healthy"}

# Test frontend (open in browser)
# http://localhost:3000
```

### 7. Verify Chat System Improvements

1. **Open the application**: http://localhost:3000
2. **Create/Login to account**
3. **Create a new bot** with your API keys
4. **Start a chat session**
5. **Test the following features**:
   - Send messages (should work with REST API fallback)
   - Check connection status (should show WebSocket or REST API status)
   - Use Chat Diagnostics tool (click "Chat Diagnostics" in chat window)
   - Test rate limiting (send multiple rapid messages)
   - Verify error handling (try with invalid API keys)

### 8. Troubleshooting Common Issues

#### Backend Won't Start
```bash
# Check backend logs
docker-compose logs backend

# Common issues:
# - Database connection failed: Wait for postgres to fully start
# - Port already in use: Stop other services using port 8000
# - Environment variables missing: Check .env file
```

#### Frontend Won't Start
```bash
# Check frontend logs
docker-compose logs frontend

# Common issues:
# - Node modules not installed: Rebuild with --no-cache
# - Port already in use: Stop other services using port 3000
# - Environment variables missing: Check docker-compose.yml
```

#### Database Issues
```bash
# Reset database completely
docker-compose down -v
docker volume rm multi-bot-rag-platform_postgres_data
docker-compose up --build

# Check database logs
docker-compose logs postgres
```

#### WebSocket Connection Issues
```bash
# Test WebSocket endpoint directly
# Use browser console or WebSocket testing tool
# ws://localhost:8000/api/ws/chat/[BOT_ID]?token=[JWT_TOKEN]

# Check if backend WebSocket endpoint is accessible
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: test" http://localhost:8000/api/ws/chat/test
```

### 9. Performance Optimization (Optional)

```bash
# Build with production optimizations
docker-compose -f docker-compose.prod.yml up --build -d

# Monitor resource usage
docker stats

# Clean up unused resources
docker system prune -a
```

### 10. Development Mode (Optional)

```bash
# For development with hot reload
docker-compose up --build

# The volumes in docker-compose.yml enable:
# - Backend: Hot reload on Python file changes
# - Frontend: Hot reload on React file changes
```

## Expected Results After Rebuild

### ✅ What Should Work
- **Chat Interface**: Complete chat functionality
- **Rate Limit Handling**: Proper OpenRouter rate limit error messages
- **Connection Status**: Shows WebSocket or REST API fallback status
- **Error Display**: User-friendly error messages with retry options
- **Diagnostics**: Built-in chat diagnostics tool
- **Message Sending**: Optimistic updates with proper error recovery

### 🔧 Configuration Verification
- **Environment Variables**: 
  - `VITE_API_URL=http://localhost:8000`
  - `VITE_WS_URL=ws://localhost:8000`
- **Services**: All 5 services (postgres, redis, qdrant, backend, frontend) running
- **Ports**: 3000 (frontend), 8000 (backend), 5432 (postgres), 6379 (redis), 6333 (qdrant)

### 📊 Health Checks
- Backend: http://localhost:8000/health
- Frontend: http://localhost:3000
- Database: Accessible via backend
- WebSocket: ws://localhost:8000/api/ws/chat/[BOT_ID]

## Post-Rebuild Testing Checklist

- [ ] All containers are running (`docker-compose ps`)
- [ ] Backend health check passes (`curl http://localhost:8000/health`)
- [ ] Frontend loads in browser (`http://localhost:3000`)
- [ ] User registration/login works
- [ ] Bot creation works
- [ ] Chat interface loads
- [ ] Messages can be sent and received
- [ ] Connection status displays correctly
- [ ] Chat diagnostics tool works
- [ ] Rate limiting shows proper error messages
- [ ] Error handling works for various scenarios

## Need Help?

If you encounter issues during the rebuild:

1. **Check the logs**: `docker-compose logs [service_name]`
2. **Verify ports**: Make sure ports 3000, 8000, 5432, 6379, 6333 are available
3. **Clean rebuild**: Use `docker-compose down -v && docker-compose up --build --no-cache`
4. **Check resources**: Ensure sufficient disk space and memory
5. **Use diagnostics**: The built-in Chat Diagnostics tool can help identify issues

The rebuild should take 5-10 minutes depending on your system and internet connection.