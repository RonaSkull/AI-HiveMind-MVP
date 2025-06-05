import { ethers } from 'ethers';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join as pathJoin } from 'path';
import fs from 'fs';

// For ES modules, we need to get the current directory differently
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// --- File Logging Setup ---
const logFilePath = pathJoin(__dirname, 'dynamic_pricing.log');

// Function to ensure log messages are strings
const formatLogMessage = (args) => {
    return args.map(arg => {
        if (arg instanceof Error) return arg.stack;
        if (typeof arg === 'object' && arg !== null) {
            try {
                return JSON.stringify(arg, null, 2);
            } catch (e) {
                return '[Unserializable Object]';
            }
        }
        return String(arg);
    }).join(' ');
};

// Clear log file at the start or create if it doesn't exist
try {
    fs.writeFileSync(logFilePath, `Log started at ${new Date().toISOString()}\n-------------------------------------\n`);
} catch (err) {
    // Use original console.error if file system operations fail early
    console.error('CRITICAL: Failed to initialize log file:', err);
}

const originalConsoleLog = console.log;
console.log = (...args) => {
    const message = formatLogMessage(args);
    originalConsoleLog(message); // Log to console as before
    try {
        fs.appendFileSync(logFilePath, message + '\n');
    } catch (err) {
        originalConsoleLog('CRITICAL: Failed to write to log file:', err); // Use original if fs fails
    }
};

const originalConsoleError = console.error;
console.error = (...args) => {
    const message = formatLogMessage(args);
    originalConsoleError('ERROR:', message); // Log to console as before
    try {
        fs.appendFileSync(logFilePath, 'ERROR: ' + message + '\n');
    } catch (err) {
        originalConsoleLog('CRITICAL: Failed to write error to log file:', err); // Use original if fs fails
    }
};
// --- End File Logging Setup ---

// --- Transaction Count Persistence Setup ---
const lastTxCountFilePath = pathJoin(__dirname, 'lastTransactionCount.json');

function readLastTransactionCount() {
    try {
        if (fs.existsSync(lastTxCountFilePath)) {
            const data = fs.readFileSync(lastTxCountFilePath, 'utf8');
            const jsonData = JSON.parse(data);
            if (typeof jsonData.count === 'number') {
                console.log(`Successfully read last transaction count: ${jsonData.count} from ${lastTxCountFilePath}`);
                return jsonData.count;
            }
            console.warn('Invalid format in lastTransactionCount.json, defaulting to 0.');
            return 0;
        }
        console.log('lastTransactionCount.json not found, defaulting to 0.');
        return 0;
    } catch (error) {
        console.error('Error reading lastTransactionCount.json, defaulting to 0:', error);
        return 0;
    }
}

function writeLastTransactionCount(count) {
    try {
        fs.writeFileSync(lastTxCountFilePath, JSON.stringify({ count: count, lastUpdated: new Date().toISOString() }, null, 2));
        console.log(`Successfully wrote transaction count: ${count} to ${lastTxCountFilePath}`);
    } catch (error) {
        console.error('Error writing to lastTransactionCount.json:', error);
    }
}
// --- End Transaction Count Persistence Setup ---

// Check required environment variables
const requiredEnvVars = [
    'METAMASK_PRIVATE_KEY',
    'SEPOLIA_URL',
    'CONTRACT_ADDRESS',
    'QWEN_API_KEY',
    'HYPERSWARM_TOPIC',
    'PRICE_INCREMENT' // Added PRICE_INCREMENT
];

// Load environment variables from .env file for local development
console.log(`Current NODE_ENV: ${process.env.NODE_ENV}`);
if (process.env.NODE_ENV !== 'production') {
    const envPath = `${__dirname}/../.env.development`;
    console.log(`Attempting to load .env file from: ${envPath}`);
    const result = dotenv.config({ path: envPath });

    if (result.error) {
        console.error('Error loading .env file:', result.error);
    } else {
        console.log('.env file loaded successfully. Parsed variables:', Object.keys(result.parsed || {}));
        // Check critical variable directly from process.env after dotenv.config()
        console.log(`METAMASK_PRIVATE_KEY in process.env after dotenv: ${process.env.METAMASK_PRIVATE_KEY ? 'Found' : 'MISSING or empty'}`);
        if (!process.env.METAMASK_PRIVATE_KEY) {
            console.log('Value of process.env.METAMASK_PRIVATE_KEY:', process.env.METAMASK_PRIVATE_KEY);
        }
    }
} else {
    console.log('NODE_ENV is production, skipping .env file loading.');
}

