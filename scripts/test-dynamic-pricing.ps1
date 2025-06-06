# This script tests the backend/dynamic_pricing.js script.
#
# IMPORTANT:
# Ensure your .env.development file in the project root is correctly configured with:
# - METAMASK_PRIVATE_KEY (this is the revenue wallet/admin key for setMinimumPrice)
# - SEPOLIA_URL
# - CONTRACT_ADDRESS
# - PRICE_INCREMENT

Write-Host "Ensuring Node.js dependencies are up to date..."
npm install

Write-Host "Running the dynamic pricing script (backend/dynamic_pricing.js)..."
# The dynamic_pricing.js script will load necessary environment variables 
# from the .env.development file using dotenv.
node backend/dynamic_pricing.js

Write-Host "Dynamic pricing script execution finished."
