# Set up environment variables
$env:METAMASK_PRIVATE_KEY = "0x05a4743525020c3a85057939ebfb283b5a1d08f26854265e0e849a98725d69b3"
$env:SEPOLIA_URL = "https://eth-sepolia.public.blastapi.io"
$env:CONTRACT_ADDRESS = "0xa0f536d1d1a8Bf63e200344Bda8a34b6d012745b"
$env:QWEN_API_KEY = "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"
$env:HYPERSWARM_TOPIC = "ai-nft-market-v3"

# Install dependencies if needed
Write-Host "Installing dependencies..."
npm install ethers dotenv

# Run the script with detailed output
Write-Host "Running dynamic pricing script..."
node backend/dynamic_pricing.js

# Capture and display any errors
if ($LASTEXITCODE -ne 0) {
    Write-Host "Script failed with exit code $LASTEXITCODE" -ForegroundColor Red
} else {
    Write-Host "Script completed successfully" -ForegroundColor Green
}
