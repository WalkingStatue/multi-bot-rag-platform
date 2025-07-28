@echo off
echo ================================
echo Multi-Bot RAG Platform Services Test
echo ================================
echo.

echo ================================
echo Testing PostgreSQL Containers
echo ================================

echo Testing Main Platform PostgreSQL (Port 5433)...
docker-compose exec postgres pg_isready -U postgres
if %errorlevel% equ 0 (
    echo ✓ Main PostgreSQL is healthy
    docker-compose exec postgres psql -U postgres -d multi_bot_rag -c "SELECT 'Main DB' as service, current_database() as database;"
) else (
    echo ✗ Main PostgreSQL is not healthy
)

echo.
echo Testing Test PostgreSQL (Port 5434)...
docker-compose -f docker-compose.test.yml exec postgres-test pg_isready -U postgres
if %errorlevel% equ 0 (
    echo ✓ Test PostgreSQL is healthy
    docker-compose -f docker-compose.test.yml exec postgres-test psql -U postgres -d multi_bot_rag_test -c "SELECT 'Test DB' as service, current_database() as database;"
) else (
    echo ✗ Test PostgreSQL is not healthy
)

echo.
echo ================================
echo Testing Redis Containers
echo ================================

echo Testing Main Platform Redis (Port 6380)...
docker-compose exec redis redis-cli ping
if %errorlevel% equ 0 (
    echo ✓ Main Redis is healthy
    docker-compose exec redis redis-cli set test_main_key "main_platform_redis" EX 60
    docker-compose exec redis redis-cli get test_main_key
    docker-compose exec redis redis-cli del test_main_key
) else (
    echo ✗ Main Redis is not healthy
)

echo.
echo Testing Test Redis (Port 6381)...
docker-compose -f docker-compose.test.yml exec redis-test redis-cli ping
if %errorlevel% equ 0 (
    echo ✓ Test Redis is healthy
    docker-compose -f docker-compose.test.yml exec redis-test redis-cli set test_env_key "test_environment_redis" EX 60
    docker-compose -f docker-compose.test.yml exec redis-test redis-cli get test_env_key
    docker-compose -f docker-compose.test.yml exec redis-test redis-cli del test_env_key
) else (
    echo ✗ Test Redis is not healthy
)

echo.
echo ================================
echo Testing Qdrant Containers
echo ================================

echo Testing Main Platform Qdrant (Port 6335)...
curl -s -o nul -w "HTTP Status: %%{http_code}" http://localhost:6335/
if %errorlevel% equ 0 (
    echo.
    echo ✓ Main Qdrant is healthy
    curl -s -X GET "http://localhost:6335/" | findstr /C:"title"
) else (
    echo ✗ Main Qdrant is not healthy
)

echo.
echo Testing Test Qdrant (Port 6337)...
curl -s -o nul -w "HTTP Status: %%{http_code}" http://localhost:6337/
if %errorlevel% equ 0 (
    echo.
    echo ✓ Test Qdrant is healthy
    curl -s -X GET "http://localhost:6337/" | findstr /C:"title"
) else (
    echo ✗ Test Qdrant is not healthy
)

echo.
echo ================================
echo Service Summary
echo ================================
echo.
echo MAIN PLATFORM SERVICES:
echo - PostgreSQL: localhost:5433 (multi_bot_rag)
echo - Redis: localhost:6380
echo - Qdrant: localhost:6335
echo.
echo TEST ENVIRONMENT SERVICES:
echo - PostgreSQL: localhost:5434 (multi_bot_rag_test)
echo - Redis: localhost:6381
echo - Qdrant: localhost:6337
echo.
echo External connection examples:
echo psql -h localhost -p 5433 -U postgres -d multi_bot_rag
echo redis-cli -h localhost -p 6380
echo curl http://localhost:6335/
echo.
pause