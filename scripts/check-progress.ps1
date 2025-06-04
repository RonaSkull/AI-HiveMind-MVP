Write-Host "=== Checking Workflow Progress ==="

# Check workflow files
git status

# Check workflow content
Get-Content .github\workflows\*.yml

# Check git history
git log -n 5

# Check environment variables
$envVars = @('METAMASK_PRIVATE_KEY', 'SEPOLIA_URL', 'CONTRACT_ADDRESS', 'QWEN_API_KEY', 'HYPERSWARM_TOPIC')
foreach ($var in $envVars) {
    Write-Host "Checking $var..."
    if ($env:$var) {
        Write-Host "$var is set"
    } else {
        Write-Host "$var is NOT set"
    }
}

Write-Host "=== Progress Check Complete ==="
