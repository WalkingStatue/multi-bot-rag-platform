@echo off
setlocal

echo Multi-Bot RAG Platform Test Runner
echo ==================================

if "%1"=="local" goto run_local
if "%1"=="cleanup" goto cleanup
if "%1"=="help" goto help

:run_docker
echo Running tests in Docker environment...

echo Starting test database services...
docker-compose -f docker-compose.test.yml up -d postgres-test-1 redis-test-1 qdrant-test-1

echo Waiting for services to be ready...
timeout /t 15 /nobreak > nul

echo Running tests...
docker-compose -f docker-compose.test.yml run --rm backend-test

echo Cleaning up test services...
docker-compose -f docker-compose.test.yml down -v
goto end

:run_local
echo Running tests locally...

echo Starting test database...
docker-compose -f docker-compose.test.yml up -d postgres-test-1 redis-test-1 qdrant-test-1

echo Waiting for database to be ready...
timeout /t 15 /nobreak > nul

echo Running tests locally...
cd backend
python -m pytest -v --tb=short
cd ..
goto end

:cleanup
echo Cleaning up test services...
docker-compose -f docker-compose.test.yml down -v
goto end

:help
echo Usage: %0 [docker^|local^|cleanup^|help]
echo   docker  - Run tests in Docker containers (default)
echo   local   - Run tests locally with Docker database
echo   cleanup - Stop and remove test services
echo   help    - Show this help message
goto end

:end
echo Done!