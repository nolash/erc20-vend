# standard imports
import unittest
import logging
import os
from chainlib.eth.nonce import RPCNonceOracle
from chainlib.eth.tx import receipt
from eth_erc20 import ERC20
from giftable_erc20_token import GiftableToken

# local imports
from erc20_vend.unittest import TestVend
from erc20_vend import Vend


logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class TestVendBase(TestVend):

    def test_create_token(self):
        nonce_oracle = RPCNonceOracle(self.accounts[0], conn=self.conn)
        c = Vend(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        (tx_hash, o) = c.create(self.vend_address, self.accounts[0], 'foo vend', 'FOOVEND')
        self.rpc.do(o)
        o = receipt(tx_hash)
        r = self.rpc.do(o)
        self.assertEqual(r['status'], 1)

        o = c.get_token(self.vend_address, 0, sender_address=self.accounts[0])
        r = self.rpc.do(o)
        vended_token_address = c.parse_token(r)
   
        c = ERC20(self.chain_spec)
        o = c.name(vended_token_address, sender_address=self.accounts[0])
        r = self.rpc.do(o)
        name = c.parse_name(r)
        self.assertEqual(name, 'foo vend')

        o = c.symbol(vended_token_address, sender_address=self.accounts[0])
        r = self.rpc.do(o)
        symbol = c.parse_symbol(r)
        self.assertEqual(symbol, 'FOOVEND')
        
    def test_vend_token(self):
        nonce_oracle = RPCNonceOracle(self.accounts[0], conn=self.conn)
        c = Vend(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        (tx_hash, o) = c.create(self.vend_address, self.accounts[0], 'foo vend', 'FOOVEND')
        self.rpc.do(o)

        o = c.get_token(self.vend_address, 0, sender_address=self.accounts[0])
        r = self.rpc.do(o)
        vended_token_address = c.parse_token(r)

        vend_amount = 100
        src_amount = vend_amount * (10 ** (self.token_decimals))
        c = GiftableToken(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        (tx_hash, o) = c.mint_to(self.token_address, self.accounts[0], self.alice, src_amount)
        self.rpc.do(o)
        o = receipt(tx_hash)
        r = self.rpc.do(o)
        self.assertEqual(r['status'], 1)

        nonce_oracle = RPCNonceOracle(self.alice, conn=self.conn)
        c = Vend(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        (tx_hash, o) = c.get_for(self.vend_address, self.alice, vended_token_address)
        self.rpc.do(o)
        o = receipt(tx_hash)
        r = self.rpc.do(o)
        self.assertEqual(r['status'], 0)

        c = ERC20(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        (tx_hash, o) = c.approve(self.token_address, self.alice, self.vend_address, src_amount)
        self.rpc.do(o)
        o = receipt(tx_hash)
        r = self.rpc.do(o)
        self.assertEqual(r['status'], 1)

        c = Vend(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        (tx_hash, o) = c.get_for(self.vend_address, self.alice, vended_token_address)
        self.rpc.do(o)
        o = receipt(tx_hash)
        r = self.rpc.do(o)
        self.assertEqual(r['status'], 1)

        c = ERC20(self.chain_spec)
        o = c.balance_of(vended_token_address, self.alice, sender_address=self.accounts[0])
        r = self.rpc.do(o)
        balance = c.parse_balance(r)
        self.assertEqual(balance, vend_amount)

        o = c.balance_of(self.token_address, self.alice, sender_address=self.accounts[0])
        r = self.rpc.do(o)
        balance = c.parse_balance(r)
        self.assertEqual(balance, 0)

        c = Vend(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        (tx_hash, o) = c.withdraw_for(self.vend_address, self.alice, vended_token_address)
        self.rpc.do(o)
        o = receipt(tx_hash)
        r = self.rpc.do(o)
        self.assertEqual(r['status'], 0)

        c = ERC20(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        (tx_hash, o) = c.approve(vended_token_address, self.alice, self.vend_address, vend_amount)
        self.rpc.do(o)

        c = Vend(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        (tx_hash, o) = c.withdraw_for(self.vend_address, self.alice, vended_token_address)
        self.rpc.do(o)
        o = receipt(tx_hash)
        r = self.rpc.do(o)
        self.assertEqual(r['status'], 1)

        c = ERC20(self.chain_spec)
        o = c.balance_of(vended_token_address, self.alice, sender_address=self.accounts[0])
        r = self.rpc.do(o)
        balance = c.parse_balance(r)
        self.assertEqual(balance, 0)

        o = c.balance_of(self.token_address, self.alice, sender_address=self.accounts[0])
        r = self.rpc.do(o)
        balance = c.parse_balance(r)
        self.assertEqual(balance, src_amount)



if __name__ == '__main__':
    unittest.main()
