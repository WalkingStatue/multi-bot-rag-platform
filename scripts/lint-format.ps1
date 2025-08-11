Param(
  [switch]$Fix
)

Write-Host "Running frontend lint/format in Docker..." -ForegroundColor Cyan
if ($Fix) {
  docker compose exec frontend npm run format
  docker compose exec frontend npm run lint:fix
} else {
  docker compose exec frontend npm run format:check
  docker compose exec frontend npm run lint
}

Write-Host "Running backend lint/format in Docker..." -ForegroundColor Cyan
if ($Fix) {
  docker compose exec backend ruff check . --fix
  docker compose exec backend isort .
  docker compose exec backend black .
} else {
  docker compose exec backend ruff check .
  docker compose exec backend isort . --check-only
  docker compose exec backend black . --check
}
