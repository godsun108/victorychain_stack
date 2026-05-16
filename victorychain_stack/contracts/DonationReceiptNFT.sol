// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

/// @title DonationReceiptNFT
/// @notice Optional ERC-721 receipt NFT for donation attestations.
/// @dev Prefer restricted transfer mode for compliance unless legal review permits.
contract DonationReceiptNFT is ERC721URIStorage, AccessControl {
    bytes32 public constant RECEIPT_MINTER_ROLE = keccak256("RECEIPT_MINTER_ROLE");

    uint256 public nextTokenId = 1;
    bool public transferable = false;

    constructor(address admin) ERC721("VictoryChain Donation Receipt", "VCDR") {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(RECEIPT_MINTER_ROLE, admin);
    }

    function setTransferable(bool allowed) external onlyRole(DEFAULT_ADMIN_ROLE) {
        transferable = allowed;
    }

    function mintReceipt(address donor, string calldata metadataUri) external onlyRole(RECEIPT_MINTER_ROLE) returns (uint256) {
        uint256 tokenId = nextTokenId++;
        _safeMint(donor, tokenId);
        _setTokenURI(tokenId, metadataUri);
        return tokenId;
    }

    function _beforeTokenTransfer(address from, address to, uint256 tokenId, uint256 batchSize) internal override {
        super._beforeTokenTransfer(from, to, tokenId, batchSize);
        if (!transferable && from != address(0) && to != address(0)) {
            revert("transfer restricted");
        }
    }
}
