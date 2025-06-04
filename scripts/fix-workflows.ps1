# Remove all workflow files
Remove-Item -Path .github\workflows\*.yml -Force -ErrorAction SilentlyContinue

# Create new workflow
$workflowContent = @"
name: AI Dynamic Pricing

on:
  workflow_dispatch:
  schedule:
    - cron: '0 0 * * *'  # Run daily at midnight

jobs:
  dynamic-pricing:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '16'

      - name: Install dependencies
        run: npm ci

      - name: Run dynamic pricing script
        env:
          METAMASK_PRIVATE_KEY: ${{ secrets.METAMASK_PRIVATE_KEY }}
          SEPOLIA_URL: ${{ secrets.SEPOLIA_URL }}
          CONTRACT_ADDRESS: ${{ secrets.CONTRACT_ADDRESS }}
          QWEN_API_KEY: ${{ secrets.QWEN_API_KEY }}
          HYPERSWARM_TOPIC: ${{ secrets.HYPERSWARM_TOPIC }}
        run: |
          echo "=== Starting Dynamic Pricing ==="
          node backend/dynamic_pricing.js
          echo "=== Dynamic Pricing Complete ==="
"@

# Write new workflow
New-Item -Path .github\workflows\ai-dynamic-pricing.yml -Value $workflowContent -Force

# Update .gitignore
$gitignorePath = ".gitignore"
$gitignoreContent = Get-Content $gitignorePath
if (-not ($gitignoreContent -contains ".env")) {
    Add-Content -Path $gitignorePath -Value ".env"
}

# Update package.json
$packageJsonPath = "package.json"
$packageJson = Get-Content $packageJsonPath | ConvertFrom-Json
$packageJson.PSObject.Properties.Add([psnoteproperty]"scripts", @{
    "test:workflow" = "node scripts/test-workflow.js";
    "test:secrets" = "node scripts/test-secrets.js";
    "test:pricing" = "node scripts/test-dynamic-pricing.js"
})
$packageJson | ConvertTo-Json -Depth 10 | Set-Content $packageJsonPath

# Stage and commit changes
git add .
git commit -m "fix: Simplify and fix workflows"
git push origin main --force
