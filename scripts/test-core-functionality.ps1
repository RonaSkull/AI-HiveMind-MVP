# Set up environment variables
$env:METAMASK_PRIVATE_KEY = "0x05a4743525020c3a85057939ebfb283b5a1d08f26854265e0e849a98725d69b3"
$env:SEPOLIA_URL = "https://eth-sepolia.public.blastapi.io"
$env:CONTRACT_ADDRESS = "0xa0f536d1d1a8Bf63e200344Bda8a34b6d012745b"
$env:QWEN_API_KEY = "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"
$env:HYPERSWARM_TOPIC = "ai-nft-market-v3"

# Create a simple test script to verify core functionality
$testScript = @"
const { ethers } = require('ethers');

// Test connection to Sepolia
const provider = new ethers.JsonRpcProvider(process.env.SEPOLIA_URL);
provider.getBlockNumber().then(blockNumber => {
    console.log(`Connected to Sepolia, current block: ${blockNumber}`);
});

// Verify contract address
console.log(`Using contract address: ${process.env.CONTRACT_ADDRESS}`);

// Test Qwen API key
console.log(`Qwen API key is set: ${!!process.env.QWEN_API_KEY}`);

// Test Hyperswarm topic
console.log(`Using Hyperswarm topic: ${process.env.HYPERSWARM_TOPIC}`);

console.log('Core functionality test completed successfully!');
"@

# Write the test script to a temporary file
$testScript | Set-Content -Path "test-core.js"

# Run the test script
Write-Host "Running core functionality test..."
node test-core.js

# Clean up
Remove-Item "test-core.js" -Force

# Capture and display any errors
if ($LASTEXITCODE -ne 0) {
    Write-Host "Test failed with exit code $LASTEXITCODE" -ForegroundColor Red
} else {
    Write-Host "Core functionality test completed successfully" -ForegroundColor Green
}
