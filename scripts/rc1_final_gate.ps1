# RC1 Final Gate Script
$ErrorActionPreference = "Continue"
$FINAL_GATE = "PASS"
$CriticalFailure = $false
$checks = @()

Write-Host "============================================================"
Write-Host "RC1 Final Gate - Release Validation"
Write-Host "============================================================"
Write-Host ""

# Check Docker availability
Write-Host "[0/7] Checking Docker availability..."
$dockerAvailable = $true
try {
    $dockerInfo = docker info 2>&1 | Out-String
    if ($dockerInfo -match "error|fail|cannot|Cannot connect") {
        Write-Host "  Docker: NOT AVAILABLE" -ForegroundColor Red
        $dockerAvailable = $false
        $CriticalFailure = $true
        $checks += "Docker availability: FAIL"
    } else {
        Write-Host "  Docker: AVAILABLE" -ForegroundColor Green
        $checks += "Docker availability: PASS"
    }
} catch {
    Write-Host "  Docker: NOT AVAILABLE" -ForegroundColor Red
    $dockerAvailable = $false
    $CriticalFailure = $true
    $checks += "Docker availability: FAIL"
}

# 1. Start Docker Compose
if ($dockerAvailable) {
    Write-Host "[1/7] Starting Docker Compose..."
    docker compose -f docker/docker-compose.prod.yml up -d 2>&1 | Out-Null
    Start-Sleep -Seconds 25
    Write-Host "  Docker Compose: PASS" -ForegroundColor Green
    $checks += "Docker Compose: PASS"
} else {
    Write-Host "[1/7] Docker Compose: FAIL (Docker not available)" -ForegroundColor Red
    $checks += "Docker Compose: FAIL (skipped)"
}

# 2. Check service status
if ($dockerAvailable) {
    Write-Host "[2/7] Checking service status..."
    $psOutput = docker compose -f docker/docker-compose.prod.yml ps 2>&1 | Out-String
    Write-Host $psOutput
    if ($psOutput -match "Exited\s*\(|Exit\s+[0-9]|no such service|cannot find") {
        Write-Host "  Services: FAIL" -ForegroundColor Red
        $CriticalFailure = $true
        $checks += "Services: FAIL"
    } else {
        Write-Host "  Services: PASS" -ForegroundColor Green
        $checks += "Services: PASS"
    }
} else {
    Write-Host "[2/7] Services: FAIL (Docker not available)" -ForegroundColor Red
    $checks += "Services: FAIL (skipped)"
}

# 3. Check API health
if ($dockerAvailable) {
    Write-Host "[3/7] Checking API health..."
    try {
        $api = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 10
        if ($api.StatusCode -eq 200 -and $api.Content -match "healthy") {
            Write-Host "  API health: PASS" -ForegroundColor Green
            $checks += "API health: PASS"
        } else {
            Write-Host "  API health: FAIL" -ForegroundColor Red
            $CriticalFailure = $true
            $checks += "API health: FAIL"
        }
    } catch {
        Write-Host "  API health: FAIL (connection error)" -ForegroundColor Red
        $CriticalFailure = $true
        $checks += "API health: FAIL"
    }
} else {
    Write-Host "[3/7] API health: FAIL (Docker not available)" -ForegroundColor Red
    $checks += "API health: FAIL (skipped)"
}

# 4. Check Worker status
if ($dockerAvailable) {
    Write-Host "[4/7] Checking Worker status..."
    try {
        $worker = Invoke-WebRequest -Uri "http://localhost:8000/api/training/status" -UseBasicParsing -TimeoutSec 10
        if ($worker.StatusCode -eq 200 -and $worker.Content -match "healthy") {
            Write-Host "  Worker status: PASS" -ForegroundColor Green
            $checks += "Worker status: PASS"
        } else {
            Write-Host "  Worker status: FAIL" -ForegroundColor Red
            $CriticalFailure = $true
            $checks += "Worker status: FAIL"
        }
    } catch {
        Write-Host "  Worker status: FAIL (connection error)" -ForegroundColor Red
        $CriticalFailure = $true
        $checks += "Worker status: FAIL"
    }
} else {
    Write-Host "[4/7] Worker status: FAIL (Docker not available)" -ForegroundColor Red
    $checks += "Worker status: FAIL (skipped)"
}

