const provider = new ethers.providers.Web3Provider(window.ethereum);
const signer = provider.getSigner();
const contract = new ethers.Contract("YOUR_CONTRACT_ADDRESS", abi, signer);

async function mintNFT() {
  const metadata = await fetch('https://qwen.aliyuncs.com/api/v1/services/aigc/text-generation/generation ', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer YOUR_QWEN_API_KEY'
    },
    body: JSON.stringify({
      prompt: "Generate a viral TikTok script about AI ethics",
      model: "qwen-max"
    })
  }).then(res => res.json()).then(data => data.output.text);

  const tx = await contract.mintNFT(metadata, ethers.utils.parseEther("0.1"));
  await tx.wait();
  console.log("NFT minted:", metadata);
}
