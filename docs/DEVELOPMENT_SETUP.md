# Development Setup Guide

This guide will help you set up the Multi-Bot RAG Platform development environment on a new PC from scratch.

## Prerequisites

### Required Software

1. **Docker Desktop**
   - Download from [docker.com](https://www.docker.com/products/docker-desktop/)
   - Install and ensure it's running
   - Verify installation: `docker --version` and `docker-compose --version`

2. **Git**
   - Download from [git-scm.com](https://git-scm.com/downloads)
   - Configure your Git credentials:
     ```bash
     git config --global user.name "Your Name"
     git config --global user.email "your.email@example.com"
     ```

3. **Code Editor (Recommended)**
   - **VS Code**: Download from [code.visualstudio.com](https://code.visualstudio.com/)
   - Install these extensions:
     - Docker
     - Remote - Containers
     - Python
     - TypeScript and JavaScript Language Features
     - Tailwind CSS IntelliSense

### System Requirements

- **RAM**: Minimum 8GB (16GB recommended)
- **Storage**: At least 5GB free space
- **OS**: Windows 10/11, macOS, or Linux
- **Ports**: Ensure these ports are available:
  - 3000 (Frontend)
  - 8000 (Backend API)
  - 5433 (PostgreSQL)
  - 6380 (Redis)
  - 6335 (Qdrant)

## Step-by-Step Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone <your-repository-url>
cd multi-bot-rag-platform

# Verify you're in the right directory
ls -la
# You should see: backend/, frontend/, docker-compose.yml, etc.
```

### 2. Environment Configuration

```bash
# Copy the environment template
cp .env.example .env

# Edit the .env file with your preferred editor
# For development, the default values should work fine
```

**Important Environment Variables to Review:**

```env
# Security - Change this for production
SECRET_KEY=your-secret-key-here-change-in-production

# Database credentials (default is fine for development)
POSTGRES_PASSWORD=password

# Frontend URL (should match your local setup)
FRONTEND_URL=http://localhost:3000
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### 3. Start the Development Environment

```bash
# Build and start all services (first time)
docker-compose up --build

# This will:
# - Build the backend Docker image
# - Build the frontend Docker image
# - Start PostgreSQL database
# - Start Redis cache
# - Start Qdrant vector database
# - Run database migrations
# - Start the development servers
```

**Expected Output:**
- Backend will be available at: http://localhost:8000
- Frontend will be available at: http://localhost:3000
- API docs will be available at: http://localhost:8000/docs

### 4. Verify Installation

Open your browser and check:

1. **Frontend**: http://localhost:3000
   - Should show the application login/register page

2. **Backend API**: http://localhost:8000/docs
   - Should show the FastAPI interactive documentation

3. **Health Checks**:
   ```bash
   # Check backend health
   curl http://localhost:8000/health
   
   # Check if all containers are running
   docker-compose ps
   ```

## Development Workflow

### Daily Development Commands

```bash
# Start services (after initial setup)
docker-compose up -d

# View logs in real-time
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop all services
docker-compose down

# Restart a specific service
docker-compose restart backend
docker-compose restart frontend
```

### Making Code Changes

The development setup includes hot reloading:

- **Backend**: Changes to Python files will automatically restart the FastAPI server
- **Frontend**: Changes to React/TypeScript files will automatically refresh the browser

### Database Operations

```bash
# Run database migrations
docker-compose exec backend alembic upgrade head

# Create a new migration (after model changes)
docker-compose exec backend alembic revision --autogenerate -m "Description of changes"

# Access PostgreSQL directly
docker-compose exec postgres psql -U postgres -d multi_bot_rag

# Reset database (WARNING: This will delete all data)
docker-compose down -v
docker-compose up --build
```

### Running Tests

```bash
# Backend tests
docker-compose exec backend pytest

# Frontend tests
docker-compose exec frontend npm test

# Run tests with coverage
docker-compose exec backend pytest --cov=app
```

### Accessing Container Shells

```bash
# Access backend container
docker-compose exec backend bash

# Access frontend container
docker-compose exec frontend sh

# Access database container
docker-compose exec postgres bash
```

## IDE Setup (VS Code)

### Recommended Extensions

Install these VS Code extensions for the best development experience:

```json
{
  "recommendations": [
    "ms-vscode.vscode-docker",
    "ms-vscode-remote.remote-containers",
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.isort",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next"
  ]
}
```

### VS Code Settings

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "/usr/local/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Find what's using the port
   netstat -tulpn | grep :8000
   
   # Kill the process or change ports in docker-compose.yml
   ```

2. **Docker Build Failures**
   ```bash
   # Clear Docker cache
   docker system prune -a
   
   # Rebuild from scratch
   docker-compose down -v
   docker-compose up --build
   ```

3. **Database Connection Issues**
   ```bash
   # Check if PostgreSQL is running
   docker-compose ps postgres
   
   # Check PostgreSQL logs
   docker-compose logs postgres
   
   # Reset database
   docker-compose down -v
   docker volume rm multi-bot-rag-platform_postgres_data
   docker-compose up --build
   ```

4. **Frontend Not Loading**
   ```bash
   # Check frontend logs
   docker-compose logs frontend
   
   # Rebuild frontend
   docker-compose build frontend
   docker-compose up frontend
   ```

5. **Permission Issues (Linux/macOS)**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   
   # Or run Docker with sudo (not recommended)
   sudo docker-compose up --build
   ```

### Performance Optimization

1. **Increase Docker Resources**
   - Open Docker Desktop settings
   - Increase RAM allocation to 4-6GB
   - Increase CPU allocation to 4+ cores

2. **Use Docker Volumes for Node Modules**
   - Already configured in docker-compose.yml
   - Prevents slow file system operations

### Debugging

1. **Backend Debugging**
   ```bash
   # Add breakpoints in your Python code
   import pdb; pdb.set_trace()
   
   # Attach to running container
   docker-compose exec backend bash
   ```

2. **Frontend Debugging**
   - Use browser developer tools
   - React DevTools extension
   - Check console for errors

## API Key Setup

Once the application is running, you'll need to configure API keys for LLM providers:

1. **Create an account and get API keys from:**
   - OpenAI: https://platform.openai.com/api-keys
   - Anthropic: https://console.anthropic.com/
   - Google Gemini: https://makersuite.google.com/app/apikey
   - OpenRouter: https://openrouter.ai/keys

2. **Add keys in the application:**
   - Register/login to your local instance
   - Go to Profile/Settings
   - Add your API keys for the providers you want to use

## Next Steps

After successful setup:

1. **Explore the codebase structure** (see `ARCHITECTURE.md`)
2. **Read the API documentation** at http://localhost:8000/docs
3. **Create your first bot** through the web interface
4. **Upload some documents** to test RAG functionality
5. **Check the development tasks** in `.kiro/specs/multi-bot-rag-system/tasks.md`

## Getting Help

- Check the main `README.md` for general information
- Review `DOCKER_SERVICES.md` for service-specific details
- Look at the API documentation at http://localhost:8000/docs
- Check container logs: `docker-compose logs [service-name]`

## Production Deployment

For production deployment, see the production section in the main README.md and use:

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

---

**Happy coding! 🚀**