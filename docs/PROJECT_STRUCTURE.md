# Project Structure

## Simplified Organization

This project uses a single, unified Docker Compose setup for all environments (development, testing, and production). No separate configurations needed.

```
multi-bot-rag-platform/
├── backend/                 # FastAPI Python backend
│   ├── app/                # Application code
│   ├── tests/              # Backend unit tests
│   ├── alembic/            # Database migrations
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile         # Backend container
│   └── main.py            # Application entry point
├── frontend/               # React TypeScript frontend
│   ├── src/               # Frontend source code
│   ├── public/            # Static assets
│   ├── package.json       # Node.js dependencies
│   ├── Dockerfile        # Frontend container
│   └── vite.config.ts    # Build configuration
├── tests/                 # Project-wide tests
│   └── integration/       # Integration tests
├── docs/                  # Documentation
│   ├── development/       # Development notes
│   └── PROJECT_STRUCTURE.md
├── scripts/               # Utility scripts
│   ├── dev-setup.ps1     # Main setup script
│   └── test-runner.ps1   # Test runner
├── tools/                 # Development tools
│   └── dev/              # Debug scripts
├── config/               # Configuration files
│   └── .env.example      # Environment template
├── docker-compose.yml    # Single Docker setup
├── .env                  # Environment variables
└── README.md            # Main documentation
```

## Key Scripts

### Setup & Development
```powershell
# Start everything
.\scripts\dev-setup.ps1

# With database migration
.\scripts\dev-setup.ps1 -Migrate

# Clean start with build
.\scripts\dev-setup.ps1 -Clean -Build -Migrate -Seed
```

### Testing
```powershell
# Run all tests
.\scripts\test-runner.ps1

# Run specific test types
.\scripts\test-runner.ps1 -TestType backend
.\scripts\test-runner.ps1 -TestType frontend

# With coverage
.\scripts\test-runner.ps1 -Coverage
```

### Docker Commands
```powershell
# Start services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Rebuild
docker compose up --build
```

## Environment Configuration

Single `.env` file for all environments:
- Copy from `config/.env.example`
- Modify values as needed
- Same file works for dev/test/prod

## File Organization Rules

- **Backend code**: `backend/app/`
- **Frontend code**: `frontend/src/`
- **Unit tests**: `backend/tests/`
- **Integration tests**: `tests/integration/`
- **Documentation**: `docs/`
- **Scripts**: `scripts/`
- **Debug tools**: `tools/dev/`

## No Multiple Environments

This project intentionally uses a single Docker Compose setup instead of separate dev/test/prod configurations for simplicity and maintainability.