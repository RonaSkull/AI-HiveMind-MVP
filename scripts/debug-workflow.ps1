# Set environment variables
$env:METAMASK_PRIVATE_KEY = "0x05a4743525020c3a85057939ebfb283b5a1d08f26854265e0e849a98725d69b3"
$env:SEPOLIA_URL = "https://eth-sepolia.public.blastapi.io"
$env:CONTRACT_ADDRESS = "0xa0f536d1d1a8Bf63e200344Bda8a34b6d012745b"
$env:QWEN_API_KEY = "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"
$env:HYPERSWARM_TOPIC = "ai-nft-market-v3"

# Install act globally
npm install -g @github/act

# Run the workflow with detailed logging
act -j dynamic-pricing -s METAMASK_PRIVATE_KEY=${env:METAMASK_PRIVATE_KEY} -s SEPOLIA_URL=${env:SEPOLIA_URL} -s CONTRACT_ADDRESS=${env:CONTRACT_ADDRESS} -s QWEN_API_KEY=${env:QWEN_API_KEY} -s HYPERSWARM_TOPIC=${env:HYPERSWARM_TOPIC} -P ubuntu-latest=catthehacker/ubuntu-base:latest --verbose
