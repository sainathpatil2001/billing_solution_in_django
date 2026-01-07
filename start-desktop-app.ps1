Write-Host "Starting Billing System Desktop Application..." -ForegroundColor Green
Write-Host ""

Write-Host "Step 1: Starting Django Server..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "manage.py", "runserver", "8000" -WindowStyle Normal

Write-Host "Step 2: Waiting for Django to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "Step 3: Starting Electron Desktop App..." -ForegroundColor Yellow
npm start

Write-Host ""
Write-Host "Desktop application started!" -ForegroundColor Green
Write-Host "Close this window to stop the application." -ForegroundColor Cyan
Read-Host "Press Enter to exit"
