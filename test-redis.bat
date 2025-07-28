@echo off
echo ================================
echo Redis Containers Test
echo ================================
echo.

echo Testing Main Platform Redis (Port 6380)...
docker-compose exec redis redis-cli ping
if %errorlevel% equ 0 (
    echo ✓ Main Redis is healthy
    echo.
    echo Testing Redis operations...
    echo Setting test key...
    docker-compose exec redis redis-cli set main_test_key "Hello from main Redis!" EX 300
    echo Getting test key...
    docker-compose exec redis redis-cli get main_test_key
    echo.
    echo Testing Redis info...
    docker-compose exec redis redis-cli info server | findstr /C:"redis_version"
    echo.
    echo Cleaning up test key...
    docker-compose exec redis redis-cli del main_test_key
    echo ✓ Main Redis operations successful
) else (
    echo ✗ Main Redis is not healthy
)

echo.
echo Testing Test Redis (Port 6381)...
docker-compose -f docker-compose.test.yml exec redis-test redis-cli ping
if %errorlevel% equ 0 (
    echo ✓ Test Redis is healthy
    echo.
    echo Testing Redis operations...
    echo Setting test key...
    docker-compose -f docker-compose.test.yml exec redis-test redis-cli set test_env_key "Hello from test Redis!" EX 300
    echo Getting test key...
    docker-compose -f docker-compose.test.yml exec redis-test redis-cli get test_env_key
    echo.
    echo Testing Redis info...
    docker-compose -f docker-compose.test.yml exec redis-test redis-cli info server | findstr /C:"redis_version"
    echo.
    echo Cleaning up test key...
    docker-compose -f docker-compose.test.yml exec redis-test redis-cli del test_env_key
    echo ✓ Test Redis operations successful
) else (
    echo ✗ Test Redis is not healthy
)

echo.
echo ================================
echo Redis Summary
echo ================================
echo Main Platform Redis: localhost:6380
echo Test Environment Redis: localhost:6381
echo.
echo External connections:
echo redis-cli -h localhost -p 6380
echo redis-cli -h localhost -p 6381
echo.
pause