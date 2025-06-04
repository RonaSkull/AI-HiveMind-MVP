# Set up environment variables
$env:METAMASK_PRIVATE_KEY = "0x05a4743525020c3a85057939ebfb283b5a1d08f26854265e0e849a98725d69b3"
$env:SEPOLIA_URL = "https://eth-sepolia.public.blastapi.io"
$env:CONTRACT_ADDRESS = "0xa0f536d1d1a8Bf63e200344Bda8a34b6d012745b"
$env:QWEN_API_KEY = "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"
$env:HYPERSWARM_TOPIC = "ai-nft-market-v3"

# Test environment variables
Write-Host "`nTesting environment variables..."
$envVars = @("METAMASK_PRIVATE_KEY", "SEPOLIA_URL", "CONTRACT_ADDRESS", "QWEN_API_KEY", "HYPERSWARM_TOPIC")

foreach ($var in $envVars) {
    if ($env.$var) {
        Write-Host "✅ $var is set"
    } else {
        Write-Host "❌ $var is not set"
    }
}

# Test contract address format
Write-Host "`nTesting contract address format..."
if ($env.CONTRACT_ADDRESS -match '^0x[a-fA-F0-9]{40}$') {
    Write-Host "✅ Contract address format is valid"
} else {
    Write-Host "❌ Contract address format is invalid"
}

# Test Qwen API key format
Write-Host "`nTesting Qwen API key format..."
if ($env.QWEN_API_KEY -match '^sk-or-v1-[a-f0-9]+$') {
    Write-Host "✅ Qwen API key format is valid"
} else {
    Write-Host "❌ Qwen API key format is invalid"
}
