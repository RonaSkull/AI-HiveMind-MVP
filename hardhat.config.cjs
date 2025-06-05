require('@nomiclabs/hardhat-ethers');
const dotenv = require('dotenv');
const path = require('path');

// Load environment variables from .env.development
dotenv.config({ path: path.resolve(__dirname, '.env.development') });

// Debug log to verify private key is loaded
console.log('Private key loaded:', process.env.METAMASK_PRIVATE_KEY ? 'Yes' : 'No');
console.log('Private key length:', process.env.METAMASK_PRIVATE_KEY ? process.env.METAMASK_PRIVATE_KEY.length : 'Not found');

module.exports = {
  solidity: '0.8.0',
  networks: {
    sepolia: {
      url: 'https://ethereum-sepolia.publicnode.com', // PublicNode Sepolia RPC
      chainId: 11155111, // Sepolia network ID
      accounts: [process.env.METAMASK_PRIVATE_KEY ? process.env.METAMASK_PRIVATE_KEY.replace(/^"|"$/g, '') : ''], // Remove any surrounding quotes
      timeout: 120000, // 2 minutes timeout for MetaMask
      gas: 2100000,
      gasPrice: 8000000000 // 8 gwei
    }
  },
  paths: {
    sources: "./smart-contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts"
  },
  mocha: {
    timeout: 20000
  }
};
