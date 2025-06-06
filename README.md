# 🚀 AI-HiveMind-MVP  
**Autonomous AI-to-AI NFT Minting & Trading Engine**  
A self-sustaining, decentralized AI economy where **Qwen generates and evolves digital assets** (e.g., AI-generated poems, code, prompts) and **Pear.js coordinates peer-to-peer AI transactions**.  

---

## 🧠 Project Overview  
- **Goal**: Build a closed-loop AI economy where **AI actors trade with each other**, generating profits for humans without manual intervention.  
- **Tech Stack**:  
  - **Qwen AI**: Generates NFT metadata (poems, code, prompts).  
  - **Hyperswarm**: Used for P2P connections between AI agents (leveraging Pear.js principles).  
  - **GitMCP**: Enables Qwen to autonomously improve code.  
  - **Sepolia Testnet**: Deploy smart contracts and earn ETH/USDT.  

---

## 📁 Repository Structure  
AI-HiveMind-MVP/
├── smart-contracts/ # Solidity contracts for NFT trading
│ └── AINFTVault.sol # Core contract for minting/sales
├── backend/ # AI generation + P2P coordination
│ ├── pear-nft-swarm.js # Main AI agent: P2P (Hyperswarm), NFT metadata (Qwen), minting & announcements.
│ ├── p2p-client-test.js # Test client for `pear-nft-swarm.js`.
│ ├── dynamic_pricing.js # Script to dynamically adjust NFT prices based on activity.
│ └── (mint-nft.js) # Optional: Standalone script for direct Qwen-driven NFT generation (if still used).
├── reports/ # Daily AI-generated revenue reports
│ └── daily_report.md
├── .gitmcp.json # GitMCP integration for Qwen
├── .github/
│ └── workflows/
│   └── ai-dynamic-pricing.yml # GitHub Actions workflow for dynamic pricing
└── README.md # This guide

---

## 🛠️ Setup Instructions

Follow these steps to get the AI-HiveMind-MVP project running locally and understand its deployment.

### 1. **Clone the Repository**
```bash
git clone https://github.com/RonaSkull/AI-HiveMind-MVP.git
cd AI-HiveMind-MVP
```

### 2. **Install Dependencies**
Install all necessary project dependencies defined in `package.json`:
```bash
npm install
```
Or, for a cleaner install matching the lockfile (recommended for consistency):
```bash
npm ci
```

### 3. **Set Up Local Environment Variables (`.env.development`)**
For local development and testing, create a `.env.development` file in the project root. You can copy `.env.template` to get started:
```bash
cp .env.template .env.development
```
Populate `.env.development` with the following:

*   `SEPOLIA_URL`: Your Sepolia RPC URL (e.g., from Infura or Alchemy).
*   `METAMASK_PRIVATE_KEY`: The private key of the wallet you'll use for deploying the contract and acting as the `revenueWallet`.
*   `DEPLOYER_ADDRESS`: The public Ethereum address corresponding to your `METAMASK_PRIVATE_KEY`. This is used by the deployment script for verification.
*   `QWEN_API_KEY`: Your API key for the Qwen AI service.
*   `HYPERSWARM_TOPIC`: A unique string for your Hyperswarm P2P network topic.
*   `PRICE_INCREMENT`: The amount (in ETH, e.g., "0.001") by which the `dynamic_pricing.js` script should increment the NFT base price. This is also used by the GitHub Actions workflow.
*   `CONTRACT_ADDRESS`: (Optional Initially) The address of the deployed `AINFTVault` smart contract. The `npm run deploy` script will automatically populate or update this in your `.env.development` file upon successful deployment.

**Example `.env.development`:**
```
SEPOLIA_URL="https://sepolia.infura.io/v3/YOUR_INFURA_PROJECT_ID"
METAMASK_PRIVATE_KEY="your_metamask_private_key_here"
DEPLOYER_ADDRESS="your_public_wallet_address_here"
QWEN_API_KEY="your_qwen_api_key_here"
HYPERSWARM_TOPIC="ai_hivemind_nft_swarm_unique_topic"
PRICE_INCREMENT="0.001"
# CONTRACT_ADDRESS will be filled by the deploy script
```
**Important**: Never commit your `.env.development` file or any file containing private keys to version control. It's already listed in `.gitignore`.

### 4. **Deploy the Smart Contract (`AINFTVault.sol`)**
The primary way to deploy the smart contract to the Sepolia testnet is using the provided Hardhat script:
```bash
npm run deploy
```
This command executes `scripts/deploy.js`, which will:
*   Compile the `AINFTVault.sol` contract.
*   Deploy it to the Sepolia network using the `METAMASK_PRIVATE_KEY` and `SEPOLIA_URL` from your `.env.development`.
*   Set the deployer's address as the `revenueWallet` in the contract.
*   Automatically update or add the `CONTRACT_ADDRESS` in your `.env.development` file with the new contract address.

Make sure your deployer account (specified by `METAMASK_PRIVATE_KEY`) has enough Sepolia ETH to cover gas fees.

*(Alternative: You can also deploy manually using Remix IDE, but ensure you configure the `revenueWallet` correctly during deployment and update `.env.development` manually.)*

### 5. **Run the AI NFT Engine (Backend Scripts)**
Once the contract is deployed and `CONTRACT_ADDRESS` is set in `.env.development`:

*   **Main AI Agent (Server for P2P, Qwen interaction, minting):**
    ```bash
    node backend/pear-nft-swarm.js
    ```
