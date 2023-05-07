# standard imports
import logging
import os
import enum

# external imports
from chainlib.eth.constant import ZERO_ADDRESS
from chainlib.eth.contract import (
    ABIContractEncoder,
    ABIContractDecoder,
    ABIContractType,
    abi_decode_single,
)
from chainlib.eth.jsonrpc import to_blockheight_param
from chainlib.eth.error import RequestMismatchException
from chainlib.eth.tx import (
    TxFactory,
    TxFormat,
)
from chainlib.jsonrpc import JSONRPCRequest
from chainlib.block import BlockSpec
from hexathon import (
    add_0x,
    strip_0x,
)

# local imports
from erc20_vend.data import data_dir

logg = logging.getLogger()



class Vend(TxFactory):

    __abi = None
    __bytecode = None

    def constructor(self, sender_address, token_address, decimals=0, lock=False, tx_format=TxFormat.JSONRPC, version=None):
        code = self.cargs(token_address, decimals=decimals, lock=lock, version=version)
        tx = self.template(sender_address, None, use_nonce=True)
        tx = self.set_code(tx, code)
        return self.finalize(tx, tx_format)


    @staticmethod
    def cargs(token_address, decimals=0, lock=False, version=None):
        code = Vend.bytecode(version=version)
        enc = ABIContractEncoder()
        enc.address(token_address)
        enc.uintn(decimals, 8)
        enc.bool(lock)
        args = enc.get()
        code += args
        logg.debug('constructor code: ' + args)
        return code


    @staticmethod
    def gas(code=None):
        return 4000000



    @staticmethod
    def abi():
        if Vend.__abi == None:
            f = open(os.path.join(data_dir, 'Vend.json'), 'r')
            Vend.__abi = json.load(f)
            f.close()
        return Vend.__abi


    @staticmethod
    def bytecode(version=None):
        if Vend.__bytecode == None:
            f = open(os.path.join(data_dir, 'Vend.bin'))
            Vend.__bytecode = f.read()
            f.close()
        return Vend.__bytecode

    
    def create(self, contract_address, sender_address, name, symbol, tx_format=TxFormat.JSONRPC, id_generator=None):
        enc = ABIContractEncoder()
        enc.method('create')
        enc.typ(ABIContractType.STRING)
        enc.typ(ABIContractType.STRING)
        enc.string(name)
        enc.string(symbol)
        data = add_0x(enc.get())
        tx = self.template(sender_address, contract_address, use_nonce=True)
        tx = self.set_code(tx, data)
        tx = self.finalize(tx, tx_format, id_generator=id_generator)
        return tx


    def get_token(self, contract_address, token_idx, sender_address=ZERO_ADDRESS, id_generator=None):
        j = JSONRPCRequest(id_generator)
        o = j.template()
        o['method'] = 'eth_call'
        enc = ABIContractEncoder()
        enc.method('getTokenByIndex')
        enc.typ(ABIContractType.UINT256)
        enc.uint256(token_idx)
        data = add_0x(enc.get())
        tx = self.template(sender_address, contract_address)
        tx = self.set_code(tx, data)
        o['params'].append(self.normalize(tx))
        o['params'].append('latest')
        o = j.finalize(o)
        return o



    def parse_token(self, v):
        dec = ABIContractDecoder()
        dec.typ(ABIContractType.ADDRESS)
        dec.val(v)
        r = dec.get()
        return r[0]
