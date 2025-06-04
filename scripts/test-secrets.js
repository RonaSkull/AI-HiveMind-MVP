const fs = require('fs');
const path = require('path');

console.log('=== Testing Secret Access ===');

// Try to read environment variables
const requiredSecrets = [
    'METAMASK_PRIVATE_KEY',
    'SEPOLIA_URL',
    'CONTRACT_ADDRESS',
    'QWEN_API_KEY',
    'HYPERSWARM_TOPIC'
];

console.log('\n=== Verifying Required Secrets ===');
requiredSecrets.forEach(secret => {
    const value = process.env[secret];
    if (value) {
        console.log(`${secret}: Present (Value length: ${value.length})`);
    } else {
        console.log(`${secret}: NOT PRESENT`);
    }
});

// Test basic Node.js functionality
console.log('\n=== Testing Node.js Functionality ===');
try {
    console.log('Testing HTTP request...');
    const https = require('https');
    const options = {
        hostname: 'api.github.com',
        path: '/meta',
        headers: {
            'User-Agent': 'Node.js'
        }
    };
    
    https.get(options, (res) => {
        console.log(`Status: ${res.statusCode}`);
        res.on('data', (d) => {
            process.stdout.write(d);
        });
    }).on('error', (e) => {
        console.error(`Error: ${e.message}`);
    });
} catch (e) {
    console.error(`Error testing HTTP: ${e.message}`);
}

// Test basic Ethereum connection
console.log('\n=== Testing Ethereum Connection ===');
try {
    const { ethers } = require('ethers');
    const provider = new ethers.providers.JsonRpcProvider(process.env.SEPOLIA_URL);
    provider.getNetwork().then(network => {
        console.log(`Connected to network: ${network.name}`);
        console.log(`Chain ID: ${network.chainId}`);
    }).catch(e => {
        console.error(`Error connecting to Ethereum: ${e.message}`);
    });
} catch (e) {
    console.error(`Error initializing Ethereum: ${e.message}`);
}

console.log('\n=== Tests Complete ===');
