// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./ReentrancyGuard.sol";

contract AINFTVault is ReentrancyGuard {
    uint256 public totalNFTs;
    address public revenueWallet;
    uint256 public minimumPrice = 0.01 ether;
    uint256 public totalRevenue;
    uint256 public totalTransactions;
    uint256 public constant REVENUE_PERCENTAGE = 90;

    constructor(address _revenueWallet) {
        revenueWallet = _revenueWallet;
    }

    struct NFT {
        string metadataURI;
        uint256 price;
        address owner;
    }

    mapping(uint256 => NFT) public nfts;

    event NFTMinted(uint256 indexed id, string metadataURI, uint256 price);
    event NFTSold(uint256 indexed id, address buyer, uint256 price);

    function mintNFT(string memory metadataURI, uint256 initialPrice) public {
        require(initialPrice >= minimumPrice, "Price must be at least minimum price");
        uint256 nftId = totalNFTs++;
        nfts[nftId] = NFT(metadataURI, initialPrice, msg.sender);
        emit NFTMinted(nftId, metadataURI, initialPrice);
    }

    function setMinimumPrice(uint256 _minimumPrice) public {
        require(msg.sender == revenueWallet, "Only revenue wallet can set minimum price");
        minimumPrice = _minimumPrice;
    }

    function buyNFT(uint256 nftId) public payable nonReentrant {
        NFT storage nft = nfts[nftId];
        require(msg.value >= nft.price, "Insufficient funds");
        require(msg.value >= minimumPrice, "Price must be at least minimum price");

        // Calculate revenue split
        uint256 revenueShare = (msg.value * REVENUE_PERCENTAGE) / 100;
        uint256 sellerShare = msg.value - revenueShare;

        // Transfer funds
        address payable previousOwner = payable(nft.owner);
        (bool success1, ) = previousOwner.call{value: sellerShare}("");
        require(success1, "Transfer to seller failed");
        
        address payable wallet = payable(revenueWallet);
        (bool success2, ) = wallet.call{value: revenueShare}("");
        require(success2, "Transfer to revenue wallet failed");

        // Update metrics
        totalRevenue += revenueShare;
        totalTransactions++;

        // Update ownership and price
        nft.owner = msg.sender;
        nfts[nftId].price = msg.value * 110 / 100; // Increase price by 10% for next buyer
        
        emit NFTSold(nftId, msg.sender, msg.value);
    }

    function evolveNFT(uint256 nftId, string memory newMetadata) public payable nonReentrant {
        NFT storage nft = nfts[nftId];
        require(nft.owner == msg.sender, "Only owner can evolve");
        require(msg.value >= minimumPrice, "Evolution cost must be at least minimum price");

        // Calculate revenue split
        uint256 revenueShare = (msg.value * REVENUE_PERCENTAGE) / 100;
        uint256 ownerShare = msg.value - revenueShare;

        // Transfer funds
        address payable wallet = payable(revenueWallet);
        (bool success, ) = wallet.call{value: revenueShare}("");
        require(success, "Transfer to revenue wallet failed");
        
        // Update metrics
        totalRevenue += revenueShare;
        totalTransactions++;

        // Update NFT
        nft.metadataURI = newMetadata;
        nft.price = msg.value * 110 / 100; // Increase price by 10% after evolution
        
        emit NFTMinted(nftId, newMetadata, msg.value);
    }

    /**
     * @notice Allows the revenueWallet to reinvest a portion of the contract's balance into minting new NFTs.
     * @dev 10% of the contract's balance (if sufficient) is used to mint a new NFT.
     *      The remaining 90% of the contract's balance is then transferred to the revenueWallet.
     *      This function can only be called by the revenueWallet.
     */
    function reinvestRevenue() public nonReentrant {
        require(msg.sender == revenueWallet, "Only revenue wallet can reinvest");

        uint256 contractBalance = address(this).balance;
        uint256 reinvestmentAmount = contractBalance / 10; // Use 10% for new NFT

        if (contractBalance >= minimumPrice * 10 && reinvestmentAmount >= minimumPrice) { // Ensure enough for reinvestment and it meets min price
            // Mint a new NFT with a portion of the balance
            // The metadataURI can be made more dynamic or passed as a parameter if needed
            mintNFT("AI-generated reinvested NFT", reinvestmentAmount);

            // Transfer remaining majority of funds to revenueWallet
            uint256 remainingBalance = address(this).balance; // Re-check balance after minting costs (though mintNFT doesn't cost ETH to the contract here)
            if (remainingBalance > 0) {
                (bool success, ) = payable(revenueWallet).call{value: remainingBalance}("");
                require(success, "Transfer to revenue wallet failed");
            }
            totalRevenue += remainingBalance; // Assuming this transfer is part of collected revenue
            totalTransactions++; // Count as a transaction type
        } else {
            // If not enough to reinvest, transfer the whole balance to revenue wallet
            if (contractBalance > 0) {
                 (bool success, ) = payable(revenueWallet).call{value: contractBalance}("");
                 require(success, "Transfer to revenue wallet failed");
                 totalRevenue += contractBalance;
                 totalTransactions++; 
            }
        }
    }
}
