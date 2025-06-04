@echo off
echo === Starting Workflow Fix Script ===

:: Remove all workflow files
del /q /f .github\workflows\*.yml

:: Create new workflow
(echo name: AI Dynamic Pricing
  echo.
  echo on:
  echo   workflow_dispatch:
  echo   schedule:
  echo     - cron: '0 0 * * *'  # Run daily at midnight
  echo.
  echo jobs:
  echo   dynamic-pricing:
  echo     runs-on: ubuntu-latest
  echo     steps:
  echo       - name: Checkout code
  echo         uses: actions/checkout@v4
  echo.
  echo       - name: Set up Node.js
  echo         uses: actions/setup-node@v4
  echo         with:
  echo           node-version: '16'
  echo.
  echo       - name: Install dependencies
  echo         run: npm ci
  echo.
  echo       - name: Run dynamic pricing script
  echo         env:
  echo           METAMASK_PRIVATE_KEY: ${{ secrets.METAMASK_PRIVATE_KEY }}
  echo           SEPOLIA_URL: ${{ secrets.SEPOLIA_URL }}
  echo           CONTRACT_ADDRESS: ${{ secrets.CONTRACT_ADDRESS }}
  echo           QWEN_API_KEY: ${{ secrets.QWEN_API_KEY }}
  echo           HYPERSWARM_TOPIC: ${{ secrets.HYPERSWARM_TOPIC }}
  echo         run: ^
  echo           echo "=== Starting Dynamic Pricing ===" ^
  echo           node backend/dynamic_pricing.js ^
  echo           echo "=== Dynamic Pricing Complete ===") > .github\workflows\ai-dynamic-pricing.yml

:: Add .env to gitignore
if not exist .gitignore (
    echo .env > .gitignore
) else (
    findstr /c:".env" .gitignore > nul
    if errorlevel 1 (
        echo .env >> .gitignore
    )
)

:: Stage and commit changes
git add .
git commit -m "fix: Simplify and fix workflows"
git push origin main --force

echo === Workflow Fix Complete ===