// Validate environment variables
for (const envVar of requiredEnvVars) {
    if (!process.env[envVar]) {
        // Log which variable is missing before throwing an error
        console.error(`Error: Environment variable ${envVar} is missing.`);
        console.error(`Please ensure ${envVar} is defined in your .env.development file or system environment.`);
        // Also log current process.env to help debug if needed (excluding sensitive ones for general logging)
        // For example: console.log('Current process.env keys:', Object.keys(process.env));
        throw new Error(`Environment variable ${envVar} is missing`);
    }
}

// Get environment variables
const rpcUrl = process.env.SEPOLIA_URL;
const privateKey = process.env.METAMASK_PRIVATE_KEY;
const contractAddress = process.env.CONTRACT_ADDRESS;

// Add detailed logging
console.log("=== Dynamic Pricing Script Started ===");
console.log("Environment:");
console.log(`Node.js version: ${process.version}`);
console.log(`NODE_ENV: ${process.env.NODE_ENV || 'development'}`);
console.log(`Network: ${rpcUrl ? 'Connected to Sepolia' : 'Not connected'}`);
console.log(`Contract: ${contractAddress || 'Not set'}`);

// Contract ABI - Only including the functions we need
const contractABI = [
    'function totalTransactions() view returns (uint256)',
    'function minimumPrice() view returns (uint256)',
    'function setMinimumPrice(uint256 _minimumPrice) external' // Changed to setMinimumPrice
];

// Main function to run the script
async function main() {
    try {
        // Validate required environment variables
        const priceIncrementStr = process.env.PRICE_INCREMENT;
        if (!rpcUrl || !privateKey || !contractAddress || !priceIncrementStr) {
            throw new Error("Missing required environment variables (RPC, Key, Contract Address, or Price Increment). Please check your configuration.");
        }
        const priceIncrement = ethers.utils.parseEther(priceIncrementStr);

        console.log("=== Setting up provider and wallet ===");
        const provider = new ethers.providers.JsonRpcProvider(rpcUrl);
        const wallet = new ethers.Wallet(privateKey, provider);
        
        console.log(`Connected with wallet: ${wallet.address}`);
        
        const blockNumber = await provider.getBlockNumber();
        console.log(`Current block number: ${blockNumber}`);
        
        const balance = await provider.getBalance(wallet.address);
        console.log(`Wallet balance: ${ethers.utils.formatEther(balance)} ETH`);
        
        console.log("\n=== Connecting to Contract ===");
        const contract = new ethers.Contract(contractAddress, contractABI, wallet);
        console.log(`Connected to contract at: ${contractAddress}`);
        
        console.log("\n=== Fetching Contract State & Last Known Transaction Count ===");
        const lastKnownTxCount = readLastTransactionCount();
        const [currentTxCountBigInt, currentMinimumPriceBigInt] = await Promise.all([
            contract.totalTransactions(),
            contract.minimumPrice()
        ]);
        const currentTxCount = Number(currentTxCountBigInt); // Convert BigInt to Number for comparison
        
        console.log(`Last known transaction count (from file): ${lastKnownTxCount}`);
        console.log(`Current transaction count (from contract): ${currentTxCount}`);
        console.log(`Current minimum price (from contract): ${ethers.utils.formatEther(currentMinimumPriceBigInt)} ETH`);
        console.log(`Price increment set to: ${ethers.utils.formatEther(priceIncrement)} ETH`);

        if (currentTxCount > lastKnownTxCount) {
            console.log(`\n=== New Transactions Detected (${currentTxCount} > ${lastKnownTxCount}). Adjusting Minimum Price ===`);
            const newMinimumPrice = currentMinimumPriceBigInt + priceIncrement;
            console.log(`Calculated new minimum price: ${ethers.utils.formatEther(newMinimumPrice)} ETH`);

            try {
                console.log("Attempting to call setMinimumPrice...");
                const tx = await contract.setMinimumPrice(newMinimumPrice);
                console.log(`setMinimumPrice transaction hash: ${tx.hash}`);
                console.log("Waiting for transaction confirmation...");
                const receipt = await tx.wait();
                console.log(`Transaction confirmed in block: ${receipt.blockNumber}`);
                
                const updatedPrice = await contract.minimumPrice();
                console.log(`Successfully updated minimum price on contract. New minimum price: ${ethers.utils.formatEther(updatedPrice)} ETH`);
            } catch (e) {
                console.error("Failed to set new minimum price on contract:", e);
                console.error("This could be due to permissions (wallet not being revenueWallet) or other contract constraints.");
            }
        } else {
            console.log("\nNo new transactions detected or transaction count has not increased. Minimum price adjustment skipped.");
        }
        
        // Update the last known transaction count for the next run
        writeLastTransactionCount(currentTxCount);

        console.log("\n=== Script Completed Successfully ===");
        
    } catch (error) {
        console.error("Error in main execution:", error);
        process.exit(1);
    }
}

// Execute the main function
main().catch(error => {
    console.error("Unhandled error:", error);
    process.exit(1);
});
