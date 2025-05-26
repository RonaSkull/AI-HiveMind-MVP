contract AINFTVault {
    uint256 public totalNFTs;
    address public revenueWallet = 0xYourWalletHere;

    struct NFT {
        string metadataURI;
        uint256 price;
        address owner;
    }

    mapping(uint256 => NFT) public nfts;

    event NFTMinted(uint256 indexed id, string metadataURI, uint256 price);
    event NFTSold(uint256 indexed id, address buyer, uint256 price);

    function mintNFT(string memory metadataURI, uint256 initialPrice) public {
        uint256 nftId = totalNFTs++;
        nfts[nftId] = NFT(metadataURI, initialPrice, msg.sender);
        emit NFTMinted(nftId, metadataURI, initialPrice);
    }

    function buyNFT(uint256 nftId) public payable {
        NFT storage nft = nfts[nftId];
        require(msg.value >= nft.price, "Insufficient funds");

        // 90% to you, 10% to seller
        address payable previousOwner = payable(nft.owner);
        previousOwner.transfer(msg.value * 10 / 100);
        revenueWallet.transfer(msg.value * 90 / 100); // 90% cut
        nft.owner = msg.sender;
        emit NFTSold(nftId, msg.sender, msg.value);
    }

    function evolveNFT(uint256 nftId, string memory newMetadata) public payable {
        NFT storage nft = nfts[nftId];
        require(nft.owner == msg.sender, "Only owner can evolve");

        // 90% to you, 10% reinvested
        revenueWallet.transfer(msg.value * 90 / 100);
        nft.metadataURI = newMetadata;
        nft.price = msg.value;
    }
}
