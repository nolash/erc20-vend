pragma solidity ^0.8.0;

// Author:	Louis Holbrook <dev@holbrook.no> 0826EDA1702D1E87C6E2875121D2E7BB88C2A746
// SPDX-License-Identifier: AGPL-3.0-or-later
// File-Version: 1
// Description: Create and vend ERC20 voting tokens in exchange for a held ERC20 token.

import "GiftableToken.sol";

contract ERC20Vend {
	address owner;
	uint256 constant UINT256_MAX = 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff;
	address controlToken;
	uint8 controlDecimals;
	uint8 decimals;
	uint256 supply;
	uint256 decimalDivisor;
	mapping ( address => uint256 ) returned;
	GiftableToken[] vendToken;
	mapping ( address => mapping ( address => uint256 ) ) used;

	mapping(address => bool) writers;

	event TokenCreated(uint256 indexed _idx, uint256 indexed _supply, address _token);

	constructor(address _controlToken, uint8 _decimals, bool _mint) {
		bool r;
		bytes memory v;

		controlToken = _controlToken;
		decimals = _decimals;

		(r, v) = controlToken.call(abi.encodeWithSignature("decimals()"));
		require(r, "ERR_TOKEN");
		controlDecimals = abi.decode(v, (uint8));
		require(controlDecimals >= decimals);

		if (!_mint) {
			(r, v) = controlToken.call(abi.encodeWithSignature("totalSupply()"));
			require(r, "ERR_TOKEN");
			supply = abi.decode(v, (uint256));
		}

		decimalDivisor = (10 ** (controlDecimals - _decimals));
		if (decimalDivisor == 0) {
			decimalDivisor = 1;
		}
		owner = msg.sender;
	}

	// Implements Writer
	function addWriter(address _minter) public returns (bool) {
		require(msg.sender == owner);
		writers[_minter] = true;
		return true;
	}

	// Implements Writer
	function deleteWriter(address _minter) public returns (bool) {
		require(msg.sender == owner || msg.sender == _minter);
		writers[_minter] = false;
		return true;
	}

	// Implements Writer
	function isWriter(address _minter) public view returns(bool) {
		return writers[_minter] || _minter == owner;
	}

	// Retrieve address of vended token by sequential index.
	function getTokenByIndex(uint256 _idx) public view returns(address) {
		return address(vendToken[_idx]);
	}

	// Create a new vended token.
	function create(string calldata _name, string calldata _symbol) public returns (address) {
		GiftableToken l_contract;
		address l_address;
		uint256 l_idx;
	
		l_contract = new GiftableToken(_name, _symbol, decimals, 0);
		l_address = address(l_contract);
		l_idx = vendToken.length;
		vendToken.push(l_contract);

		if (supply > 0) {
			l_contract.mintTo(address(this), supply);
		}
		emit TokenCreated(l_idx, supply, l_address);
		return l_address;
	}

	// Receive the vended token for the currently held balance.
	function getFor(address _token) public returns (uint256) {
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

		(r, v) = controlToken.call(abi.encodeWithSignature("transferFrom(address,address,uint256)", msg.sender, this, l_controlBalance));
		require(r, "ERR_TOKEN");
		r = abi.decode(v, (bool));
		require(r, "ERR_TOKEN_TRANSFER");
		used[msg.sender][address(l_token)] = l_controlBalance;

		if (decimalDivisor == 0) {
			l_ratioedValue = l_controlBalance;
		} else {
			l_ratioedValue = l_controlBalance / decimalDivisor;
		}

		if (supply == 0) {
			if (!l_token.mintTo(msg.sender, l_ratioedValue)) {
				revert("ERR_MINT");
			}
		} else {
			(r, v) = _token.call(abi.encodeWithSignature("transfer(address,uint256)", msg.sender, l_ratioedValue));
			require(r, "ERR_TOKEN");
			r = abi.decode(v, (bool));
			require(r, "ERR_VEND_TOKEN_TRANSFER");
		}
		return l_ratioedValue;
	}

	// If contract locks exchanged tokens, this can be called to retrieve the locked tokens.
	// The vended token balance MUST match the original balance emitted on the exchange.
	// The caller must have given allowance for the full amount.
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

		if (l_vendBalance == UINT256_MAX) {
			return 0;
		}

		(r, v) = _token.call(abi.encodeWithSignature("transferFrom(address,address,uint256)", msg.sender, this, l_vendBalance));
		require(r, "ERR_TOKEN");
		r = abi.decode(v, (bool));
		require(r, "ERR_TOKEN_TRANSFER");
		returned[_token] += l_vendBalance;

		(r, v) = controlToken.call(abi.encodeWithSignature("transfer(address,uint256)", msg.sender, l_balance));
		require(r, "ERR_TOKEN");
		r = abi.decode(v, (bool));
		require(r, "ERR_TOKEN_TRANSFER");

		return l_balance;
	}

//	// burn used vend tokens.
//	// should self-destruct contract if possible when supply reaches 0.
//	function burnFor(address _token) public returns(uint256) {
//		bool r;
//		bytes memory v;
//		uint256 l_burnValue;
//
//		l_burnValue = returned[_token];
//		(r, v) = _token.call(abi.encodeWithSignature("burn(uint256)", l_burnValue));
//		require(r, "ERR_TOKEN");
//		r = abi.decode(v, (bool));
//		require(r, "ERR_TOKEN_BURN");
//		returned[_token] = 0;
//		return l_burnValue;
//	}
	
	// returns UINT256_MAX if lock is inactive
	// reverts if target does not have the original balance
	function checkLock(address _token, address _target) private returns (uint256) {
		bool r;
		bytes memory v;
		uint256 l_currentBalance;
		uint256 l_heldBalance;

		(r, v) = _token.call(abi.encodeWithSignature("balanceOf(address)", _target));
		require(r, "ERR_TOKEN");
		l_currentBalance = abi.decode(v, (uint256));
		l_heldBalance = used[_target][_token];
		require(l_currentBalance * decimalDivisor == l_heldBalance, "ERR_LOCKED");
		return l_currentBalance;
	}

	// Implements EIP165
	function supportsInterface(bytes4 _sum) public pure returns (bool) {
		if (_sum == 0x01ffc9a7) { // EIP165
			return true;
		}
		if (_sum == 0xabe1f1f5) { // Writer
			return true;
		}
		return false;
	}
}
