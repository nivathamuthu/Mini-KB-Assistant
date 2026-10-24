# Run Mini Knowledge Assistant (db + backend + frontend) with Docker Compose
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Checking Docker..." -ForegroundColor Cyan
docker info 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Docker is not running. Start Docker Desktop, wait until it is ready, then run:" -ForegroundColor Yellow
    Write-Host "  .\docker-up.ps1" -ForegroundColor White
    exit 1
}

# Default host ports (8000 is often taken by other dev containers)
if (-not $env:API_HOST_PORT) { $env:API_HOST_PORT = "8001" }
if (-not $env:UI_HOST_PORT) { $env:UI_HOST_PORT = "5173" }

Write-Host "Building and starting services (db, backend, frontend)..." -ForegroundColor Cyan
Write-Host "  API host port: $($env:API_HOST_PORT)  UI host port: $($env:UI_HOST_PORT)"
docker compose up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host "docker compose failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Stack is up:" -ForegroundColor Green
$apiPort = $env:API_HOST_PORT
$uiPort = $env:UI_HOST_PORT
Write-Host "  UI:      http://localhost:$uiPort"
Write-Host "  API:     http://localhost:$apiPort"
Write-Host "  Swagger: http://localhost:$apiPort/docs"
Write-Host "  Health:  http://localhost:$apiPort/health"
Write-Host ""
Write-Host "Logs:  docker compose logs -f"
Write-Host "Stop:  docker compose down"
