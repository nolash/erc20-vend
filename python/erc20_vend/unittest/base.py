# standard imports
import logging
import time

# external imports
from chainlib.eth.unittest.ethtester import EthTesterCase
from chainlib.connection import RPCConnection
from chainlib.eth.nonce import RPCNonceOracle
from chainlib.eth.tx import receipt
from chainlib.eth.address import to_checksum_address
from giftable_erc20_token.unittest import TestGiftableToken
from eth_erc20 import ERC20
from chainlib.eth.block import block_latest

# local imports
from erc20_vend import Vend

logg = logging.getLogger(__name__)

class TestVendCore(TestGiftableToken):

    expire = 0

    def setUp(self):
        super(TestVendCore, self).setUp()

        self.alice = self.accounts[1]
        self.bob = self.accounts[2]

        self.token_address = self.address

        c = ERC20(self.chain_spec)
        o = c.decimals(self.token_address, sender_address=self.accounts[0])
        r = self.rpc.do(o)
        self.token_decimals = c.parse_decimals(r)


    def publish(self, mint=False, decimals=0):
        nonce_oracle = RPCNonceOracle(self.accounts[0], conn=self.conn)
        c = Vend(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        (tx_hash, o) = c.constructor(self.accounts[0], self.token_address, mint=mint, decimals=decimals)
        self.rpc.do(o)
        o = receipt(tx_hash)
        r = self.rpc.do(o)
        self.assertEqual(r['status'], 1)
        self.vend_address = to_checksum_address(r['contract_address'])
        logg.debug('published vend on address {} with hash {}'.format(self.vend_address, tx_hash))


class TestVend(TestVendCore):

    def setUp(self):
        super(TestVend, self).setUp()
        self.publish()


class TestVendParams(TestVendCore):

    def setUp(self):
        super(TestVendParams, self).setUp()
        self.publish(lock=True, decimals=2)
