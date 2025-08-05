# Development Tools

## Structure

- `dev/` - Debug scripts and development utilities

## Debug Scripts

The `dev/` directory contains debugging utilities:

- `debug_chat.py` - Chat system debugging
- `debug_routes.py` - API route debugging  
- `debug-document-service.py` - Document processing debugging

## Usage

These scripts are meant to be run within the Docker environment:

```powershell
# Run a debug script
docker compose exec backend python /app/../tools/dev/debug_chat.py
```

Or copy them into the backend container for easier access during development.