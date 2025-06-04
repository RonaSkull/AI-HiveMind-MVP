import { ethers } from "ethers";
import dotenv from 'dotenv';

// Load environment variables from .env file for local development
if (!process.env.CI) {
  dotenv.config();
}

// Get environment variables
const rpcUrl = process.env.SEPOLIA_URL;
const privateKey = process.env.METAMASK_PRIVATE_KEY;
const contractAddress = process.env.CONTRACT_ADDRESS;

if (!privateKey || !rpcUrl || !contractAddress) {
  console.error("=== ERROR: Missing required environment variables ===");
  console.error("Please set the following variables in GitHub Secrets:");
  console.error("- METAMASK_PRIVATE_KEY (current value: " + (privateKey ? "SET" : "MISSING") + ")");
  console.error("- SEPOLIA_URL (current value: " + (rpcUrl ? "SET" : "MISSING") + ")");
  console.error("- CONTRACT_ADDRESS (current value: " + (contractAddress ? "SET" : "MISSING") + ")");
  console.error("\nCurrent values:");
  console.error("- METAMASK_PRIVATE_KEY: " + (privateKey ? "***SET***" : "MISSING"));
  console.error("- SEPOLIA_URL: " + (rpcUrl || "MISSING"));
  console.error("- CONTRACT_ADDRESS: " + (contractAddress || "MISSING"));
  console.error("\nTo set these variables:");
  console.error("1. Go to your GitHub repository -> Settings -> Secrets and variables -> Actions");
  console.error("2. Click 'New repository secret' for each variable");
  console.error("3. Copy the values from your .env.development file");
  process.exit(1);
}

// PLACEHOLDER: "abi": 
const contractABI = [ // The ENTIRE JSON ABI from AINFTVault.json starts here
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "_revenueWallet",
          "type": "address"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "constructor"
    },
    {
      "anonymous": false,
      "inputs": [
        {
          "indexed": true,
          "internalType": "uint256",
          "name": "id",
          "type": "uint256"
        },
        {
          "indexed": false,
          "internalType": "string",
          "name": "metadataURI",
          "type": "string"
        },
        {
          "indexed": false,
          "internalType": "uint256",
          "name": "price",
          "type": "uint256"
        }
      ],
      "name": "NFTMinted",
      "type": "event"
    },
    {
      "anonymous": false,
      "inputs": [
        {
          "indexed": true,
          "internalType": "uint256",
          "name": "id",
          "type": "uint256"
        },
        {
          "indexed": false,
          "internalType": "address",
          "name": "buyer",
          "type": "address"
        },
        {
          "indexed": false,
          "internalType": "uint256",
          "name": "price",
          "type": "uint256"
        }
      ],
      "name": "NFTSold",
      "type": "event"
    },
    {
      "inputs": [],
      "name": "REVENUE_PERCENTAGE",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "nftId",
          "type": "uint256"
        }
      ],
      "name": "buyNFT",
      "outputs": [],
      "stateMutability": "payable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "nftId",
          "type": "uint256"
        },
        {
          "internalType": "string",
          "name": "newMetadata",
          "type": "string"
        }
      ],
      "name": "evolveNFT",
      "outputs": [],
      "stateMutability": "payable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "minimumPrice",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "string",
          "name": "metadataURI",
          "type": "string"
        },
        {
          "internalType": "uint256",
          "name": "initialPrice",
          "type": "uint256"
        }
      ],
      "name": "mintNFT",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "name": "nfts",
      "outputs": [
        {
          "internalType": "string",
          "name": "metadataURI",
          "type": "string"
        },
        {
          "internalType": "uint256",
          "name": "price",
          "type": "uint256"
        },
        {
          "internalType": "address",
          "name": "owner",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "reinvestRevenue",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "revenueWallet",
      "outputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "_minimumPrice",
          "type": "uint256"
        }
      ],
      "name": "setMinimumPrice",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "totalNFTs",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "totalRevenue",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "totalTransactions",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    }
  ];

async function adjustPriceBasedOnDemand() {
  try {
    console.log(`Connecting to RPC: ${rpcUrl}`);
    console.log("Attempting to connect to provider...");
    const provider = new ethers.providers.JsonRpcProvider(rpcUrl);
    console.log(`Connected to provider: ${rpcUrl}`);
    
    console.log(`Using wallet for address: ${new ethers.Wallet(privateKey).address}`);
    const wallet = new ethers.Wallet(privateKey, provider);
    
    console.log(`Interacting with contract at: ${contractAddress}`);
    const contract = new ethers.Contract(contractAddress, contractABI, wallet);

    const currentTotalTransactions = await contract.totalTransactions();
    console.log(`Current total transactions: ${currentTotalTransactions.toString()}`);

    // Dynamic pricing logic: 0.01 base, 1% increase for every 100 transactions
    // Example: 0 transactions = 0.01 ETH
    //          100 transactions = 0.01 * (1 + 100/100) = 0.01 * 2 = 0.02 ETH
    //          50 transactions = 0.01 * (1 + 50/100) = 0.01 * 1.5 = 0.015 ETH
    // More robust: ensure BigNumber operations for precision with ETH values
    const basePriceEth = 0.01;
    const increaseFactor = ethers.BigNumber.from(currentTotalTransactions.toString()).div(ethers.BigNumber.from(100));
    const newMinimumPriceEth = basePriceEth + (Math.floor(Number(currentTotalTransactions) / 100) * 0.01);
    console.log(`Calculated new minimum price (ETH): ${newMinimumPriceEth.toFixed(5)}`); // Convert factor to number for JS multiplication
    
    const newMinPriceWei = ethers.utils.parseUnits(newMinimumPriceEth.toFixed(18), 'ether'); // toFixed to handle potential floating point inaccuracies before parsing

    const currentMinPriceWei = await contract.minimumPrice(); // Assuming 'minimumPrice' is the getter for your minimum price state variable
    const currentMinimumPriceEth = ethers.utils.formatUnits(currentMinPriceWei, 'ether');
    console.log(`Current minimum price (ETH): ${currentMinimumPriceEth}`);

    if (newMinPriceWei.eq(currentMinPriceWei)) {
      console.log(`New minimum price (${ethers.utils.formatEther(newMinPriceWei)} ETH) is the same as current. No update needed.`);
      return;
    }

    console.log(`Attempting to update minimum price to: ${ethers.utils.formatUnits(newMinPriceWei, 'ether')} ETH...`);
    console.log(`New price (${newMinimumPriceEth.toFixed(5)}) is different from current price (${currentMinimumPriceEth}). Attempting to update.`);
    const tx = await contract.connect(provider).setMinimumPrice(newMinPriceWei);
    console.log(`Transaction sent: ${tx.hash}`);
    await tx.then();
    console.log("Minimum price updated successfully!");
  } catch (error) {
    console.error("Error adjusting price:", error);
    process.exit(1);
  }
}

adjustPriceBasedOnDemand();
