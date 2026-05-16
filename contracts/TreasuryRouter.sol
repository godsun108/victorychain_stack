// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/// @title TreasuryRouter
/// @notice Routes incoming donations to category treasuries for transparent accounting.
contract TreasuryRouter is AccessControl, Pausable {
    bytes32 public constant TREASURY_ADMIN_ROLE = keccak256("TREASURY_ADMIN_ROLE");

    enum Category {
        WIDOW,
        ELDER,
        ORPHAN,
        MERCY,
        EARTH
    }

    mapping(Category => address payable) public treasuryWallets;

    event DonationRouted(
        address indexed donor,
        Category indexed category,
        uint256 amount,
        string paymentReference,
        string receiptId
    );

    constructor(
        address admin,
        address payable widow,
        address payable elder,
        address payable orphan,
        address payable mercy,
        address payable earth
    ) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(TREASURY_ADMIN_ROLE, admin);
        treasuryWallets[Category.WIDOW] = widow;
        treasuryWallets[Category.ELDER] = elder;
        treasuryWallets[Category.ORPHAN] = orphan;
        treasuryWallets[Category.MERCY] = mercy;
        treasuryWallets[Category.EARTH] = earth;
    }

    function setTreasuryWallet(Category category, address payable wallet) external onlyRole(TREASURY_ADMIN_ROLE) {
        treasuryWallets[category] = wallet;
    }

    function routeDonation(Category category, string calldata paymentReference, string calldata receiptId) external payable whenNotPaused {
        require(msg.value > 0, "amount=0");
        address payable wallet = treasuryWallets[category];
        require(wallet != address(0), "treasury not set");
        (bool ok, ) = wallet.call{value: msg.value}("");
        require(ok, "transfer failed");
        emit DonationRouted(msg.sender, category, msg.value, paymentReference, receiptId);
    }

    function pause() external onlyRole(TREASURY_ADMIN_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(TREASURY_ADMIN_ROLE) {
        _unpause();
    }
}
