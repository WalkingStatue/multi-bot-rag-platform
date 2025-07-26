# Docker Services Setup

## Running Services

The following Docker containers have been successfully set up and are running:

### PostgreSQL Database
- **Container Name**: `postgres`
- **Image**: `postgres:15-alpine`
- **Port**: `5432` (host) → `5432` (container)
- **Database**: `multi_bot_rag`
- **Username**: `postgres`
- **Password**: `password`
- **Network IP**: `172.18.0.2`
- **Status**: ✅ Running and accepting connections

### Redis Cache
- **Container Name**: `redis`
- **Image**: `redis:7-alpine`
- **Port**: `6379` (host) → `6379` (container)
- **Network IP**: `172.18.0.3`
- **Status**: ✅ Running and responding to ping

### Qdrant Vector Database
- **Container Name**: `qdrant`
- **Image**: `qdrant/qdrant:latest`
- **Ports**: 
  - `6333` (host) → `6333` (container) - HTTP API
  - `6334` (host) → `6334` (container) - gRPC API
- **Network IP**: `172.18.0.4`
- **Version**: `1.15.1`
- **Status**: ✅ Running and responding to HTTP requests

## Docker Network
- **Network Name**: `app-network`
- **Type**: Bridge network
- **Subnet**: `172.18.0.0/16`
- **Gateway**: `172.18.0.1`

## Connection Testing Results

All services have been tested and are working properly:

1. **PostgreSQL**: Connection test passed with `pg_isready`
2. **Redis**: Connection test passed with `redis-cli ping` returning `PONG`
3. **Qdrant**: HTTP API responding correctly on port 6333

## Usage Commands

### Check container status:
```bash
wsl docker ps
```

### View container logs:
```bash
wsl docker logs postgres
wsl docker logs redis
wsl docker logs qdrant
```

### Stop all services:
```bash
wsl docker stop postgres redis qdrant
```

### Start all services:
```bash
wsl docker start postgres redis qdrant
```

### Remove all containers (when done):
```bash
wsl docker rm -f postgres redis qdrant
wsl docker network rm app-network
```

## Environment Variables for Application

Use these connection strings in your application:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/multi_bot_rag
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333
```

For Docker-to-Docker communication (when running app in containers):
```env
DATABASE_URL=postgresql://postgres:password@postgres:5432/multi_bot_rag
REDIS_URL=redis://redis:6379
QDRANT_URL=http://qdrant:6333
```