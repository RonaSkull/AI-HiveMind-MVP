# Verify environment variables
Write-Host "`nVerifying environment variables..."

# List all environment variables
$envVars = Get-ChildItem Env:
foreach ($var in $envVars) {
    Write-Host "$($var.Name) = $($var.Value)"
}

# Test specific variables
Write-Host "`nTesting specific variables..."
$requiredVars = @(
    "METAMASK_PRIVATE_KEY",
    "SEPOLIA_URL",
    "CONTRACT_ADDRESS",
    "QWEN_API_KEY",
    "HYPERSWARM_TOPIC"
)

foreach ($var in $requiredVars) {
    if ($env:$var) {
        Write-Host "✅ $var is set"
    } else {
        Write-Host "❌ $var is not set"
    }
}
