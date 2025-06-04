const { ethers } = require('ethers');
const fs = require('fs');
const path = require('path');

console.log('=== Testing Dynamic Pricing Functionality ===');

// Load contract ABI
const abiPath = path.join(__dirname, '..', 'backend', 'AINFTVault.json');
let contractABI;
try {
    contractABI = JSON.parse(fs.readFileSync(abiPath)).abi;
    console.log('\n=== Contract ABI ===');
    console.log(`ABI loaded successfully`);
} catch (e) {
    console.error(`Error loading ABI: ${e.message}`);
    process.exit(1);
}

// Test Ethereum connection
console.log('\n=== Testing Ethereum Connection ===');
try {
    const provider = new ethers.providers.JsonRpcProvider(process.env.SEPOLIA_URL);
    
    // Test network connection
    provider.getNetwork().then(network => {
        console.log(`Connected to network: ${network.name}`);
        console.log(`Chain ID: ${network.chainId}`);
    }).catch(e => {
        console.error(`Error connecting to network: ${e.message}`);
        process.exit(1);
    });

    // Test contract interaction
    const wallet = new ethers.Wallet(process.env.METAMASK_PRIVATE_KEY, provider);
    const contract = new ethers.Contract(process.env.CONTRACT_ADDRESS, contractABI, wallet);

    // Test contract methods
    console.log('\n=== Testing Contract Methods ===');
    
    contract.minimumPrice().then(price => {
        console.log(`Current minimum price: ${ethers.utils.formatEther(price)}`);
    }).catch(e => {
        console.error(`Error getting minimum price: ${e.message}`);
    });

    contract.totalTransactions().then(count => {
        console.log(`Total transactions: ${count}`);
    }).catch(e => {
        console.error(`Error getting transaction count: ${e.message}`);
    });

} catch (e) {
    console.error(`Error initializing Ethereum: ${e.message}`);
    process.exit(1);
}

console.log('\n=== Tests Complete ===');
