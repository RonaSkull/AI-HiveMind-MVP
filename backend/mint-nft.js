import dotenv from 'dotenv';
import { ethers } from 'ethers';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables from .env.development
dotenv.config({ path: path.resolve(__dirname, '../.env.development') });

// Ensure QWEN_API_KEY is set
if (!process.env.QWEN_API_KEY || process.env.QWEN_API_KEY === 'YOUR_QWEN_API_KEY' || !process.env.QWEN_API_KEY.startsWith('sk-or-v1-')) {
  console.error('Error: QWEN_API_KEY is not set correctly in .env.development for OpenRouter. Please add your OpenRouter API key.');
  process.exit(1);
}

// Setup provider and signer
const provider = new ethers.providers.JsonRpcProvider(process.env.SEPOLIA_URL);
const privateKey = process.env.PRIVATE_KEY.startsWith('0x') ? process.env.PRIVATE_KEY : '0x' + process.env.PRIVATE_KEY;
const signer = new ethers.Wallet(privateKey, provider);

// Load Contract ABI
const contractArtifactPath = path.resolve(__dirname, '../artifacts/smart-contracts/AINFTVault.sol/AINFTVault.json');
const contractArtifact = JSON.parse(fs.readFileSync(contractArtifactPath, 'utf8'));
const abi = contractArtifact.abi;

const contract = new ethers.Contract(process.env.CONTRACT_ADDRESS, abi, signer);

async function mintNFT() {
  let metadata;
  try {
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.QWEN_API_KEY}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'http://localhost', // Optional, but recommended by OpenRouter
        'X-Title': 'AI HiveMind MVP' // Optional, but recommended by OpenRouter
      },
      body: JSON.stringify({
        model: 'qwen/qwq-32b:free', // Using the model you specified
        messages: [
          { role: 'user', content: 'Generate a viral TikTok script about AI ethics' }
        ]
      })
    });
    if (!response.ok) {
      const errorBody = await response.text();
      console.error(`OpenRouter API error: ${response.status} ${response.statusText}`, errorBody);
      throw new Error(`OpenRouter API request failed with status ${response.status}`);
    }
    const data = await response.json();
    if (!data.choices || data.choices.length === 0 || !data.choices[0].message || !data.choices[0].message.content) {
        console.error('OpenRouter API response does not contain expected content:', data);
        throw new Error('Invalid response structure from OpenRouter API');
    }
    metadata = data.choices[0].message.content;
  } catch (error) {
    console.error('Failed to fetch metadata from OpenRouter:', error);
    // Optionally, re-throw or handle to prevent minting with no metadata
    throw error; 
  }

  try {
    const tx = await contract.mintNFT(metadata, ethers.utils.parseEther("0.1"));
    await tx.wait();
    console.log("NFT minted:", metadata);
  } catch (error) {
    console.error("Minting failed:", error);
  }
}

// To run this script, uncomment the line below or call mintNFT from another module
mintNFT().catch(console.error);