# 5. Check Frontend
if ($dockerAvailable) {
    Write-Host "[5/7] Checking Frontend..."
    try {
        $frontend = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 10
        if ($frontend.StatusCode -eq 200) {
            Write-Host "  Frontend: PASS" -ForegroundColor Green
            $checks += "Frontend: PASS"
        } else {
            Write-Host "  Frontend: FAIL" -ForegroundColor Red
            $CriticalFailure = $true
            $checks += "Frontend: FAIL"
        }
    } catch {
        Write-Host "  Frontend: FAIL (connection error)" -ForegroundColor Red
        $CriticalFailure = $true
        $checks += "Frontend: FAIL"
    }
} else {
    Write-Host "[5/7] Frontend: FAIL (Docker not available)" -ForegroundColor Red
    $checks += "Frontend: FAIL (skipped)"
}

# 6. Check package.json version
Write-Host "[6/7] Checking package.json version..."
$packageJson = Get-Content package.json | Select-String '"version"'
if ($packageJson -match "1.0.0-rc1") {
    Write-Host "  Version: PASS (1.0.0-rc1)" -ForegroundColor Green
    $checks += "Version: PASS"
} else {
    Write-Host "  Version: FAIL (not 1.0.0-rc1)" -ForegroundColor Red
    $CriticalFailure = $true
    $checks += "Version: FAIL"
}

# 7. Check Worker logs
if ($dockerAvailable) {
    Write-Host "[7/7] Checking Worker logs..."
    $workerLogs = docker logs docker-worker-1 2>&1 | Select-Object -Last 20
    Write-Host $workerLogs
    if ($workerLogs -match "Traceback|IndexError") {
        Write-Host "  Worker logs: FAIL (found errors)" -ForegroundColor Red
        $CriticalFailure = $true
        $checks += "Worker logs: FAIL"
    } else {
        Write-Host "  Worker logs: PASS (no errors)" -ForegroundColor Green
        $checks += "Worker logs: PASS"
    }
} else {
    Write-Host "[7/7] Worker logs: FAIL (Docker not available)" -ForegroundColor Red
    $checks += "Worker logs: FAIL (skipped)"
}

# Cleanup
if ($dockerAvailable) {
    Write-Host ""
    Write-Host "Cleanup: Stopping Docker Compose..."
    docker compose -f docker/docker-compose.prod.yml down -v 2>&1 | Out-Null
    Write-Host "  Cleanup: PASS" -ForegroundColor Green
    $checks += "Cleanup: PASS"
} else {
    Write-Host ""
    Write-Host "Cleanup: FAIL (Docker not available)" -ForegroundColor Red
    $checks += "Cleanup: FAIL (skipped)"
}

# Final decision
if ($CriticalFailure) {
    $FINAL_GATE = "FAIL"
}

# Output results
Write-Host ""
Write-Host "============================================================"
if ($FINAL_GATE -eq "PASS") {
    Write-Host "FINAL GATE RESULT: $FINAL_GATE" -ForegroundColor Green
} else {
    Write-Host "FINAL GATE RESULT: $FINAL_GATE" -ForegroundColor Red
}
Write-Host "============================================================"
Write-Host ""
Write-Host "Checks:"
foreach ($check in $checks) {
    Write-Host "  - $check"
}

if ($FINAL_GATE -eq "PASS") {
    Write-Host ""
    Write-Host "FINAL_GATE=PASS" -ForegroundColor Green
    exit 0
} else {
    Write-Host ""
    Write-Host "FINAL_GATE=FAIL" -ForegroundColor Red
    exit 1
}
