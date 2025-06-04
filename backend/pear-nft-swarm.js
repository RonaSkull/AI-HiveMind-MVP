import dotenv from 'dotenv';
import Hyperswarm from 'hyperswarm';
import { ethers } from 'ethers';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables from .env.development
dotenv.config({ path: path.resolve(__dirname, '../.env.development') });

// Ensure API_KEY (for OpenRouter) is set
if (!process.env.QWEN_API_KEY || !process.env.QWEN_API_KEY.startsWith('sk-or-v1-')) {
  console.error('Error: QWEN_API_KEY (for OpenRouter) is not set correctly in .env.development.');
  process.exit(1);
}

// Setup provider and signer for blockchain interaction
const provider = new ethers.providers.JsonRpcProvider(process.env.SEPOLIA_URL);
const privateKey = process.env.PRIVATE_KEY.startsWith('0x') ? process.env.PRIVATE_KEY : '0x' + process.env.PRIVATE_KEY;
const signer = new ethers.Wallet(privateKey, provider);
console.log(`AI Agent Address (Signer): ${signer.address}`);

// Load Contract ABI
const contractArtifactPath = path.resolve(__dirname, '../artifacts/smart-contracts/AINFTVault.sol/AINFTVault.json');
const contractArtifact = JSON.parse(fs.readFileSync(contractArtifactPath, 'utf8'));
const abi = contractArtifact.abi;
const contract = new ethers.Contract(process.env.CONTRACT_ADDRESS, abi, signer);

// Hyperswarm P2P setup
const swarm = new Hyperswarm();
const topicString = 'ai-nft-market-v3'; // New topic for hyperswarm
const topicBuffer = Buffer.alloc(32).fill(topicString);
console.log('AI Agent joining Hyperswarm topic:', topicString);

swarm.join(topicBuffer, {
  server: true, // Act as a server on the topic
  client: false // Not strictly necessary to connect to others initially as a server
});

swarm.on('connection', async (socket, peerInfo) => {
  console.log('New P2P connection from:', peerInfo.publicKey.toString('hex'));
  try {
    // 1. Generate NFT metadata using OpenRouter
    console.log('Generating NFT metadata via OpenRouter...');
    let generatedMetadata;
    try {
      const openRouterResponse = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${process.env.QWEN_API_KEY}`,
          'Content-Type': 'application/json',
          'HTTP-Referer': 'http://localhost', // Optional, but recommended
          'X-Title': 'AI HiveMind Peer Agent' // Optional
        },
        body: JSON.stringify({
          model: 'qwen/qwq-32b:free', // Or any other model you prefer
          messages: [
            { role: 'user', content: 'Generate a compelling description for a unique digital art piece about symbiotic AI.' }
          ]
        })
      });
      if (!openRouterResponse.ok) {
        const errorBody = await openRouterResponse.text();
        console.error(`OpenRouter API error: ${openRouterResponse.status} ${openRouterResponse.statusText}`, errorBody);
        throw new Error(`OpenRouter API request failed with status ${openRouterResponse.status}`);
      }
      const data = await openRouterResponse.json();
      if (!data.choices || data.choices.length === 0 || !data.choices[0].message || !data.choices[0].message.content) {
          console.error('OpenRouter API response does not contain expected content:', data);
          throw new Error('Invalid response structure from OpenRouter API');
      }
      generatedMetadata = data.choices[0].message.content;
      console.log('Metadata generated:', generatedMetadata.substring(0, 100) + '...');
    } catch (error) {
      console.error('Failed to fetch metadata from OpenRouter:', error);
      socket.write(JSON.stringify({ error: 'Failed to generate metadata' }));
      return; // Stop if metadata generation fails
    }

    // 2. Mint the NFT using the AINFTVault contract
    console.log('Minting NFT on Sepolia via contract:', process.env.CONTRACT_ADDRESS);
    const initialPrice = ethers.utils.parseEther("0.01"); // Example price
    const tx = await contract.mintNFT(generatedMetadata, initialPrice);
    const receipt = await tx.wait();
    console.log('NFT Minted! Transaction Hash:', tx.hash);
    
    // Extract NFT ID from events (assuming NFTMinted event exists with 'id')
    let nftId = 'Unknown';
    const mintEvent = receipt.events?.find(e => e.event === 'NFTMinted');
    if (mintEvent && mintEvent.args) {
        nftId = mintEvent.args.id.toString();
        console.log('Minted NFT ID:', nftId);
    }

    // 3. Announce the newly minted NFT to the connected peer
    const announcement = {
      type: 'NFT_MINTED_ANNOUNCEMENT',
      nftId: nftId,
      metadataSummary: generatedMetadata.substring(0, 100) + '...',
      price: ethers.utils.formatEther(initialPrice) + ' ETH',
      owner: signer.address,
      contract: process.env.CONTRACT_ADDRESS
    };
    try {
      socket.write(JSON.stringify(announcement));
      console.log('Announced new NFT to peer:', announcement);
    } catch (writeError) {
      console.error(`Error writing announcement to peer ${peerInfo.publicKey.toString('hex').substring(0,10)}...:`, writeError.message);
      // Decide if you need to do more here, e.g., close the socket if it's unusable
    }

    // The 'pear.executeTrade(socket)' is too vague.
    // A real trade would involve the other peer calling 'buyNFT' on the contract.
    // This script's role for now is to mint and announce.

  } catch (error) {
    console.error("Error during P2P connection handling or NFT minting:", error);
    socket.write(JSON.stringify({ error: 'An internal error occurred' }));
  }
});

// Keep the process alive for P2P communication
// Handle graceful shutdown if needed
process.on('SIGINT', () => {
  console.log('Shutting down AI agent...');
  swarm.leave(topicBuffer).then(() => {
    console.log('Left Hyperswarm topic.');
    return swarm.destroy();
  }).then(() => {
    console.log('Hyperswarm instance destroyed.');
    process.exit(0);
  }).catch(err => {
    console.error('Error during shutdown:', err);
    process.exit(1);
  });
});
