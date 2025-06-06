require('@nomiclabs/hardhat-waffle'); // Reverted to ethers v5 compatible plugin
const dotenv = require('dotenv');
const path = require('path');

// Load environment variables from .env.development
dotenv.config({ path: path.resolve(__dirname, '.env.development') });

// METAMASK_PRIVATE_KEY should be loaded via dotenv.
// No console logs for private key details.

const sepoliaPrivateKey = process.env.METAMASK_PRIVATE_KEY ? process.env.METAMASK_PRIVATE_KEY.replace(/^"|"$/g, '') : undefined;

module.exports = {
  solidity: '0.8.20',
  networks: {
    sepolia: {
      url: process.env.SEPOLIA_RPC_URL || 'https://ethereum-sepolia.publicnode.com', // Allow override
      chainId: 11155111,
      accounts: sepoliaPrivateKey ? [sepoliaPrivateKey] : [],
      timeout: 120000,
      // gas: 2100000, // Consider removing or increasing if deployment issues occur
      gasPrice: 8000000000
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
