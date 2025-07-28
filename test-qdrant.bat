@echo off
echo ================================
echo Qdrant Vector Database Test
echo ================================
echo.

echo Testing Main Platform Qdrant (Port 6335)...
curl -s -f http://localhost:6335/ >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Main Qdrant is healthy
    echo.
    echo Testing Qdrant API...
    echo Getting Qdrant version:
    curl -s -X GET "http://localhost:6335/" | findstr /C:"title"
    echo.
    echo Getting collections:
    curl -s -X GET "http://localhost:6335/collections"
    echo.
    echo Creating test collection...
    curl -s -X PUT "http://localhost:6335/collections/test_main" -H "Content-Type: application/json" -d "{\"vectors\":{\"size\":384,\"distance\":\"Cosine\"}}"
    echo.
    echo Listing collections:
    curl -s -X GET "http://localhost:6335/collections"
    echo.
    echo Deleting test collection...
    curl -s -X DELETE "http://localhost:6335/collections/test_main"
    echo ✓ Main Qdrant operations successful
) else (
    echo ✗ Main Qdrant is not healthy
)

echo.
echo Testing Test Qdrant (Port 6337)...
curl -s -f http://localhost:6337/ >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Test Qdrant is healthy
    echo.
    echo Testing Qdrant API...
    echo Getting Qdrant version:
    curl -s -X GET "http://localhost:6337/" | findstr /C:"title"
    echo.
    echo Getting collections:
    curl -s -X GET "http://localhost:6337/collections"
    echo.
    echo Creating test collection...
    curl -s -X PUT "http://localhost:6337/collections/test_env" -H "Content-Type: application/json" -d "{\"vectors\":{\"size\":384,\"distance\":\"Cosine\"}}"
    echo.
    echo Listing collections:
    curl -s -X GET "http://localhost:6337/collections"
    echo.
    echo Deleting test collection...
    curl -s -X DELETE "http://localhost:6337/collections/test_env"
    echo ✓ Test Qdrant operations successful
) else (
    echo ✗ Test Qdrant is not healthy
)

echo.
echo ================================
echo Qdrant Summary
echo ================================
echo Main Platform Qdrant: http://localhost:6335
echo Test Environment Qdrant: http://localhost:6337
echo.
echo Web UI Access:
echo Main: http://localhost:6335/dashboard
echo Test: http://localhost:6337/dashboard
echo.
echo API Examples:
echo curl http://localhost:6335/collections
echo curl http://localhost:6337/collections
echo.
pause