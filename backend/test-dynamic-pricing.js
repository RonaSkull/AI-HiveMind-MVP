const { ethers } = require('ethers');
require('dotenv').config({ path: '../.env.development' });

// Contract ABI - Simplified for testing
const ABI = [
    'function totalTransactions() view returns (uint256)',
    'function minimumPrice() view returns (uint256)',
    'function adjustPriceBasedOnDemand() external'
];

async function testDynamicPricing() {
    console.log("=== Starting Dynamic Pricing Test ===");
    
    // 1. Verify environment variables
    console.log("\n1. Checking environment variables...");
    const requiredVars = [
        'SEPOLIA_URL',
        'METAMASK_PRIVATE_KEY',
        'CONTRACT_ADDRESS',
        'QWEN_API_KEY',
        'HYPERSWARM_TOPIC'
    ];

    for (const varName of requiredVars) {
        if (!process.env[varName]) {
            throw new Error(`Missing required environment variable: ${varName}`);
        }
        console.log(`✅ ${varName} is set`);
    }

    // 2. Connect to Sepolia
    console.log("\n2. Connecting to Sepolia...");
    const provider = new ethers.JsonRpcProvider(process.env.SEPOLIA_URL);
    const blockNumber = await provider.getBlockNumber();
    console.log(`✅ Connected to Sepolia. Current block: ${blockNumber}`);

    // 3. Set up wallet and contract
    console.log("\n3. Setting up wallet and contract...");
    const wallet = new ethers.Wallet(process.env.METAMASK_PRIVATE_KEY, provider);
    const contract = new ethers.Contract(process.env.CONTRACT_ADDRESS, ABI, wallet);
    console.log(`✅ Wallet connected: ${wallet.address}`);
    console.log(`✅ Contract address: ${process.env.CONTRACT_ADDRESS}`);

    // 4. Get current state
    console.log("\n4. Fetching current contract state...");
    const [initialTxCount, initialPrice] = await Promise.all([
        contract.totalTransactions(),
        contract.minimumPrice()
    ]);
    
    console.log(`Current transaction count: ${initialTxCount.toString()}`);
    console.log(`Current minimum price: ${ethers.formatEther(initialPrice)} ETH`);

    // 5. Test price adjustment (read-only first)
    console.log("\n5. Testing price adjustment (read-only)...");
    console.log("Current price before adjustment:", ethers.formatEther(initialPrice), "ETH");
    
    // 6. Calculate expected new price (simulate the logic)
    const priceIncrement = ethers.parseEther(process.env.PRICE_INCREMENT || '0.01');
    const incrementMultiplier = Math.floor(Number(initialTxCount) / 100);
    const expectedNewPrice = ethers.parseEther(process.env.MINIMUM_PRICE || '0.01') + 
                            (priceIncrement * BigInt(incrementMultiplier));
    
    console.log(`Expected new price after adjustment: ${ethers.formatEther(expectedNewPrice)} ETH`);
    
    // 7. If you want to actually execute the transaction, uncomment the following:
    /*
    console.log("\n6. Executing price adjustment transaction...");
    const tx = await contract.adjustPriceBasedOnDemand();
    console.log(`Transaction hash: ${tx.hash}`);
    const receipt = await tx.wait();
    console.log(`Transaction confirmed in block: ${receipt.blockNumber}`);

    // 8. Verify the price was updated
    const newPrice = await contract.minimumPrice();
    console.log(`New minimum price: ${ethers.formatEther(newPrice)} ETH`);
    */

    console.log("\n✅ Test completed successfully!");
}

testDynamicPricing().catch(error => {
    console.error("❌ Test failed:", error);
    process.exit(1);
});
