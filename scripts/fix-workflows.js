const fs = require('fs');
const path = require('path');

console.log('=== Starting Workflow Fix Script ===');

// Remove all existing workflow files
const workflowDir = path.join(__dirname, '..', '.github', 'workflows');
fs.readdirSync(workflowDir).forEach(file => {
    const filePath = path.join(workflowDir, file);
    if (file.endsWith('.yml')) {
        fs.unlinkSync(filePath);
        console.log(`Removed: ${file}`);
    }
});

// Create new, simplified workflow
const newWorkflow = `name: AI Dynamic Pricing

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
          echo "=== Dynamic Pricing Complete ==="`;

// Write new workflow
fs.writeFileSync(path.join(workflowDir, 'ai-dynamic-pricing.yml'), newWorkflow);
console.log('Created new workflow file');

// Create .env file with placeholder values
const envContent = `# Ethereum Network Configuration
SEPOLIA_URL=https://eth-sepolia.public.blastapi.io

# Wallet Configuration
METAMASK_PRIVATE_KEY=your_private_key_here
DEPLOYER_ADDRESS=your_deployer_address_here

# Smart Contract Configuration
CONTRACT_ADDRESS=your_contract_address_here

# AI Configuration
QWEN_API_KEY=your_qwen_api_key_here

# P2P Swarm Configuration
HYPERSWARM_TOPIC=ai-nft-market-v3`;

fs.writeFileSync(path.join(__dirname, '..', '.env'), envContent);
console.log('Created .env file with placeholders');

// Update .gitignore
const gitignorePath = path.join(__dirname, '..', '.gitignore');
const gitignoreContent = fs.readFileSync(gitignorePath, 'utf8');
if (!gitignoreContent.includes('.env')) {
    fs.appendFileSync(gitignorePath, '\n.env');
    console.log('Added .env to .gitignore');
}

// Update package.json scripts
const packageJsonPath = path.join(__dirname, '..', 'package.json');
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
packageJson.scripts = {
    ...packageJson.scripts,
    'test:workflow': 'node scripts/test-workflow.js',
    'test:secrets': 'node scripts/test-secrets.js',
    'test:pricing': 'node scripts/test-dynamic-pricing.js'
};
fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
console.log('Updated package.json scripts');

console.log('=== Workflow Fix Complete ===');