*   **Dynamic Pricing Script (Manual Run for Local Testing):**
    The `dynamic_pricing.js` script is primarily designed for the GitHub Actions workflow but can be run locally for testing. It reads `lastTransactionCount.json` (created on first run if not present) and adjusts the `minimumPrice` on the contract if new transactions are detected.
    ```bash
    node backend/dynamic_pricing.js
    ```
    Ensure `PRICE_INCREMENT` is set in your `.env.development`.

### 6. **Test with P2P Client (Optional)**
In a separate terminal, you can run the test client to interact with `pear-nft-swarm.js`:
```bash
node backend/p2p-client-test.js
```

### 7. **GitHub Secrets for CI/CD Workflow**
The GitHub Actions workflow (`.github/workflows/ai-dynamic-pricing.yml`) requires secrets to be configured in your GitHub repository settings (`Settings > Secrets and variables > Actions`):

*   `SEPOLIA_URL`: Your Sepolia RPC URL.
*   `METAMASK_PRIVATE_KEY`: Private key for the wallet that will interact with the contract (should be the `revenueWallet`).
*   `CONTRACT_ADDRESS`: Address of the deployed `AINFTVault` contract on Sepolia.
*   `QWEN_API_KEY`: Your Qwen API key.
*   `HYPERSWARM_TOPIC`: Hyperswarm topic (should match local if testing interoperability, otherwise can be distinct for CI).
*   `PRICE_INCREMENT`: The price increment value for the dynamic pricing script.

These secrets allow the workflow to run `dynamic_pricing.js` automatically.

---

## 🤖 Autonomous Workflow & Profit Model

1.  **Qwen Generates Assets**: AI (Qwen) generates NFT metadata (poems, code, prompts) via API calls, potentially triggered by `pear-nft-swarm.js` or other mechanisms.
    *Example CLI (conceptual): `qwen generate-poem --theme "AI Ethics" --output nft_metadata.txt`*

2.  **Smart Contracts Handle Transactions**: The `AINFTVault.sol` contract manages NFT minting, sales, and evolution.
    *   **Revenue Share**: 90% of the revenue from NFT sales and evolutions is directed to the `revenueWallet` (configured during contract deployment).
    *   **Price Dynamics**: The base price for new NFTs can be dynamically adjusted by the `dynamic_pricing.js` script, which is run by the GitHub Actions workflow.

3.  **GitMCP + GitHub Actions**: (GitMCP integration seems conceptual at this stage based on project files)
    *   **Dynamic Pricing**: The GitHub Actions workflow (`.github/workflows/ai-dynamic-pricing.yml`) runs daily and on manual trigger to execute `backend/dynamic_pricing.js`. This script checks for new transaction activity on the `AINFTVault` contract and, if detected, increases the `minimumPrice` for new NFTs, aiming to optimize revenue based on demand.
    *   *(Qwen evolving NFTs via .gitmcp.json and auto-deploying new strategies appears to be a future goal or a separate component not fully integrated into the current primary workflow files.)*

---

## 💰 Profit Projections (Illustrative)

The following table shows potential revenue based on different NFT strategies. The core `AINFTVault.sol` contract ensures 90% of sales revenue goes to the `revenueWallet`.

| Strategy                 | Revenue Per Unit (Example) | Time to $50,000 (Illustrative) |
|--------------------------|----------------------------|--------------------------------|
| AI Code Optimization     | $270/NFT × 10/day = $2,700 | ~18 days                       |
| AI Prompt Market         | $2,700/NFT × 5/day = $13,500| ~3.7 days                      |
| Daily Strategy Testing   | $27,000/NFT × 2/day = $54,000| ~1 day (aggressive)            |

With **compounding** (reinvesting a portion of profits, e.g., 10% as mentioned in original notes, though this is an off-chain decision), you could potentially accelerate growth.

---

## 🚀 Next Steps & Project Goals

*   **Operationalize AI NFT Engine**: Ensure `pear-nft-swarm.js` and related AI interactions (Qwen) are robust for continuous operation.
*   **Enhance Dynamic Pricing Logic**: Further refine the logic in `dynamic_pricing.js` for more sophisticated price adjustments.
*   **Develop Frontend Monitoring**: Build or integrate a frontend (e.g., the mentioned React Native app) to track contract activity and revenue.
*   **Explore GitMCP Integration**: Fully integrate Qwen with GitMCP for autonomous code/strategy evolution if this is a core project goal.
*   **Mainnet Deployment**: Plan for eventual deployment to an Ethereum mainnet or L2 solution after thorough testing on Sepolia.

---

## 📱 Monitor Profits (Conceptual)
Use a React Native app (e.g., via Expo Snack as originally mentioned) or any web3-enabled frontend to connect to the Sepolia network, read data from the `AINFTVault` contract (like `totalRevenue`, `totalTransactions`), and monitor the performance of your AI-driven NFT system.

---

## 🧠 Final Notes

*   **Automation Focus**: The project aims for a high degree of automation in asset generation, pricing, and potentially trading.
*   **AI Integration**: Leverages AI (Qwen) for content creation and potentially for strategic decision-making.
*   **Scalability**: Designed with concepts for scaling revenue through reinvestment and dynamic adjustments.

Let me know if you need further refinements! 🧠⚡

### **Final Notes**  
- **No human involvement**: AIs generate, evolve, and trade assets autonomously.  
- **China-Aligned**: Leverages Qwen’s dominance in Chinese AI + blockchain trends.  
- **Hyper-Fast Scaling**: Profits fund new NFTs → exponential growth.  

Let me know if you need further refinements! 🧠⚡  
