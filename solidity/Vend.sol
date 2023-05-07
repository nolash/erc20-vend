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

	function mintFor(address _token, uint256 _value) public returns (uint256) {
		GiftableToken l_token;
		bool r;
		bytes memory v;
		uint256 l_balance;
		uint256 l_ratioedValue;

		require(_value < UINT256_MAX, "ERR_VALUE_TOO_HIGH");
		if (_value == 0) {
			return 0;
		}

		l_token = GiftableToken(_token);
		require(used[msg.sender][address(_token)] == 0, "ERR_USED");

		l_balance = l_token.balanceOf(msg.sender);
		(r, v) = controlToken.call(abi.encodeWithSignature("transferFrom(address,address,uint256)", msg.sender, this, _value));
		require(r, "ERR_TOKEN");
		r = abi.decode(v, (bool));
		require(r, "ERR_TOKEN_TRANSFER");

		if (decimalDivisor == 0) {
			l_ratioedValue = _value;
		} else {
			l_ratioedValue = _value / decimalDivisor;
		}
		used[msg.sender][address(l_token)] += _value;
		if (!l_token.mintTo(msg.sender, _value)) {
			revert("ERR_MINT");
		}
		return _value;
	}

	function withdrawFor(address _token) public returns (uint256) {
		bool r;
		bytes memory v;
		uint256 l_balance;

		l_balance = used[msg.sender][_token];
		if (l_balance == 0) {
			return 0;
		}
		checkLock(_token, msg.sender);
		used[msg.sender][_token] = UINT256_MAX;

		(r, v) = controlToken.call(abi.encodeWithSignature("transfer(address,uint256)", msg.sender, l_balance));
		require(r, "ERR_TOKEN");
		r = abi.decode(v, (bool));
		require(r, "ERR_TOKEN_TRANSFER");

		return l_balance;
	}

	function checkLock(address _token, address _target) private returns (bool) {
		bool r;
		bytes memory v;
		uint256 l_currentBalance;
		uint256 l_heldBalance;

		if (lock) {
			(r, v) = _token.call(abi.encodeWithSignature("balanceOf(address)", _target));
			require(r, "ERR_TOKEN");
			l_currentBalance = abi.decode(v, (uint256));
			l_heldBalance = used[_target][_token];
			require(l_currentBalance == l_heldBalance, "ERR_LOCKED");
		}
		return true;
	}
}