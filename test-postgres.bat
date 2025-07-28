@echo off
echo Testing PostgreSQL Containers...
echo.

echo ================================
echo Testing Main Platform PostgreSQL (Port 5433)
echo ================================
docker-compose ps postgres
echo.

echo Checking if main postgres is running...
docker-compose exec postgres pg_isready -U postgres
if %errorlevel% equ 0 (
    echo ✓ Main PostgreSQL is healthy
    echo.
    echo Testing database connection...
    docker-compose exec postgres psql -U postgres -d multi_bot_rag -c "SELECT version();"
    echo.
    echo Testing table creation...
    docker-compose exec postgres psql -U postgres -d multi_bot_rag -c "CREATE TABLE IF NOT EXISTS test_main (id SERIAL PRIMARY KEY, name VARCHAR(50));"
    docker-compose exec postgres psql -U postgres -d multi_bot_rag -c "INSERT INTO test_main (name) VALUES ('main_test');"
    docker-compose exec postgres psql -U postgres -d multi_bot_rag -c "SELECT * FROM test_main;"
    docker-compose exec postgres psql -U postgres -d multi_bot_rag -c "DROP TABLE test_main;"
    echo ✓ Main PostgreSQL operations successful
) else (
    echo ✗ Main PostgreSQL is not healthy
)

echo.
echo ================================
echo Testing Test PostgreSQL (Port 5434)
echo ================================
docker-compose -f docker-compose.test.yml ps postgres-test
echo.

echo Checking if test postgres is running...
docker-compose -f docker-compose.test.yml exec postgres-test pg_isready -U postgres
if %errorlevel% equ 0 (
    echo ✓ Test PostgreSQL is healthy
    echo.
    echo Testing database connection...
    docker-compose -f docker-compose.test.yml exec postgres-test psql -U postgres -d multi_bot_rag_test -c "SELECT version();"
    echo.
    echo Testing table creation...
    docker-compose -f docker-compose.test.yml exec postgres-test psql -U postgres -d multi_bot_rag_test -c "CREATE TABLE IF NOT EXISTS test_db (id SERIAL PRIMARY KEY, name VARCHAR(50));"
    docker-compose -f docker-compose.test.yml exec postgres-test psql -U postgres -d multi_bot_rag_test -c "INSERT INTO test_db (name) VALUES ('test_env');"
    docker-compose -f docker-compose.test.yml exec postgres-test psql -U postgres -d multi_bot_rag_test -c "SELECT * FROM test_db;"
    docker-compose -f docker-compose.test.yml exec postgres-test psql -U postgres -d multi_bot_rag_test -c "DROP TABLE test_db;"
    echo ✓ Test PostgreSQL operations successful
) else (
    echo ✗ Test PostgreSQL is not healthy
)

echo.
echo ================================
echo Connection Summary
echo ================================
echo Main Platform DB: localhost:5433 (multi_bot_rag)
echo Test DB: localhost:5434 (multi_bot_rag_test)
echo.
echo Both databases should be accessible from host machine:
echo psql -h localhost -p 5433 -U postgres -d multi_bot_rag
echo psql -h localhost -p 5434 -U postgres -d multi_bot_rag_test
echo.
pause