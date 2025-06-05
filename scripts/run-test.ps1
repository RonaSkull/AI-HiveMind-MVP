# This script runs the dynamic_pricing.js script.
# It relies on the .env.development file in the project root (d:\AI-HiveMind-MVP\.env.development)
# for all necessary environment variables.

# Ensure your .env.development file is correctly configured with:
# SEPOLIA_URL, METAMASK_PRIVATE_KEY, CONTRACT_ADDRESS, QWEN_API_KEY, HYPERSWARM_TOPIC, MINIMUM_PRICE, PRICE_INCREMENT

Write-Host "Navigating to backend directory..."
Set-Location -Path "$PSScriptRoot\..\backend"

Write-Host "Attempting to run dynamic_pricing.js..."
Write-Host "Please ensure d:\AI-HiveMind-MVP\.env.development is correctly populated with all required variables."

# Run the dynamic pricing script. It will load environment variables from ../.env.development
node dynamic_pricing.js
