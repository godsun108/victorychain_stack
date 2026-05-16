// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/// @title BeneficiaryDisbursement
/// @notice Admin-controlled payout executor with auditable events.
contract BeneficiaryDisbursement is AccessControl, Pausable {
    bytes32 public constant DISBURSE_ROLE = keccak256("DISBURSE_ROLE");

    event DisbursementExecuted(
        bytes32 indexed requestId,
        address indexed recipient,
        uint256 amount,
        string aidCategory,
        string publicImpactNote,
        string internalReceiptId
    );

    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(DISBURSE_ROLE, admin);
    }

    function executeDisbursement(
        bytes32 requestId,
        address payable recipient,
        uint256 amount,
        string calldata aidCategory,
        string calldata publicImpactNote,
        string calldata internalReceiptId
    ) external onlyRole(DISBURSE_ROLE) whenNotPaused {
        require(recipient != address(0), "bad recipient");
        require(amount > 0, "amount=0");
        require(address(this).balance >= amount, "insufficient balance");

        (bool ok, ) = recipient.call{value: amount}("");
        require(ok, "payout failed");

        emit DisbursementExecuted(requestId, recipient, amount, aidCategory, publicImpactNote, internalReceiptId);
    }

    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }

    receive() external payable {}
}
