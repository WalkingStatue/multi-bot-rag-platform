@echo off
echo ================================
echo PostgreSQL Containers Test
echo ================================
echo.

echo Testing Main Platform PostgreSQL (Port 5433)...
docker-compose exec postgres pg_isready -U postgres
if %errorlevel% equ 0 (
    echo ✓ Main PostgreSQL is healthy
    docker-compose exec postgres psql -U postgres -d multi_bot_rag -c "SELECT 'Main DB Connected' as status, current_database(), version();"
) else (
    echo ✗ Main PostgreSQL is not healthy
)

echo.
echo Testing Test PostgreSQL (Port 5434)...
docker-compose -f docker-compose.test.yml exec postgres-test pg_isready -U postgres
if %errorlevel% equ 0 (
    echo ✓ Test PostgreSQL is healthy
    docker-compose -f docker-compose.test.yml exec postgres-test psql -U postgres -d multi_bot_rag_test -c "SELECT 'Test DB Connected' as status, current_database(), version();"
) else (
    echo ✗ Test PostgreSQL is not healthy
)

echo.
echo ================================
echo Summary
echo ================================
echo Main Platform: localhost:5433 (multi_bot_rag)
echo Test Environment: localhost:5434 (multi_bot_rag_test)
echo.
echo External connections:
echo psql -h localhost -p 5433 -U postgres -d multi_bot_rag
echo psql -h localhost -p 5434 -U postgres -d multi_bot_rag_test
echo.
pause