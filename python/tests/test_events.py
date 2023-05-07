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
        self.publish(mint=True)
        nonce_oracle = RPCNonceOracle(self.accounts[0], conn=self.conn)
        c = Vend(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        (tx_hash, o) = c.create(self.vend_address, self.accounts[0], 'foo vend', 'FOOVEND')
        self.rpc.do(o)
        o = receipt(tx_hash)
        r = self.rpc.do(o)
        rlog = r['logs'][0]
        
        o = c.get_token(self.vend_address, 0, sender_address=self.accounts[0])
        r = self.rpc.do(o)
        vended_token_address = c.parse_token(r)

        dec = ABIContractLogDecoder()
        dec.topic('TokenCreated')
        dec.typ(ABIContractType.UINT256)
        dec.typ(ABIContractType.UINT256)
        dec.typ(ABIContractType.ADDRESS)
        dec.apply(rlog['topics'], [rlog['data']])
        self.assertEqual(int(dec.contents[0], 16), 0)
        self.assertEqual(int(dec.contents[1], 16), 0)
        self.assertEqual(int(dec.contents[2], 16), int(vended_token_address, 16))


    def test_mint_event(self):
        self.publish(mint=True)
        nonce_oracle = RPCNonceOracle(self.accounts[0], conn=self.conn)
        c = Vend(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        (tx_hash, o) = c.create(self.vend_address, self.accounts[0], 'foo vend', 'FOOVEND')
        self.rpc.do(o)

        o = c.get_token(self.vend_address, 0, sender_address=self.accounts[0])
        r = self.rpc.do(o)
        vended_token_address = c.parse_token(r)

        vend_amount = 100
        src_amount = vend_amount * (10 ** self.token_decimals)
        c = GiftableToken(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        (tx_hash, o) = c.mint_to(self.token_address, self.accounts[0], self.alice, src_amount)
        self.rpc.do(o)

        nonce_oracle = RPCNonceOracle(self.alice, conn=self.conn)
        c = Vend(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        (tx_hash, o) = c.get_for(self.vend_address, self.alice, vended_token_address)
        self.rpc.do(o)
        o = receipt(tx_hash)
        r = self.rpc.do(o)
        self.assertEqual(r['status'], 1)
        rlog = r['logs'][0]

        dec = ABIContractLogDecoder()
        dec.topic('Mint')
        dec.typ(ABIContractType.ADDRESS)
        dec.typ(ABIContractType.ADDRESS)
        dec.typ(ABIContractType.UINT256)
        dec.apply(rlog['topics'], [rlog['data']])
        self.assertEqual(int(dec.contents[0], 16), int(self.vend_address, 16))
        self.assertEqual(int(dec.contents[1], 16), int(self.alice, 16))
        self.assertEqual(int(dec.contents[2], 16), vend_amount)


    def test_create_token_nomint_event(self):
        self.publish()
        nonce_oracle = RPCNonceOracle(self.accounts[0], conn=self.conn)
        c = Vend(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        (tx_hash, o) = c.create(self.vend_address, self.accounts[0], 'foo vend', 'FOOVEND')
        self.rpc.do(o)
        o = receipt(tx_hash)
        r = self.rpc.do(o)
        self.assertEqual(r['status'], 1)
        rlog = r['logs'][1]
        
        o = c.get_token(self.vend_address, 0, sender_address=self.accounts[0])
        r = self.rpc.do(o)
        vended_token_address = c.parse_token(r)

        dec = ABIContractLogDecoder()
        dec.topic('TokenCreated')
        dec.typ(ABIContractType.UINT256)
        dec.typ(ABIContractType.UINT256)
        dec.typ(ABIContractType.ADDRESS)
        dec.apply(rlog['topics'], [rlog['data']])
        self.assertEqual(int(dec.contents[0], 16), 0)
        self.assertEqual(int(dec.contents[1], 16), self.initial_supply)
        self.assertEqual(int(dec.contents[2], 16), int(vended_token_address, 16))


    def test_mint_event(self):
        self.publish()
        nonce_oracle = RPCNonceOracle(self.accounts[0], conn=self.conn)
        c = Vend(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        (tx_hash, o) = c.create(self.vend_address, self.accounts[0], 'foo vend', 'FOOVEND')
        self.rpc.do(o)

        o = c.get_token(self.vend_address, 0, sender_address=self.accounts[0])
        r = self.rpc.do(o)
        vended_token_address = c.parse_token(r)

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
        (tx_hash, o) = c.get_for(self.vend_address, self.alice, vended_token_address)
        self.rpc.do(o)
        o = receipt(tx_hash)
        r = self.rpc.do(o)
        self.assertEqual(r['status'], 1)
        rlog = r['logs'][1]

        dec = ABIContractLogDecoder()
        dec.topic('Transfer')
        dec.typ(ABIContractType.ADDRESS)
        dec.typ(ABIContractType.ADDRESS)
        dec.typ(ABIContractType.UINT256)
        dec.apply(rlog['topics'], [rlog['data']])
        self.assertEqual(int(dec.contents[0], 16), int(self.vend_address, 16))
        self.assertEqual(int(dec.contents[1], 16), int(self.alice, 16))
        self.assertEqual(int(dec.contents[2], 16), vend_amount)


if __name__ == '__main__':
    unittest.main()
