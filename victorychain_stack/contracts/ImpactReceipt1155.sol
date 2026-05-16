// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/// @title ImpactReceipt1155
/// @notice Non-transferable impact receipt tokens for nonprofit donations.
/// @dev Tokens are explicitly non-investment records and carry no profit rights.
contract ImpactReceipt1155 is ERC1155, AccessControl, Pausable {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");
    uint256 public constant WIDOW_IMPACT_RECEIPT = 1;
    uint256 public constant ELDER_IMPACT_RECEIPT = 2;
    uint256 public constant ORPHAN_IMPACT_RECEIPT = 3;
    uint256 public constant MERCY_IMPACT_RECEIPT = 4;
    uint256 public constant EARTH_RESTORATION_RECEIPT = 5;

    string public constant LEGAL_NOTICE =
        "Nonprofit impact record only. No profit, dividends, appreciation, or resale rights.";

    mapping(uint256 => mapping(address => string)) public receiptMetadata;

    constructor(string memory baseUri, address admin) ERC1155(baseUri) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(MINTER_ROLE, admin);
        _grantRole(PAUSER_ROLE, admin);
    }

    function mintImpactReceipt(
        address donor,
        uint256 tokenId,
        uint256 amount,
        string calldata metadataJson
    ) external onlyRole(MINTER_ROLE) whenNotPaused {
        _mint(donor, tokenId, amount, "");
        receiptMetadata[tokenId][donor] = metadataJson;
    }

    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(PAUSER_ROLE) {
        _unpause();
    }

    function _beforeTokenTransfer(
        address operator,
        address from,
        address to,
        uint256[] memory ids,
        uint256[] memory amounts,
        bytes memory data
    ) internal override {
        super._beforeTokenTransfer(operator, from, to, ids, amounts, data);
        if (from != address(0) && to != address(0)) {
            revert("SBT: transfer disabled");
        }
    }
}
