// scripts/simulateDemand.js
async function main() {
  const contractAddress = process.env.CONTRACT_ADDRESS;
  if (!contractAddress) {
    console.error("Error: CONTRACT_ADDRESS environment variable is not set.");
    process.exit(1);
  }

  const [signer] = await ethers.getSigners();
  console.log("Using signer:", signer.address);

  const AINFTVault = await ethers.getContractFactory("AINFTVault");
  const contract = new ethers.Contract(contractAddress, AINFTVault.interface, signer);

  // --- 1. Mint an NFT ---
  const metadataURI = "ipfs://example-metadata-uri-for-simulation";
  // Use the contract's current minimumPrice or a value slightly above it for initialPrice
  const minimumPrice = await contract.minimumPrice();
  const initialPrice = minimumPrice; // Or ethers.utils.parseEther("0.011") if minimum is 0.01

  console.log(`Attempting to mint NFT with URI: "${metadataURI}" and price: ${ethers.utils.formatEther(initialPrice)} ETH...`);
  try {
    const mintTx = await contract.mintNFT(metadataURI, initialPrice);
    const mintReceipt = await mintTx.wait();
    console.log("NFT Minted! Transaction Hash:", mintTx.hash);

    // Find the minted NFT's ID from events (more robust)
    let mintedNftId = null;
    for (const event of mintReceipt.events) {
      if (event.event === "NFTMinted") {
        mintedNftId = event.args.id;
        break;
      }
    }

    if (mintedNftId === null || typeof mintedNftId === 'undefined') {
      console.error("Could not determine minted NFT ID from event. Will try to use totalNFTs-1.");
      // Fallback: This assumes totalNFTs was correctly incremented and gives the ID of the *last* minted NFT
      // Note: totalNFTs is incremented *before* assignment in your mintNFT (nftId = totalNFTs++),
      // so the ID of the newly minted NFT is totalNFTs (after mint) - 1.
      const currentTotalNFTs = await contract.totalNFTs();
      mintedNftId = currentTotalNFTs.sub(1); // Subtract 1 because totalNFTs is now the next ID to be minted
    }
    
    console.log("Minted NFT ID:", mintedNftId.toString());

    // --- 2. Evolve the minted NFT (this will increment totalTransactions) ---
    const newMetadataURI = "ipfs://example-evolved-metadata-uri";
    // For evolveNFT, msg.value must be >= minimumPrice
    const evolutionCost = minimumPrice; // Send minimumPrice as the cost for evolution

    console.log(`Attempting to evolve NFT ID: ${mintedNftId.toString()} with new URI: "${newMetadataURI}" and sending ${ethers.utils.formatEther(evolutionCost)} ETH...`);
    
    const evolveTx = await contract.evolveNFT(mintedNftId, newMetadataURI, { value: evolutionCost });
    await evolveTx.wait();
    console.log(`NFT ID ${mintedNftId.toString()} Evolved! Transaction Hash:`, evolveTx.hash);
    console.log("totalTransactions should now be incremented.");

  } catch (error) {
    console.error("Error during simulation script:", error);
    process.exit(1);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
