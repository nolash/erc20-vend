pragma solidity ^0.8.0;

// Author:	Louis Holbrook <dev@holbrook.no> 0826EDA1702D1E87C6E2875121D2E7BB88C2A746
// SPDX-License-Identifier: AGPL-3.0-or-later
// File-Version: 1
// Description: Create and vend ERC20 voting tokens in exchange for a held ERC20 token.

import "GiftableToken.sol";

contract ERC20Vend {
	uint256 constant UINT256_MAX = 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff;
	address controlToken;
	uint8 controlDecimals;
	uint8 decimals;
	uint256 decimalDivisor;
	bool lock;
	GiftableToken[] vendToken;
	mapping ( address => mapping ( address => uint256 ) ) used;

	event TokenCreated(uint256 indexed _idx, address _token);

	constructor(address _controlToken, uint8 _decimals, bool _lock) {
		bool r;
		bytes memory v;

		controlToken = _controlToken;
		decimals = _decimals;
		lock = _lock;

		(r, v) = controlToken.call(abi.encodeWithSignature("decimals()"));
		require(r, "ERR_TOKEN");
		controlDecimals = abi.decode(v, (uint8));
		require(controlDecimals >= decimals);

		decimalDivisor = (10 ** (controlDecimals - _decimals));
		if (decimalDivisor == 0) {
			decimalDivisor = 1;
		}
	}

	function getTokenByIndex(uint256 _idx) public view returns(address) {
		return address(vendToken[_idx]);
	}

	function create(string calldata _name, string calldata _symbol) public returns (address) {
		GiftableToken l_contract;
		address l_address;
		uint256 l_idx;
	
		l_contract = new GiftableToken(_name, _symbol, decimals, 0);
		l_address = address(l_contract);
		l_idx = vendToken.length;
		vendToken.push(l_contract);
		emit TokenCreated(l_idx, l_address);
		return l_address;
	}

	function mintFor(address _token) public returns (uint256) {
		GiftableToken l_token;
		bool r;
		bytes memory v;
		uint256 l_ratioedValue;
		uint256 l_controlBalance;

		l_token = GiftableToken(_token);

		require(used[msg.sender][address(_token)] == 0, "ERR_USED");

		(r, v) = controlToken.call(abi.encodeWithSignature("balanceOf(address)", msg.sender));
		require(r, "ERR_TOKEN");
		l_controlBalance = abi.decode(v, (uint256));

		require(l_controlBalance < UINT256_MAX, "ERR_VALUE_TOO_HIGH");
		if (l_controlBalance == 0) {
			return 0;
		}

		if (lock) {
			(r, v) = controlToken.call(abi.encodeWithSignature("transferFrom(address,address,uint256)", msg.sender, this, l_controlBalance));
			require(r, "ERR_TOKEN");
			r = abi.decode(v, (bool));
			require(r, "ERR_TOKEN_TRANSFER");
			used[msg.sender][address(l_token)] = l_controlBalance;
		} else {
			used[msg.sender][address(l_token)] = UINT256_MAX;
		}

		if (decimalDivisor == 0) {
			l_ratioedValue = l_controlBalance;
		} else {
			l_ratioedValue = l_controlBalance / decimalDivisor;
		}
		if (!l_token.mintTo(msg.sender, l_ratioedValue)) {
			revert("ERR_MINT");
		}
		return l_ratioedValue;
	}

	function withdrawFor(address _token) public returns (uint256) {
		bool r;
		bytes memory v;
		uint256 l_balance;
		uint256 l_vendBalance;

		l_balance = used[msg.sender][_token];
		if (l_balance == 0) {
			return 0;
		}
		require(used[msg.sender][_token] < UINT256_MAX, "ERR_ALREADY_WITHDRAWN");
		l_vendBalance = checkLock(_token, msg.sender);
		used[msg.sender][_token] = UINT256_MAX;

		if (l_vendBalance < UINT256_MAX) {	
			(r, v) = _token.call(abi.encodeWithSignature("transferFrom(address,address,uint256)", msg.sender, this, l_vendBalance));
			require(r, "ERR_TOKEN");
			r = abi.decode(v, (bool));
			require(r, "ERR_TOKEN_TRANSFER");
		}

		(r, v) = controlToken.call(abi.encodeWithSignature("transfer(address,uint256)", msg.sender, l_balance));
		require(r, "ERR_TOKEN");
		r = abi.decode(v, (bool));
		require(r, "ERR_TOKEN_TRANSFER");

		return l_balance;
	}

	// returns UINT256_MAX if lock is inactive
	// reverts if locked and target does not have the original balance
	function checkLock(address _token, address _target) private returns (uint256) {
		bool r;
		bytes memory v;
		uint256 l_currentBalance;
		uint256 l_heldBalance;

		if (lock) {
			(r, v) = _token.call(abi.encodeWithSignature("balanceOf(address)", _target));
			require(r, "ERR_TOKEN");
			l_currentBalance = abi.decode(v, (uint256));
			l_heldBalance = used[_target][_token];
			require(l_currentBalance * decimalDivisor == l_heldBalance, "ERR_LOCKED");
			return l_currentBalance;
		}
		return UINT256_MAX;
	}
}
