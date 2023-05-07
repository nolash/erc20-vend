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
        

if __name__ == '__main__':
    unittest.main()
