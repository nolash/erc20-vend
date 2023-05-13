# standard imports
import unittest
import logging

# external imports
from eth_writer.unittest import TestEthWriterInterface

# local imports
from erc20_vend.unittest import TestVend

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class TestEthWriter(TestVend, TestEthWriterInterface):

    def setUp(self):
        super(TestEthWriter, self).setUp()
        self.contracts['writer'] = self.address
        self.roles['writer'] = self.accounts[1]


if __name__ == '__main__':
    unittest.main()
