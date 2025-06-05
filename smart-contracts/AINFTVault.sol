// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

/**
 * @title AINFTVault
 * @notice A smart contract for minting, trading, and evolving AI-generated NFTs.
 * @dev Implements dynamic pricing adjustments and revenue sharing.
 *      Uses ReentrancyGuard for security.
 */
contract AINFTVault is ReentrancyGuard {
    using Strings for uint256;
    // --- Constants ---
    uint256 public constant REVENUE_PERCENTAGE = 90;
    uint256 public constant NEXT_PRICE_MULTIPLIER_PERCENT = 110;
    uint256 public constant REINVESTMENT_DIVISOR = 10;

    // --- Errors ---
    error OnlyRevenueWallet();
    error PriceTooLow();
    error OwnerCannotBeZeroAddress();
    error NFTNotOwnedOrNonExistent();
    error InsufficientFunds();
    error OnlyNFTOwner();
    error TransferFailed();
    error ReinvestmentConditionsNotMet();
    error CannotBuyYourOwnNFT();

    // --- State Variables ---
    /// @notice The total number of NFTs ever minted. Used for ID generation.
    uint256 public totalNFTs;
    /// @notice The address designated to receive revenue shares and manage certain contract functions.
    address public revenueWallet;
    /// @notice The minimum price an NFT can be listed for or an evolution can cost.
    uint256 public minimumPrice = 0.01 ether;
    /// @notice The cumulative revenue share collected by the revenueWallet.
    uint256 public totalRevenue;
    /// @notice A general counter for significant contract interactions (buy, evolve, reinvest).
    uint256 public totalTransactions;

    /// @notice The base URI for constructing token URIs. e.g., "https://api.example.com/nft/"
    string public baseURI;

    // --- Structs ---
    struct NFT {
        string metadataURI;
        uint256 price;
        address owner;
    }

    // --- Mappings ---
    /// @notice Mapping from NFT ID to NFT details.
    mapping(uint256 => NFT) public nfts;

    // --- Events ---
    event MinimumPriceChanged(uint256 oldPrice, uint256 newPrice, address indexed changedBy);
    event BaseURIChanged(string oldBaseURI, string newBaseURI, address indexed changedBy);
    event NFTMinted(uint256 indexed id, address indexed owner, string metadataURI, uint256 price);
    event NFTSold(uint256 indexed id, address buyer, uint256 price);
    event NFTEvolved(uint256 indexed id, address indexed owner, string newMetadataURI, uint256 evolutionCost, uint256 newPrice);

    // --- Constructor ---
    /**
     * @notice Sets up the contract with the designated revenue wallet.
     * @param _revenueWallet The address for the revenue wallet.
     */
    constructor(address _revenueWallet) {
        if (_revenueWallet == address(0)) revert OwnerCannotBeZeroAddress(); // Using OwnerCannotBeZeroAddress for consistency
        revenueWallet = _revenueWallet;
    }

    // --- Internal Functions ---
    /**
     * @dev Internal function to mint a new NFT.
     * @param _owner The address that will own the newly minted NFT.
     * @param _initialPrice The initial selling price of the NFT.
     */
    function _mintNFT(address _owner, uint256 _initialPrice) internal {
        if (_initialPrice < minimumPrice) revert PriceTooLow();
        if (_owner == address(0)) revert OwnerCannotBeZeroAddress();
        
        uint256 nftId = totalNFTs++;
        string memory constructedMetadataURI = string(abi.encodePacked(baseURI, nftId.toString()));
        nfts[nftId] = NFT(constructedMetadataURI, _initialPrice, _owner);
        emit NFTMinted(nftId, _owner, constructedMetadataURI, _initialPrice);
    }

    // --- Public External Functions ---
    /**
     * @notice Allows any user to mint an NFT for themselves.
     * @param _initialPrice The initial price for the NFT. Must be >= minimumPrice.
     */
    function mintNFTForSelf(uint256 _initialPrice) public {
        _mintNFT(msg.sender, _initialPrice);
    }

    /**
     * @notice Sets the global minimum price for NFTs and evolutions.
     * @dev Can only be called by the `revenueWallet`.
     * @param _minimumPrice The new minimum price in wei.
     */
    /**
     * @notice Sets the base URI for all token metadata.
     * @dev Can only be called by the `revenueWallet`.
     * @param _newBaseURI The new base URI string.
     */
    function setBaseURI(string memory _newBaseURI) public {
        if (msg.sender != revenueWallet) revert OnlyRevenueWallet();
        string memory oldURI = baseURI;
        baseURI = _newBaseURI;
        emit BaseURIChanged(oldURI, baseURI, msg.sender);
    }

    function setMinimumPrice(uint256 _minimumPrice) public {
        if (msg.sender != revenueWallet) revert OnlyRevenueWallet();
        uint256 oldPrice = minimumPrice;
        minimumPrice = _minimumPrice;
        emit MinimumPriceChanged(oldPrice, minimumPrice, msg.sender);
    }

    /**
     * @notice Returns the URI for a given token ID.
     * @param tokenId The ID of the token.
     * @return The URI string for the token's metadata.
     */
    function tokenURI(uint256 tokenId) public view returns (string memory) {
        if (nfts[tokenId].owner == address(0)) revert NFTNotOwnedOrNonExistent(); // Or handle as per ERC721 spec (e.g., revert if not exists)
        return nfts[tokenId].metadataURI;
    }

    /**
     * @notice Allows a user to buy an existing NFT.
     * @dev Transfers funds to the previous owner and `revenueWallet`. Increases NFT price for next sale.
     * @param nftId The ID of the NFT to buy.
     */
    function buyNFT(uint256 nftId) public payable nonReentrant {
        if (nfts[nftId].owner == msg.sender) revert CannotBuyYourOwnNFT();
        NFT storage nft = nfts[nftId];
        if (nft.owner == address(0)) revert NFTNotOwnedOrNonExistent();
        if (msg.value < nft.price) revert InsufficientFunds();
        if (msg.value < minimumPrice) revert PriceTooLow();

        uint256 revenueShare = (msg.value * REVENUE_PERCENTAGE) / 100;
        uint256 sellerShare = msg.value - revenueShare;

        address payable previousOwner = payable(nft.owner);
        (bool success1, ) = previousOwner.call{value: sellerShare}("");
        if (!success1) revert TransferFailed();
        
        address payable wallet = payable(revenueWallet);
        (bool success2, ) = wallet.call{value: revenueShare}("");
        if (!success2) revert TransferFailed();

        totalRevenue += revenueShare;
        totalTransactions++;

        nft.owner = msg.sender;
        nfts[nftId].price = (msg.value * NEXT_PRICE_MULTIPLIER_PERCENT) / 100;
        
        emit NFTSold(nftId, msg.sender, msg.value);
    }

    /**
     * @notice Allows the owner of an NFT to evolve it by providing new metadata.
     * @dev A fee is charged, shared with `revenueWallet`. Increases NFT price.
     * @param nftId The ID of the NFT to evolve.
     * @param newMetadata The new metadata URI for the NFT.
     */
    function evolveNFT(uint256 nftId, string memory newMetadata) public payable nonReentrant {
        NFT storage nft = nfts[nftId];
        if (nft.owner != msg.sender) revert OnlyNFTOwner();
        if (msg.value < minimumPrice) revert PriceTooLow();

        uint256 revenueShare = (msg.value * REVENUE_PERCENTAGE) / 100;

        address payable wallet = payable(revenueWallet);
        (bool success, ) = wallet.call{value: revenueShare}("");
        if (!success) revert TransferFailed();
        
        totalRevenue += revenueShare;
        totalTransactions++;

        nft.metadataURI = newMetadata;
        nft.price = (msg.value * NEXT_PRICE_MULTIPLIER_PERCENT) / 100;
        
        emit NFTEvolved(nftId, nft.owner, newMetadata, msg.value, nft.price);
    }

    /**
     * @notice Allows the `revenueWallet` to reinvest a portion of the contract's balance.
     * @dev Mints a new NFT (owned by `revenueWallet`) using a fraction of the balance and transfers the rest to `revenueWallet`.
     *      If conditions for reinvestment aren't met, transfers the entire balance to `revenueWallet`.
     */
    function reinvestRevenue() public nonReentrant {
        if (msg.sender != revenueWallet) revert OnlyRevenueWallet();

        uint256 contractBalance = address(this).balance;
        uint256 reinvestmentAmount = contractBalance / REINVESTMENT_DIVISOR;

        if (contractBalance >= (minimumPrice * REINVESTMENT_DIVISOR) && reinvestmentAmount >= minimumPrice) {
            _mintNFT(revenueWallet, reinvestmentAmount);

            uint256 remainingBalance = address(this).balance;
            if (remainingBalance > 0) {
                (bool successTransfer, ) = payable(revenueWallet).call{value: remainingBalance}("");
                if (!successTransfer) revert TransferFailed();
            }
            totalTransactions++;
        } else {
            if (contractBalance > 0) {
                 (bool successTransfer, ) = payable(revenueWallet).call{value: contractBalance}("");
                 if (!successTransfer) revert TransferFailed();
                 totalTransactions++;
            }
            // Optional: revert or emit event if no action taken due to zero balance
            // if (contractBalance == 0) revert ReinvestmentConditionsNotMet(); // Or some other error/event
        }
    }
}
