// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract DividendVault {
    struct Position {
        address token;
        uint256 shares;
        uint256 accumulatedDividend;
    }

    mapping(address => Position) public positions;
    IERC20 public immutable dividendToken;

    event Deposit(address indexed user, address indexed token, uint256 shares, uint256 dividendPerShare);
    event DividendProcessed(address indexed token, uint256 totalAmount, uint256 distributed);
    event Withdraw(address indexed user, address indexed token, uint256 shares);

    constructor(address _dividendToken) {
        dividendToken = IERC20(_dividendToken);
    }

    function deposit(address token, uint256 shares) external {
        positions[msg.sender] = Position({
            token: token,
            shares: positions[msg.sender].shares + shares,
            accumulatedDividend: positions[msg.sender].accumulatedDividend
        });
        emit Deposit(msg.sender, token, shares, 0);
    }

    function processDividend(address token, uint256 totalAmount) external {
        uint256 totalShares = positions[token].shares;
        require(totalShares > 0, "no shares");
        uint256 perShare = (totalAmount * 1e18) / totalShares;
        positions[token].accumulatedDividend += perShare;
        emit DividendProcessed(token, totalAmount, totalAmount);
    }

    function claim(address token) external returns (uint256) {
        Position storage p = positions[token];
        uint256 amount = (p.shares * p.accumulatedDividend) / 1e18;
        p.accumulatedDividend = 0;
        require(amount > 0, "nothing to claim");
        dividendToken.transfer(msg.sender, amount);
        return amount;
    }

    function withdraw(address token, uint256 shares) external {
        require(positions[msg.sender].shares >= shares, "insufficient shares");
        positions[msg.sender].shares -= shares;
        emit Withdraw(msg.sender, token, shares);
    }
}
