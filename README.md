# 🚀 AI-HiveMind-MVP  
**Autonomous AI-to-AI NFT Minting & Trading Engine**  

A self-sustaining, decentralized AI economy where **AI agents collaborate** to manage, price, and trade digital assets autonomously, using the **Model Context Protocol (MCP)** for seamless communication and shared context.

## 🌟 Key Features

- **Multi-Agent System (MAS)** with specialized agents for different tasks
- **Model Context Protocol (MCP)** for shared context and agent communication
- **Decentralized Architecture** with Redis for state management
- **Autonomous NFT Management** with dynamic pricing and execution
- **Extensible Design** for adding new agents and capabilities

---

## 🧠 Project Overview  

### Core Components

#### 1. Model Context Protocol (MCP)
- **Context Manager**: Centralized context storage with Redis backend
- **Agent State Management**: Track and manage agent states consistently
- **Search & Retrieval**: Efficient context search by agent ID and metadata

#### 2. Agent Architecture
- **Base Agent**: Abstract class with lifecycle management and MCP integration
- **Specialized Agents**:
  - `VaultReaderAgent`: Monitors and reports on NFT vault state
  - `PricingDecisionAgent`: Implements dynamic pricing strategies
  - `PriceExecutionAgent`: Handles on-chain transactions

#### 3. Tech Stack  
- **Backend**: Python 3.11+
- **Blockchain**: Web3.py, Sepolia Testnet
- **Data**: Redis for context management
- **AI**: CrewAI for agent orchestration
- **Monitoring**: Structured logging and metrics

#### 4. Key Features
- **Autonomous Operation**: Agents work independently and collaboratively
- **Fault Tolerance**: Graceful error handling and recovery
- **Extensible**: Easy to add new agents and capabilities
- **Observable**: Built-in monitoring and logging

---

## 📁 Repository Structure  
```
AI-HiveMind-MVP/
├── agents/                   # Agent implementations
│   ├── __init__.py          # Package initialization
│   ├── base_agent.py        # Base agent class with common functionality
│   ├── vault_reader_agent.py # Vault monitoring agent
│   ├── pricing_decision_agent.py # Pricing strategy agent
│   └── price_execution_agent.py # Transaction execution agent
│
├── mcp/                     # Model Context Protocol
│   ├── __init__.py
│   └── context_manager.py   # Redis-based context management
│
├── smart-contracts/         # Solidity contracts
│   └── AINFTVault.sol       # Core contract for NFT operations
│
├── tests/                   # Test suite
│   ├── __init__.py
│   └── test_context_manager.py
│
├── .env.development        # Local development environment
├── .gitignore
├── README.md                # This file
├── requirements.txt         # Python dependencies
└── setup.py                # Package configuration
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Redis Server
- Node.js 16+ (for smart contract interaction)
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/RonaSkull/AI-HiveMind-MVP.git
cd AI-HiveMind-MVP
```

### 2. Set Up Python Environment

```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -e .[test]  # Install in development mode with test dependencies
```

### 3. Configure Environment

Create a `.env` file in the project root:

```ini
# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Blockchain Configuration
WEB3_PROVIDER_URI=https://sepolia.infura.io/v3/YOUR_INFURA_PROJECT_ID
PRIVATE_KEY=your_private_key_here
CONTRACT_ADDRESS=0x...  # After deployment

# Agent Configuration
LOG_LEVEL=INFO
```

### 4. Start Redis

```bash
# Using Docker (recommended)
docker run --name redis -p 6379:6379 -d redis

# Or install locally
# Windows: https://github.com/tporadowski/redis/releases
# Linux: sudo apt install redis-server
# Mac: brew install redis
```

### 5. Run Tests

```bash
pytest tests/ -v
```

## 🤖 Agent Architecture

### Base Agent

The `BaseAgent` class provides common functionality for all agents:

```python
from agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self, agent_id: str, mcp: MCPContextManager):
        super().__init__(agent_id, mcp)
        
    async def _setup(self):
        """Initialize agent-specific resources"""
        pass
        
    async def _execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent's main logic"""
        pass
```

### Available Agents

1. **VaultReaderAgent**
   - Monitors NFT vault state
   - Reports on metrics and events

2. **PricingDecisionAgent**
   - Implements dynamic pricing strategies
   - Analyzes market conditions

3. **PriceExecutionAgent**
   - Handles on-chain transactions
   - Manages gas fees and confirmations

## 🔄 Model Context Protocol (MCP)

The MCP provides shared context and communication between agents:

```python
from mcp.context_manager import MCPContextManager

# Initialize with Redis
mcp = MCPContextManager()

# Update context
context_id = mcp.update(
    agent_id="my_agent",
    data={"key": "value"},
    ttl=3600  # Optional TTL in seconds
)

# Retrieve context
context = mcp.get(context_id)


# Search context
results = mcp.search(agent_id="my_agent", limit=10)
```

## 🧪 Running the System

### Start All Agents

```bash
python -m agents.vault_reader_agent &
python -m agents.pricing_decision_agent &
python -m agents.price_execution_agent &
```

### Monitor System

```bash
# View Redis keys
redis-cli keys "*"

# Monitor logs
tail -f logs/agent_*.log
## 📚 Documentation

### Agent Lifecycle

Each agent follows this lifecycle:

1. **Initialization**: Set up resources and connections
2. **Execution**: Process tasks from the queue
3. **Feedback**: Log results and update context
4. **Cleanup**: Release resources on shutdown

### Error Handling

- Agents automatically retry failed operations
- Critical errors trigger graceful degradation
- All errors are logged with context for debugging

### Monitoring

- Logs are written to `logs/agent_<id>.log`
- Redis stores operational metrics
- Use `redis-cli monitor` for real-time debugging

## 🚀 Next Steps

1. **Enhance Agents**:
   - Add more sophisticated pricing strategies
   - Implement gas optimization
   - Add support for multiple blockchains

2. **Improve MCP**:
   - Add access control
   - Implement context versioning
   - Add support for binary data

3. **Scaling**:
   - Add load balancing
   - Implement sharding for Redis
   - Add support for distributed tracing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📜 License

MIT

## 📞 Contact

For questions or support, please open an issue on GitHub.
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
