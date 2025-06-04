# Environment Setup Instructions

This project uses several environment variables for configuration. These should be set up as GitHub Secrets rather than in a `.env` file:

1. Go to your repository settings -> Secrets and variables -> Actions
2. Add these secrets:
   - `SEPOLIA_URL`: Sepolia RPC URL (e.g., https://eth-sepolia.public.blastapi.io)
   - `METAMASK_PRIVATE_KEY`: Private key for the revenue wallet
   - `CONTRACT_ADDRESS`: Deployed AINFTVault contract address
   - `QWEN_API_KEY`: Qwen API key for AI integration
   - `HYPERSWARM_TOPIC`: Hyperswarm topic for P2P communication (e.g., ai-nft-market-v3)

**Important**: Never commit sensitive values to version control. All sensitive configuration should be handled through GitHub Secrets.

## Local Development

For local development, create a `.env.development` file in the root directory with placeholder values:

```bash
cp .env.example .env.development
```

Then edit `.env.development` with your local development values.
