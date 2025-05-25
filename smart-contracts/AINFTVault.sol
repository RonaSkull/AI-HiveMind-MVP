// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract AINFTVault {
    uint256 public totalNFTs;
    address public revenueWallet = 0xYourWalletHere; // Replace with your MetaMask address

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
        address payable previousOwner = payable(nft.owner);
        previousOwner.transfer(nft.price * 95 / 100); // 95% to seller
        revenueWallet.transfer(nft.price * 5 / 100); // 5% to you
        nft.owner = msg.sender;
        emit NFTSold(nftId, msg.sender, nft.price);
    }

    function evolveNFT(uint256 nftId, string memory newMetadata) public payable {
        NFT storage nft = nfts[nftId];
        require(nft.owner == msg.sender, "Only owner can evolve");
        nft.metadataURI = newMetadata;
        nft.price = msg.value; // New price after evolution
        revenueWallet.transfer(msg.value * 10 / 100); // 10% cut
    }
}
