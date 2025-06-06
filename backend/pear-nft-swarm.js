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
if (!process.env.METAMASK_PRIVATE_KEY) { 
  console.error('Error: METAMASK_PRIVATE_KEY is not set in .env.development.');
  process.exit(1);
}
const privateKey = process.env.METAMASK_PRIVATE_KEY.startsWith('0x') ? process.env.METAMASK_PRIVATE_KEY : '0x' + process.env.METAMASK_PRIVATE_KEY;
const signer = new ethers.Wallet(privateKey, provider);
console.log(`AI Agent Address (Signer): ${signer.address}`);

// Load Contract ABI
const contractArtifactPath = path.resolve(__dirname, '../artifacts/smart-contracts/AINFTVault.sol/AINFTVault.json');
const contractArtifact = JSON.parse(fs.readFileSync(contractArtifactPath, 'utf8'));
const abi = contractArtifact.abi;
const contract = new ethers.Contract(process.env.CONTRACT_ADDRESS, abi, signer);

// Hyperswarm P2P setup
const swarm = new Hyperswarm();
const topicString = process.env.HYPERSWARM_TOPIC || 'ai-nft-market-fallback-topic'; 
const topicBuffer = Buffer.alloc(32).fill(topicString);
console.log('AI Agent joining Hyperswarm topic:', topicString);

swarm.join(topicBuffer, {
  server: true, // Act as a server on the topic
  client: false // Not strictly necessary to connect to others initially as a server
});

swarm.on('connection', async (socket, peerInfo) => {
  console.log('New P2P connection from:', peerInfo.publicKey.toString('hex'));
  try {
    // 1. Generate NFT metadata using OpenRouter (for announcement, not directly for minting if using mintNFTForSelf)
    console.log('Generating NFT metadata via OpenRouter for announcement purposes...');
    let generatedMetadataForAnnouncement;
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
            { role: 'user', content: 'Generate a compelling description for a unique digital art piece about symbiotic AI.' } // Consider making this prompt dynamic
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
      generatedMetadataForAnnouncement = data.choices[0].message.content;
      console.log('Metadata for announcement generated:', generatedMetadataForAnnouncement.substring(0, 100) + '...');
    } catch (error) {
      console.error('Failed to fetch metadata from OpenRouter for announcement:', error);
      // Decide if this is fatal for the interaction. Maybe proceed without off-chain metadata.
      generatedMetadataForAnnouncement = "AI generated content - details pending on-chain."; 
    }

    // 2. Mint the NFT using the AINFTVault contract's mintNFTForSelf method
    console.log('Minting NFT on Sepolia via contract (mintNFTForSelf):', process.env.CONTRACT_ADDRESS);
    const initialPriceForMinting = ethers.utils.parseEther("0.01"); // Define an initial price, must be >= contract.minimumPrice()
    // TODO: Consider fetching contract.minimumPrice() and using it or ensuring initialPriceForMinting respects it.
    const tx = await contract.mintNFTForSelf(initialPriceForMinting); // Pass initial price
    const receipt = await tx.wait();
    console.log('NFT Minted! Transaction Hash:', tx.hash);
    
    // Extract NFT ID and other details from events
    let nftId = 'Unknown';
    let mintedPrice = 'N/A'; // Price set by contract
    let metadataURIFromEvent = 'N/A'; // Metadata URI set by contract

    const mintEvent = receipt.events?.find(e => e.event === 'NFTMinted');
    if (mintEvent && mintEvent.args) {
        nftId = mintEvent.args.tokenId.toString(); // CORRECTED: tokenId
        mintedPrice = ethers.utils.formatEther(mintEvent.args.price);
        metadataURIFromEvent = mintEvent.args.metadataURI;
        console.log('Minted NFT ID:', nftId);
        console.log('Minted Price (from event):', mintedPrice, 'ETH');
        console.log('Metadata URI (from event):', metadataURIFromEvent);
    } else {
        console.warn('NFTMinted event not found or args missing. Check contract and event signature.');
    }

    // 3. Announce the newly minted NFT to the connected peer
    // Use generatedMetadataForAnnouncement for summary, but acknowledge on-chain details might differ
    const announcement = {
      type: 'NFT_MINTED_ANNOUNCEMENT',
      nftId: nftId,
      // Use off-chain generated metadata for a quick summary if available
      metadataSummary: generatedMetadataForAnnouncement ? generatedMetadataForAnnouncement.substring(0, 100) + '...' : "See on-chain metadata.",
      onChainMetadataURI: metadataURIFromEvent, // Add this for clarity
      price: mintedPrice + ' ETH', // Price from the event
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
