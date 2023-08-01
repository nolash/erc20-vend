# standard imports
import unittest
import logging
import os
from chainlib.eth.nonce import RPCNonceOracle
from chainlib.eth.contract import ABIContractLogDecoder
from chainlib.eth.contract import ABIContractType
from chainlib.eth.tx import receipt
from eth_erc20 import ERC20
from giftable_erc20_token import GiftableToken
from hexathon import same as same_hex

# local imports
from erc20_vend.unittest.base import TestVendCore
from erc20_vend import Vend


logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class TestVendBase(TestVendCore):

    def test_create_token_event(self):
        self.publish()

        nonce_oracle = RPCNonceOracle(self.accounts[0], conn=self.conn)
        c = Vend(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        (tx_hash, o) = c.create(self.vend_address, self.accounts[0], 'foo vend', 'FOOVEND')
        self.rpc.do(o)
        
        o = c.get_token(self.vend_address, 0, sender_address=self.accounts[0])
        r = self.rpc.do(o)
        vended_token_address = c.parse_token(r)

        c = ERC20(self.chain_spec)
        o = c.total_supply(vended_token_address, sender_address=self.accounts[0])
        r = self.rpc.do(o)
        self.assertEqual(int(r, 16), self.initial_supply)


    def test_create_token_nomint_event(self):
        self.publish(mint=True)

        nonce_oracle = RPCNonceOracle(self.accounts[0], conn=self.conn)
        c = Vend(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        (tx_hash, o) = c.create(self.vend_address, self.accounts[0], 'foo vend', 'FOOVEND')
        self.rpc.do(o)
        
        o = c.get_token(self.vend_address, 0, sender_address=self.accounts[0])
        r = self.rpc.do(o)
        vended_token_address = c.parse_token(r)

        c = ERC20(self.chain_spec)
        o = c.total_supply(vended_token_address, sender_address=self.accounts[0])
        r = self.rpc.do(o)
        self.assertEqual(int(r, 16), 0)

        vend_amount = 100
        src_amount = vend_amount * (10 ** self.token_decimals)
        c = GiftableToken(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        (tx_hash, o) = c.mint_to(self.token_address, self.accounts[0], self.alice, src_amount)
        self.rpc.do(o)

        nonce_oracle = RPCNonceOracle(self.alice, conn=self.conn)
        c = ERC20(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        (tx_hash, o) = c.approve(self.token_address, self.alice, self.vend_address, src_amount)
        self.rpc.do(o)

        c = Vend(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        (tx_hash, o) = c.deposit(self.vend_address, self.alice, vended_token_address)
        self.rpc.do(o)

        c = ERC20(self.chain_spec)
        o = c.total_supply(vended_token_address, sender_address=self.accounts[0])
        r = self.rpc.do(o)
        self.assertEqual(int(r, 16), vend_amount)


if __name__ == '__main__':
    unittest.main()
